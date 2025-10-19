"""
Sistema de análisis de carga de trabajo y recomendaciones.
Detecta profesores sobrecargados y genera alertas.
"""

from typing import Dict, List
from collections import defaultdict
from django.db.models import Count
from .models import (
    Class, Instructor, ClassInstructor, Schedule, 
    ScheduleAssignment, Room, TimeSlot
)


class WorkloadAnalyzer:
    """
    Analiza la carga de trabajo de instructores y genera recomendaciones.
    """
    
    # Umbrales de carga
    OPTIMAL_LOAD = 6  # Carga óptima
    HIGH_LOAD = 8     # Carga alta
    OVERLOAD = 10     # Sobrecarga
    
    def __init__(self):
        self.instructors = {}
        self.courses_by_offering = defaultdict(list)
        
    def analyze_instructor_workload(self) -> Dict:
        """
        Analiza la carga de todos los instructores.
        
        Returns:
            Dict con categorías: optimal, high_load, overloaded, synthetic, missing
        """
        # Obtener todos los instructores con sus clases
        instructor_classes = ClassInstructor.objects.values(
            'instructor_id',
            'instructor__name',
            'instructor__email',
            'instructor__xml_id'
        ).annotate(
            class_count=Count('class_obj')
        ).order_by('-class_count')
        
        result = {
            'optimal': [],
            'high_load': [],
            'overloaded': [],
            'synthetic': [],
            'missing_instructors': [],
            'total_instructors': 0,
            'total_classes': Class.objects.count(),
            'avg_load': 0
        }
        
        total_classes = 0
        
        for item in instructor_classes:
            instructor_data = {
                'instructor_id': item['instructor_id'],
                'name': item['instructor__name'],
                'email': item['instructor__email'],
                'xml_id': item['instructor__xml_id'],
                'class_count': item['class_count'],
                'load_percentage': (item['class_count'] / self.OPTIMAL_LOAD) * 100,
                'recommendation': self._get_recommendation(item['class_count'], item['instructor__xml_id'])
            }
            
            total_classes += item['class_count']
            
            # Clasificar por tipo
            if item['instructor__xml_id'] >= 900000:
                # Instructor sintético
                result['synthetic'].append(instructor_data)
            elif item['class_count'] >= self.OVERLOAD:
                result['overloaded'].append(instructor_data)
            elif item['class_count'] >= self.HIGH_LOAD:
                result['high_load'].append(instructor_data)
            else:
                result['optimal'].append(instructor_data)
        
        result['total_instructors'] = len(instructor_classes)
        result['avg_load'] = total_classes / len(instructor_classes) if instructor_classes else 0
        
        # Analizar cursos sin profesor
        result['missing_instructors'] = self._analyze_missing_instructors()
        
        return result
    
    def _get_recommendation(self, class_count: int, xml_id: int) -> str:
        """Genera recomendación basada en carga"""
        if xml_id >= 900000:
            return f"⚠️ URGENTE: Asignar {class_count} profesores reales para estas clases"
        
        if class_count >= self.OVERLOAD:
            needed = (class_count - self.OPTIMAL_LOAD) // self.OPTIMAL_LOAD + 1
            return f"🚨 Sobrecargado: Contratar {needed} ayudante(s) o redistribuir {class_count - self.OPTIMAL_LOAD} clases"
        elif class_count >= self.HIGH_LOAD:
            return f"⚠️ Carga alta: Considerar ayudante o reducir {class_count - self.OPTIMAL_LOAD} clases"
        else:
            remaining = self.OPTIMAL_LOAD - class_count
            return f"✅ Óptimo: Puede tomar {remaining} clases más"
    
    def _analyze_missing_instructors(self) -> List[Dict]:
        """Analiza cursos que necesitan más profesores"""
        # Obtener clases agrupadas por offering (curso)
        courses = Class.objects.values('offering_id', 'offering__name', 'offering__code').annotate(
            section_count=Count('id')
        ).order_by('-section_count')
        
        missing = []
        
        for course in courses:
            if not course['offering_id']:
                continue
            
            # Contar clases del curso con instructor
            classes_with_instructor = ClassInstructor.objects.filter(
                class_obj__offering_id=course['offering_id']
            ).count()
            
            # Contar clases del curso con instructor sintético
            classes_with_synthetic = ClassInstructor.objects.filter(
                class_obj__offering_id=course['offering_id'],
                instructor__xml_id__gte=900000
            ).count()
            
            # Contar clases del curso sin instructor
            classes_without = course['section_count'] - classes_with_instructor
            
            if classes_without > 0 or classes_with_synthetic > 0:
                # Estimar profesores necesarios
                professors_needed = max(
                    (course['section_count'] - classes_with_instructor + classes_with_synthetic) // self.OPTIMAL_LOAD,
                    1
                )
                
                missing.append({
                    'offering_id': course['offering_id'],
                    'course_name': course['offering__name'] or course['offering__code'] or f"Curso {course['offering_id']}",
                    'total_sections': course['section_count'],
                    'classes_without_instructor': classes_without,
                    'classes_with_synthetic': classes_with_synthetic,
                    'professors_needed': professors_needed,
                    'recommendation': f"Contratar {professors_needed} profesor(es) para cubrir {course['section_count']} sección(es)"
                })
        
        return missing
    
    def get_instructor_schedule(self, instructor_id: int, schedule_id: int = None) -> Dict:
        """
        Obtiene el horario completo de un instructor.
        
        Args:
            instructor_id: ID del instructor
            schedule_id: ID del horario (opcional, usa el más reciente si no se especifica)
        
        Returns:
            Dict con horario del instructor
        """
        if not schedule_id:
            schedule = Schedule.objects.order_by('-id').first()
            if not schedule:
                return {'error': 'No hay horarios generados'}
            schedule_id = schedule.id
        
        # Obtener clases del instructor en este horario
        assignments = ScheduleAssignment.objects.filter(
            schedule_id=schedule_id,
            class_obj__instructors__id=instructor_id
        ).select_related('class_obj', 'room', 'time_slot', 'class_obj__offering')
        
        instructor = Instructor.objects.get(id=instructor_id)
        
        classes = []
        for assignment in assignments:
            classes.append({
                'class_id': assignment.class_obj.id,
                'class_name': assignment.class_obj.offering.name if assignment.class_obj.offering else f"Class {assignment.class_obj.id}",
                'room': assignment.room.id if assignment.room else None,
                'room_capacity': assignment.room.capacity if assignment.room else None,
                'time_slot': {
                    'id': assignment.time_slot.id if assignment.time_slot else None,
                    'days': assignment.time_slot.days if assignment.time_slot else None,
                    'start': assignment.time_slot.start_time if assignment.time_slot else None,
                    'length': assignment.time_slot.length if assignment.time_slot else None,
                },
                'students': assignment.class_obj.class_limit
            })
        
        return {
            'instructor_id': instructor.id,
            'instructor_name': instructor.name,
            'instructor_email': instructor.email,
            'is_synthetic': instructor.xml_id >= 900000,
            'class_count': len(classes),
            'classes': classes,
            'load_status': self._get_load_status(len(classes)),
            'recommendation': self._get_recommendation(len(classes), instructor.xml_id)
        }
    
    def _get_load_status(self, class_count: int) -> str:
        """Determina el estado de carga"""
        if class_count >= self.OVERLOAD:
            return 'overloaded'
        elif class_count >= self.HIGH_LOAD:
            return 'high'
        else:
            return 'optimal'


