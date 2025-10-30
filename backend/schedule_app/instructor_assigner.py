"""
Módulo para asignación inteligente de instructores después de la generación del horario.

Este módulo se encarga de:
1. Analizar el horario generado (clases ya tienen aula y horario asignados)
2. Asignar instructores disponibles considerando:
   - Preferencias de horario del instructor
   - Evitar conflictos (instructor en 2 lugares al mismo tiempo)
   - Maximizar match entre preferencias e instructor
3. Permitir clases sin instructor si no hay disponibilidad
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict
from .models import (
    Schedule, ScheduleAssignment, Instructor, ClassInstructor,
    TimeSlot, InstructorTimeSlot
)


class InstructorAssigner:
    """
    Asigna instructores a clases que ya tienen aula y horario definidos.
    """
    
    def __init__(self, schedule: Schedule):
        """
        Inicializa el asignador para un horario específico.
        
        Args:
            schedule: Horario con asignaciones de clase-aula-tiempo ya definidas
        """
        self.schedule = schedule
        self.assignments = list(
            ScheduleAssignment.objects.filter(schedule=schedule)
            .select_related('class_obj', 'room', 'time_slot')
        )
        
        # Estructuras de datos para optimización
        self.instructor_availability = {}  # {instructor_id: {(day, start, end): bool}}
        self.instructor_preferences = {}   # {instructor_id: {timeslot_id: preference}}
        self.class_instructors_assigned = {}  # {class_id: instructor_id}
        
        print(f"[INFO] InstructorAssigner inicializado para horario '{schedule.name}'")
        print(f"[INFO] Total de asignaciones a procesar: {len(self.assignments)}")
    
    def load_instructor_data(self):
        """
        Carga datos de instructores: disponibilidad y preferencias.
        """
        all_instructors = Instructor.objects.all()
        
        print(f"[INFO] Cargando datos de {all_instructors.count()} instructores...")
        
        for instructor in all_instructors:
            # Inicializar disponibilidad (por defecto: disponible en todos los horarios)
            self.instructor_availability[instructor.id] = {}
            
            # Cargar preferencias de horario
            time_prefs = InstructorTimeSlot.objects.filter(
                instructor=instructor
            ).values_list('time_slot_id', 'preference')
            
            self.instructor_preferences[instructor.id] = dict(time_prefs)
        
        print(f"[OK] Datos de instructores cargados")
    
    def assign_instructors(self) -> Dict:
        """
        Asigna instructores a todas las clases del horario.
        
        Returns:
            Dict con estadísticas de asignación:
            - assigned: número de clases con instructor asignado
            - unassigned: número de clases sin instructor
            - conflicts_avoided: número de conflictos evitados
        """
        self.load_instructor_data()
        
        assigned_count = 0
        unassigned_count = 0
        conflicts_avoided = 0
        
        # Obtener todos los instructores disponibles
        all_instructors = list(Instructor.objects.all())
        
        print(f"\n[INFO] Iniciando asignación de instructores...")
        print(f"[INFO] Instructores disponibles: {len(all_instructors)}")
        
        # Ordenar asignaciones por preferencia (clases con menos opciones primero)
        # Esto asegura mejor distribución
        sorted_assignments = sorted(
            self.assignments,
            key=lambda a: self._count_available_instructors(a, all_instructors)
        )
        
        for assignment in sorted_assignments:
            # Intentar asignar instructor a esta clase
            instructor = self._find_best_instructor(
                assignment,
                all_instructors
            )
            
            if instructor:
                # Crear relación ClassInstructor
                ClassInstructor.objects.get_or_create(
                    class_obj=assignment.class_obj,
                    instructor=instructor
                )
                
                # Marcar horario como ocupado
                self._mark_instructor_busy(
                    instructor.id,
                    assignment.time_slot
                )
                
                assigned_count += 1
                self.class_instructors_assigned[assignment.class_obj.id] = instructor.id
            else:
                unassigned_count += 1
                print(f"[WARNING] Clase {assignment.class_obj.xml_id} quedó sin instructor")
        
        stats = {
            'assigned': assigned_count,
            'unassigned': unassigned_count,
            'conflicts_avoided': conflicts_avoided,
            'total': len(self.assignments)
        }
        
        self._print_report(stats)
        
        return stats
    
    def _count_available_instructors(
        self,
        assignment: ScheduleAssignment,
        instructors: List[Instructor]
    ) -> int:
        """
        Cuenta cuántos instructores están disponibles para una asignación.
        Usado para priorizar clases con pocas opciones.
        """
        count = 0
        for instructor in instructors:
            if self._is_instructor_available(instructor.id, assignment.time_slot):
                count += 1
        return count
    
    def _find_best_instructor(
        self,
        assignment: ScheduleAssignment,
        instructors: List[Instructor]
    ) -> Instructor:
        """
        Encuentra el mejor instructor para una asignación específica.
        
        Criterios (en orden de prioridad):
        1. Disponible en ese horario (sin conflictos)
        2. Tiene preferencia positiva por ese horario
        3. Tiene menor carga de clases asignadas
        
        Args:
            assignment: Asignación de clase-aula-tiempo
            instructors: Lista de instructores disponibles
        
        Returns:
            Instructor seleccionado, o None si no hay disponibles
        """
        time_slot = assignment.time_slot
        candidates = []
        
        for instructor in instructors:
            # CRITERIO 1: Disponibilidad (sin conflictos)
            if not self._is_instructor_available(instructor.id, time_slot):
                continue
            
            # CRITERIO 2: Preferencia de horario
            preference = self.instructor_preferences.get(instructor.id, {}).get(
                time_slot.id,
                0.0  # Neutral si no hay preferencia definida
            )
            
            # CRITERIO 3: Carga actual (cuántas clases ya tiene asignadas)
            current_load = sum(
                1 for cid, iid in self.class_instructors_assigned.items()
                if iid == instructor.id
            )
            
            # Calcular score combinado
            # Mayor preferencia = mejor
            # Menor carga = mejor (para distribuir equitativamente)
            score = preference - (current_load * 0.5)
            
            candidates.append((instructor, score, preference, current_load))
        
        if not candidates:
            return None
        
        # Ordenar por score (mayor es mejor)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        best_instructor, score, pref, load = candidates[0]
        
        return best_instructor
    
    def _is_instructor_available(
        self,
        instructor_id: int,
        time_slot: TimeSlot
    ) -> bool:
        """
        Verifica si un instructor está disponible en un horario específico.
        
        Un instructor está disponible si:
        - No tiene otra clase al mismo tiempo (mismo día + horario solapado)
        """
        busy_schedule = self.instructor_availability.get(instructor_id, {})
        
        # Parsear días y tiempo del slot
        days = time_slot.days
        start = time_slot.start_time
        end = start + time_slot.length
        
        # Verificar cada día de la semana
        for day_idx, day_active in enumerate(days):
            if day_active == '1':
                # Verificar si hay conflicto en ese día
                key = (day_idx, start, end)
                if key in busy_schedule and busy_schedule[key]:
                    return False  # Ocupado en ese horario
        
        return True  # Disponible
    
    def _mark_instructor_busy(
        self,
        instructor_id: int,
        time_slot: TimeSlot
    ):
        """
        Marca un instructor como ocupado en un horario específico.
        """
        days = time_slot.days
        start = time_slot.start_time
        end = start + time_slot.length
        
        if instructor_id not in self.instructor_availability:
            self.instructor_availability[instructor_id] = {}
        
        # Marcar cada día como ocupado
        for day_idx, day_active in enumerate(days):
            if day_active == '1':
                key = (day_idx, start, end)
                self.instructor_availability[instructor_id][key] = True
    
    def _print_report(self, stats: Dict):
        """
        Imprime un reporte de la asignación de instructores.
        """
        print(f"\n========================================")
        print(f" REPORTE DE ASIGNACION DE INSTRUCTORES")
        print(f"========================================")
        print(f"Total de clases: {stats['total']}")
        print(f"  • Asignadas: {stats['assigned']} ({stats['assigned']/stats['total']*100:.1f}%)")
        print(f"  • Sin instructor: {stats['unassigned']} ({stats['unassigned']/stats['total']*100:.1f}%)")
        print(f"Conflictos evitados: {stats['conflicts_avoided']}")
        print(f"========================================\n")
    
    def get_unassigned_classes(self) -> List[Dict]:
        """
        Retorna lista de clases que quedaron sin instructor asignado.
        
        Returns:
            Lista de diccionarios con información de cada clase sin instructor
        """
        unassigned = []
        
        for assignment in self.assignments:
            has_instructor = ClassInstructor.objects.filter(
                class_obj=assignment.class_obj
            ).exists()
            
            if not has_instructor:
                unassigned.append({
                    'class_id': assignment.class_obj.xml_id,
                    'offering': assignment.class_obj.offering.code if assignment.class_obj.offering else 'N/A',
                    'room': assignment.room.xml_id if assignment.room else 'N/A',
                    'time': f"{assignment.time_slot.days} @ {assignment.time_slot.start_time}" if assignment.time_slot else 'N/A'
                })
        
        return unassigned


def assign_instructors_to_schedule(schedule: Schedule) -> Dict:
    """
    Función helper para asignar instructores a un horario ya generado.
    
    Uso:
        from schedule_app.instructor_assigner import assign_instructors_to_schedule
        from schedule_app.models import Schedule
        
        schedule = Schedule.objects.get(id=24)
        stats = assign_instructors_to_schedule(schedule)
        print(f"Asignadas: {stats['assigned']}, Sin instructor: {stats['unassigned']}")
    
    Args:
        schedule: Horario con asignaciones de clase-aula-tiempo ya definidas
    
    Returns:
        Diccionario con estadísticas de asignación
    """
    assigner = InstructorAssigner(schedule)
    stats = assigner.assign_instructors()
    
    return stats
