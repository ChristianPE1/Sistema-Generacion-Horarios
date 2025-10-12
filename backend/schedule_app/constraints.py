"""
Sistema de validación de restricciones para el algoritmo genético.
Define y evalúa restricciones duras (hard) y blandas (soft).
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from .models import Class, Room, TimeSlot, Instructor, ClassInstructor


class ConstraintValidator:
    """
    Valida restricciones duras y blandas para evaluar la calidad de una solución.
    
    Restricciones Duras (DEBEN cumplirse):
    - No solapamiento de clases del mismo instructor
    - No solapamiento de clases en la misma aula
    - No solapamiento de clases del mismo estudiante (mismo curso/grupo)
    - Capacidad del aula >= límite de estudiantes de la clase
    
    Restricciones Blandas (PREFERENCIAS):
    - Preferencias de aula para cada clase
    - Preferencias de horario para cada clase
    - Minimizar ventanas horarias (gaps) para instructores
    - Distribución equilibrada de clases
    """
    
    def __init__(self, 
                 hard_constraint_weight: float = 1000.0,
                 soft_constraint_weight: float = 1.0):
        """
        Parámetros:
        - hard_constraint_weight: Peso de las restricciones duras
        - soft_constraint_weight: Peso de las restricciones blandas
        """
        self.hard_weight = hard_constraint_weight
        self.soft_weight = soft_constraint_weight
        
        # Cache de datos para optimizar evaluaciones
        self.class_instructors: Dict[int, Set[int]] = {}
        self.class_students: Dict[int, Set[int]] = {}
        self.room_capacities: Dict[int, int] = {}
        self.class_limits: Dict[int, int] = {}
        self.room_preferences: Dict[int, Dict[int, float]] = {}
        self.time_preferences: Dict[int, Dict[int, float]] = {}
    
    def load_data(self, classes: List[Class], rooms: List[Room]):
        """Carga y cachea los datos necesarios para las validaciones"""
        from .models import ClassRoom, StudentClass
        
        # Cargar instructores por clase
        for class_obj in classes:
            instructors = ClassInstructor.objects.filter(
                class_obj=class_obj
            ).values_list('instructor_id', flat=True)
            self.class_instructors[class_obj.id] = set(instructors)
        
        # Cargar estudiantes por clase (mismo offering = mismo grupo de estudiantes)
        for class_obj in classes:
            if class_obj.offering_id:
                # Estudiantes del curso
                students = StudentClass.objects.filter(
                    class_obj__offering_id=class_obj.offering_id
                ).values_list('student_id', flat=True)
                self.class_students[class_obj.id] = set(students)
            else:
                self.class_students[class_obj.id] = set()
        
        # Cargar capacidades de aulas
        for room in rooms:
            self.room_capacities[room.id] = room.capacity
        
        # Cargar límites de clase
        for class_obj in classes:
            self.class_limits[class_obj.id] = class_obj.class_limit
        
        # Cargar preferencias de aula
        for class_obj in classes:
            prefs = ClassRoom.objects.filter(
                class_obj=class_obj
            ).values_list('room_id', 'preference')
            self.room_preferences[class_obj.id] = dict(prefs)
        
        # Cargar preferencias de horario
        for class_obj in classes:
            time_slots = TimeSlot.objects.filter(
                class_obj=class_obj
            ).values_list('id', 'preference')
            self.time_preferences[class_obj.id] = dict(time_slots)
    
    def evaluate(self, individual) -> float:
        """
        Evalúa un individuo y retorna su fitness.
        Fitness = MAX_SCORE - (violaciones_duras * peso_duro + violaciones_blandas * peso_blando)
        """
        hard_violations = self._evaluate_hard_constraints(individual)
        soft_violations = self._evaluate_soft_constraints(individual)
        
        # Penalización total
        penalty = (hard_violations * self.hard_weight + 
                  soft_violations * self.soft_weight)
        
        # Fitness: a mayor fitness, mejor solución
        # Usamos un valor base grande para tener fitness positivos
        fitness = 100000.0 - penalty
        
        return fitness
    
    def _evaluate_hard_constraints(self, individual) -> int:
        """Evalúa restricciones duras y retorna el número de violaciones"""
        violations = 0
        
        # Obtener asignaciones agrupadas
        time_slots_map = self._get_timeslots_from_genes(individual)
        
        # 1. Conflictos de instructor (mismo instructor, mismo horario)
        violations += self._check_instructor_conflicts(individual, time_slots_map)
        
        # 2. Conflictos de aula (misma aula, mismo horario)
        violations += self._check_room_conflicts(individual, time_slots_map)
        
        # 3. Conflictos de estudiantes (mismos estudiantes, mismo horario)
        violations += self._check_student_conflicts(individual, time_slots_map)
        
        # 4. Violaciones de capacidad (aula muy pequeña)
        violations += self._check_capacity_violations(individual)
        
        return violations
    
    def _evaluate_soft_constraints(self, individual) -> float:
        """Evalúa restricciones blandas y retorna una penalización acumulada"""
        penalty = 0.0
        
        # 1. Preferencias de aula no cumplidas
        penalty += self._check_room_preferences(individual)
        
        # 2. Preferencias de horario no cumplidas
        penalty += self._check_time_preferences(individual)
        
        # 3. Gaps en horarios de instructores
        penalty += self._check_instructor_gaps(individual)
        
        return penalty
    
    def _get_timeslots_from_genes(self, individual) -> Dict[int, Tuple]:
        """Obtiene los detalles de los timeslots desde los genes"""
        from .models import TimeSlot as TimeSlotModel
        
        timeslots_data = {}
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            if timeslot_id:
                try:
                    ts = TimeSlotModel.objects.get(id=timeslot_id)
                    timeslots_data[class_id] = (ts.days, ts.start_time, ts.length)
                except TimeSlotModel.DoesNotExist:
                    timeslots_data[class_id] = (None, None, None)
            else:
                timeslots_data[class_id] = (None, None, None)
        
        return timeslots_data
    
    def _check_instructor_conflicts(self, individual, time_slots_map) -> int:
        """Verifica conflictos de horario para instructores"""
        conflicts = 0
        instructor_schedules = defaultdict(list)
        
        # Agrupar clases por instructor
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            instructors = self.class_instructors.get(class_id, set())
            days, start, length = time_slots_map.get(class_id, (None, None, None))
            
            if days and start is not None and length:
                for instructor_id in instructors:
                    instructor_schedules[instructor_id].append({
                        'class_id': class_id,
                        'days': days,
                        'start': start,
                        'end': start + length
                    })
        
        # Verificar solapamientos
        for instructor_id, schedule in instructor_schedules.items():
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if self._times_overlap(schedule[i], schedule[j]):
                        conflicts += 1
        
        return conflicts
    
    def _check_room_conflicts(self, individual, time_slots_map) -> int:
        """Verifica conflictos de horario en aulas"""
        conflicts = 0
        room_schedules = defaultdict(list)
        
        # Agrupar clases por aula
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            days, start, length = time_slots_map.get(class_id, (None, None, None))
            
            if room_id and days and start is not None and length:
                room_schedules[room_id].append({
                    'class_id': class_id,
                    'days': days,
                    'start': start,
                    'end': start + length
                })
        
        # Verificar solapamientos
        for room_id, schedule in room_schedules.items():
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if self._times_overlap(schedule[i], schedule[j]):
                        conflicts += 1
        
        return conflicts
    
    def _check_student_conflicts(self, individual, time_slots_map) -> int:
        """Verifica conflictos de horario para estudiantes"""
        conflicts = 0
        student_schedules = defaultdict(list)
        
        # Agrupar clases por estudiante
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            students = self.class_students.get(class_id, set())
            days, start, length = time_slots_map.get(class_id, (None, None, None))
            
            if days and start is not None and length:
                for student_id in students:
                    student_schedules[student_id].append({
                        'class_id': class_id,
                        'days': days,
                        'start': start,
                        'end': start + length
                    })
        
        # Verificar solapamientos
        for student_id, schedule in student_schedules.items():
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if self._times_overlap(schedule[i], schedule[j]):
                        conflicts += 1
        
        return conflicts
    
    def _check_capacity_violations(self, individual) -> int:
        """Verifica violaciones de capacidad de aula"""
        violations = 0
        
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            if room_id:
                room_capacity = self.room_capacities.get(room_id, float('inf'))
                class_limit = self.class_limits.get(class_id, 0)
                
                if room_capacity < class_limit:
                    violations += 1
        
        return violations
    
    def _check_room_preferences(self, individual) -> float:
        """Calcula penalización por preferencias de aula no cumplidas"""
        penalty = 0.0
        
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            if room_id:
                preferences = self.room_preferences.get(class_id, {})
                # Si no hay preferencia definida, penalización neutral
                preference = preferences.get(room_id, 0.0)
                # Preferencias negativas aumentan la penalización
                if preference < 0:
                    penalty += abs(preference)
        
        return penalty
    
    def _check_time_preferences(self, individual) -> float:
        """Calcula penalización por preferencias de horario no cumplidas"""
        penalty = 0.0
        
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            if timeslot_id:
                preferences = self.time_preferences.get(class_id, {})
                preference = preferences.get(timeslot_id, 0.0)
                if preference < 0:
                    penalty += abs(preference)
        
        return penalty
    
    def _check_instructor_gaps(self, individual) -> float:
        """Calcula penalización por gaps en horarios de instructores"""
        penalty = 0.0
        instructor_schedules = defaultdict(list)
        
        time_slots_map = self._get_timeslots_from_genes(individual)
        
        # Agrupar por instructor y día
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            instructors = self.class_instructors.get(class_id, set())
            days, start, length = time_slots_map.get(class_id, (None, None, None))
            
            if days and start is not None:
                for instructor_id in instructors:
                    # Por cada día de la semana
                    for day_idx, day_active in enumerate(days):
                        if day_active == '1':
                            instructor_schedules[(instructor_id, day_idx)].append(start)
        
        # Calcular gaps
        for (instructor_id, day), times in instructor_schedules.items():
            if len(times) > 1:
                times_sorted = sorted(times)
                for i in range(len(times_sorted) - 1):
                    gap = times_sorted[i + 1] - times_sorted[i]
                    # Penalizar gaps grandes (más de 12 slots = 1 hora)
                    if gap > 12:
                        penalty += (gap - 12) * 0.1
        
        return penalty
    
    def _times_overlap(self, time1: Dict, time2: Dict) -> bool:
        """
        Verifica si dos horarios se solapan.
        Deben coincidir en al menos un día Y tener solapamiento de tiempo.
        """
        # Verificar si comparten al menos un día
        days1 = time1['days']
        days2 = time2['days']
        
        share_day = False
        for i in range(min(len(days1), len(days2))):
            if days1[i] == '1' and days2[i] == '1':
                share_day = True
                break
        
        if not share_day:
            return False
        
        # Verificar solapamiento de tiempo
        start1, end1 = time1['start'], time1['end']
        start2, end2 = time2['start'], time2['end']
        
        return not (end1 <= start2 or end2 <= start1)
    
    def get_conflicts_report(self, individual) -> Dict:
        """Genera un reporte detallado de conflictos"""
        time_slots_map = self._get_timeslots_from_genes(individual)
        
        return {
            'hard_constraints': {
                'instructor_conflicts': self._check_instructor_conflicts(individual, time_slots_map),
                'room_conflicts': self._check_room_conflicts(individual, time_slots_map),
                'student_conflicts': self._check_student_conflicts(individual, time_slots_map),
                'capacity_violations': self._check_capacity_violations(individual)
            },
            'soft_constraints': {
                'room_preference_penalty': self._check_room_preferences(individual),
                'time_preference_penalty': self._check_time_preferences(individual),
                'instructor_gaps_penalty': self._check_instructor_gaps(individual)
            },
            'total_fitness': individual.fitness
        }