class ConflictAnalyzer:
    """
    Analiza conflictos en horarios generados.
    """
    
    def analyze_schedule_conflicts(self, schedule_id: int) -> Dict:
        """
        Analiza todos los conflictos en un horario.
        
        Returns:
            Dict con conflictos detectados
        """
        schedule = Schedule.objects.get(id=schedule_id)
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule
        ).select_related('class_obj', 'room', 'time_slot')
        
        conflicts = {
            'room_conflicts': [],
            'capacity_issues': [],
            'instructor_conflicts': [],
            'total_conflicts': 0
        }
        
        # Detectar conflictos de aula
        room_schedule = defaultdict(list)
        for assignment in assignments:
            if assignment.room and assignment.time_slot:
                key = (assignment.room.id, assignment.time_slot.id)
                room_schedule[key].append(assignment)
        
        for (room_id, timeslot_id), classes in room_schedule.items():
            if len(classes) > 1:
                conflicts['room_conflicts'].append({
                    'room_id': room_id,
                    'timeslot_id': timeslot_id,
                    'conflicting_classes': [c.class_obj.id for c in classes],
                    'severity': 'high'
                })
        
        # Detectar problemas de capacidad
        for assignment in assignments:
            if assignment.room and assignment.class_obj:
                if assignment.room.capacity < assignment.class_obj.class_limit:
                    conflicts['capacity_issues'].append({
                        'class_id': assignment.class_obj.id,
                        'class_limit': assignment.class_obj.class_limit,
                        'room_id': assignment.room.id,
                        'room_capacity': assignment.room.capacity,
                        'overflow': assignment.class_obj.class_limit - assignment.room.capacity,
                        'severity': 'medium'
                    })
        
        conflicts['total_conflicts'] = (
            len(conflicts['room_conflicts']) + 
            len(conflicts['capacity_issues'])
        )
        
        return conflicts


class RoomUtilizationAnalyzer:
    """
    Analiza la utilización de aulas.
    """
    
    def analyze_room_utilization(self, schedule_id: int) -> Dict:
        """
        Analiza qué tan utilizadas están las aulas.
        
        Returns:
            Dict con estadísticas de utilización
        """
        schedule = Schedule.objects.get(id=schedule_id)
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule
        ).select_related('room', 'time_slot')
        
        # Contar asignaciones por aula
        room_usage = defaultdict(list)
        for assignment in assignments:
            if assignment.room:
                room_usage[assignment.room.id].append(assignment)
        
        rooms_data = []
        all_rooms = Room.objects.all()
        
        for room in all_rooms:
            usage_count = len(room_usage.get(room.id, []))
            
            # Calcular utilización (asumiendo ~50 slots útiles por semana)
            total_available_slots = 50
            utilization_percentage = (usage_count / total_available_slots) * 100 if usage_count > 0 else 0
            
            status = 'unused'
            if utilization_percentage >= 80:
                status = 'overused'
            elif utilization_percentage >= 50:
                status = 'well_used'
            elif utilization_percentage > 0:
                status = 'underused'
            
            rooms_data.append({
                'room_id': room.id,
                'capacity': room.capacity,
                'assignments': usage_count,
                'utilization_percentage': round(utilization_percentage, 1),
                'status': status,
                'recommendation': self._get_room_recommendation(status, usage_count, room.capacity)
            })
        
        rooms_data.sort(key=lambda x: x['utilization_percentage'], reverse=True)
        
        return {
            'rooms': rooms_data,
            'total_rooms': len(all_rooms),
            'used_rooms': sum(1 for r in rooms_data if r['assignments'] > 0),
            'unused_rooms': sum(1 for r in rooms_data if r['assignments'] == 0),
            'avg_utilization': sum(r['utilization_percentage'] for r in rooms_data) / len(rooms_data) if rooms_data else 0
        }
    
    def _get_room_recommendation(self, status: str, usage: int, capacity: int) -> str:
        """Genera recomendación para aula"""
        if status == 'unused':
            return f"💡 Aula sin uso - Considerar para nuevas clases o mantenimiento"
        elif status == 'underused':
            return f"ℹ️ Poco usada ({usage} clases) - Potencial para más clases"
        elif status == 'well_used':
            return f"✅ Bien utilizada ({usage} clases) - Balance óptimo"
        else:
            return f"⚠️ Sobre-utilizada ({usage} clases) - Considerar distribuir carga"
