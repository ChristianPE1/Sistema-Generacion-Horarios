"""
Sistema de validación de restricciones para el algoritmo genético.
Define y evalúa restricciones duras (hard) y blandas (soft).
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from .models import Class, Room, TimeSlot, Instructor, ClassInstructor, GroupConstraint, GroupConstraintClass
import math


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
        - hard_constraint_weight: Peso de las restricciones duras (reducido a 1000 para evitar fitness negativos)
        - soft_constraint_weight: Peso de las restricciones blandas
        """
        self.hard_weight = hard_constraint_weight
        self.soft_weight = soft_constraint_weight
        
        # Cache de datos para optimizar evaluaciones
        self.class_instructors: Dict[int, Set[int]] = {}
        self.class_students: Dict[int, Set[int]] = {}
        self.room_capacities: Dict[int, int] = {}
        self.room_locations: Dict[int, Tuple[float, float]] = {}
        self.class_limits: Dict[int, int] = {}
        self.room_preferences: Dict[int, Dict[int, float]] = {}
        self.time_preferences: Dict[int, Dict[int, float]] = {}
        self.timeslot_cache: Dict[int, Tuple] = {}  # Caché de timeslots
        self.group_constraints: List[Dict] = []  # Restricciones de grupo (BTB, etc.)
    
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
            
            # Parsear location (formato: "x,y")
            if room.location:
                try:
                    coords = room.location.split(',')
                    x, y = float(coords[0]), float(coords[1])
                    self.room_locations[room.id] = (x, y)
                except:
                    self.room_locations[room.id] = (0.0, 0.0)
            else:
                self.room_locations[room.id] = (0.0, 0.0)
        
        # Cargar límites de clase
        for class_obj in classes:
            self.class_limits[class_obj.id] = class_obj.class_limit
        
        # Cargar preferencias de aula
        for class_obj in classes:
            prefs = ClassRoom.objects.filter(
                class_obj=class_obj
            ).values_list('room_id', 'preference')
            self.room_preferences[class_obj.id] = dict(prefs)
        
        # Cargar preferencias de horario y cachear timeslots
        all_timeslots = TimeSlot.objects.all()
        for ts in all_timeslots:
            self.timeslot_cache[ts.id] = (ts.days, ts.start_time, ts.length)
        
        for class_obj in classes:
            time_slots = TimeSlot.objects.filter(
                class_obj=class_obj
            ).values_list('id', 'preference')
            self.time_preferences[class_obj.id] = dict(time_slots)
        
        # Cargar group constraints
        all_constraints = GroupConstraint.objects.all()
        for constraint in all_constraints:
            class_ids = GroupConstraintClass.objects.filter(
                constraint=constraint
            ).values_list('class_obj_id', flat=True)
            
            self.group_constraints.append({
                'id': constraint.id,
                'type': constraint.constraint_type,
                'preference': constraint.preference,
                'classes': list(class_ids)
            })
    
    def evaluate(self, individual) -> float:
        """
        Evalúa un individuo y retorna su fitness.
        Fitness = BASE - (violaciones_duras * peso_duro + violaciones_blandas * peso_blando)
        
        BASE_FITNESS ajustado dinámicamente según el dataset:
        - Dataset pequeño (<100 clases): BASE = 10,000
        - Dataset mediano (100-300): BASE = 50,000  
        - Dataset grande (>300): BASE = 100,000
        
        Escala de fitness:
        - BASE - 1000 = Perfecto (sin violaciones críticas)
        - BASE - 5000 = Excelente
        - BASE - 10000 = Bueno
        - < BASE - 20000 = Necesita mejoras
        """
        hard_violations = self._evaluate_hard_constraints(individual)
        soft_violations = self._evaluate_soft_constraints(individual)
        
        # Penalización total
        penalty = (hard_violations * self.hard_weight + 
                  soft_violations * self.soft_weight)
        
        # BASE_FITNESS dinámico con restricciones relajadas
        # Fórmula: BASE = num_classes * 500 (más margen con restricciones reducidas)
        num_classes = len(individual.genes)
        BASE_FITNESS = num_classes * 500.0
        
        # Mínimo 50k, máximo 300k
        BASE_FITNESS = max(50000.0, min(300000.0, BASE_FITNESS))
        
        fitness = BASE_FITNESS - penalty
        
        return fitness
    
    def _evaluate_hard_constraints(self, individual) -> int:
        """
        Evalúa restricciones duras y retorna el número de violaciones.
        
        RESTRICCIONES HABILITADAS:
        - Conflictos de instructor (HABILITADO - crítico para calidad)
        - Conflictos de aula (HABILITADO - crítico)
        - Violaciones de capacidad (HABILITADO - crítico)
        - Conflictos de estudiantes (DESHABILITADO - post-procesamiento manual)
        """
        violations = 0
        
        # Obtener asignaciones agrupadas
        time_slots_map = self._get_timeslots_from_genes(individual)
        
        # 1. Conflictos de instructor (REACTIVADO - peso 100)
        violations += self._check_instructor_conflicts(individual, time_slots_map)
        
        # 2. Conflictos de aula (CRÍTICO - misma aula, mismo horario)
        violations += self._check_room_conflicts(individual, time_slots_map)
        
        # 3. Conflictos de estudiantes - TEMPORALMENTE IGNORADO
        # (se resolverá manualmente después de generar horario base)
        # violations += self._check_student_conflicts(individual, time_slots_map)
        
        # 4. Violaciones de capacidad (CRÍTICO - aula muy pequeña)
        violations += self._check_capacity_violations(individual)
        
        return violations
    
    def _evaluate_soft_constraints(self, individual) -> float:
        """
        Evalúa restricciones blandas y retorna una penalización acumulada.
        
        NOTA: Preferencias de aula y horario ELIMINADAS según optimización.
        Solo se evalúan constraints estructurales (gaps, group constraints).
        """
        penalty = 0.0
        
        # 1. Gaps en horarios de instructores
        penalty += self._check_instructor_gaps(individual)
        
        # 2. Restricciones de grupo (BTB, DIFF_TIME, SAME_TIME)
        penalty += self._check_group_constraints(individual)
        
        return penalty
    
    def _get_timeslots_from_genes(self, individual) -> Dict[int, Tuple]:
        """Obtiene los detalles de los timeslots desde los genes usando caché"""
        timeslots_data = {}
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            if timeslot_id and timeslot_id in self.timeslot_cache:
                timeslots_data[class_id] = self.timeslot_cache[timeslot_id]
            else:
                timeslots_data[class_id] = (None, None, None)
        
        return timeslots_data
    
    def _check_instructor_conflicts(self, individual, time_slots_map) -> int:
        """Verifica conflictos de horario para instructores (OPTIMIZADO)"""
        conflicts = 0
        instructor_schedules = defaultdict(list)
        
        # Agrupar clases por instructor
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            instructors = self.class_instructors.get(class_id, set())
            
            # Si no hay instructores, no hay conflicto posible
            if not instructors:
                continue
            
            days, start, length = time_slots_map.get(class_id, (None, None, None))
            
            if days and start is not None and length:
                class_info = {
                    'class_id': class_id,
                    'days': days,
                    'start': start,
                    'end': start + length
                }
                for instructor_id in instructors:
                    instructor_schedules[instructor_id].append(class_info)
        
        # Verificar solapamientos (optimizado: solo verificar si hay >1 clase)
        for instructor_id, schedule in instructor_schedules.items():
            if len(schedule) < 2:
                continue  # Sin conflictos posibles
            
            # Verificar pares
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if self._times_overlap(schedule[i], schedule[j]):
                        conflicts += 1
        
        return conflicts
    
    def _check_room_conflicts(self, individual, time_slots_map) -> int:
        """Verifica conflictos de horario en aulas (OPTIMIZADO)"""
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
        
        # Verificar solapamientos (optimizado: solo verificar si hay >1 clase)
        for room_id, schedule in room_schedules.items():
            if len(schedule) < 2:
                continue  # Sin conflictos posibles
            
            # Verificar pares
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
            
            # Si no hay estudiantes, no hay conflicto posible
            if not students:
                continue
            
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
    
    # ELIMINADO: _check_room_preferences() - No se evalúan preferencias de aula
    # ELIMINADO: _check_time_preferences() - No se evalúan preferencias de horario
    # Razón: Optimización para enfocarse solo en constraints estructurales
    
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
    
    def _check_group_constraints(self, individual) -> float:
        """
        Evalúa restricciones de grupo (BTB, DIFF_TIME, SAME_TIME).
        Retorna penalización acumulada según el tipo y preferencia.
        """
        penalty = 0.0
        time_slots_map = self._get_timeslots_from_genes(individual)
        
        for constraint in self.group_constraints:
            constraint_type = constraint['type']
            preference = constraint['preference']
            class_ids = constraint['classes']
            
            # Filtrar clases que están en el individuo
            valid_classes = [cid for cid in class_ids if cid in individual.genes]
            
            if len(valid_classes) < 2:
                continue  # Necesitamos al menos 2 clases para evaluar
            
            if constraint_type == 'BTB':
                penalty += self._evaluate_btb_constraint(valid_classes, individual, time_slots_map, preference)
            elif constraint_type == 'DIFF_TIME':
                penalty += self._evaluate_diff_time_constraint(valid_classes, individual, time_slots_map, preference)
            elif constraint_type == 'SAME_TIME':
                penalty += self._evaluate_same_time_constraint(valid_classes, individual, time_slots_map, preference)
        
        return penalty
    
    def _evaluate_btb_constraint(self, class_ids: List[int], individual, time_slots_map: Dict, preference: str) -> float:
        """
        Evalúa restricción Back-To-Back (BTB).
        Penaliza clases consecutivas en edificios lejanos.
        """
        penalty = 0.0
        
        # Comparar cada par de clases
        for i in range(len(class_ids)):
            for j in range(i + 1, len(class_ids)):
                class1_id = class_ids[i]
                class2_id = class_ids[j]
                
                room1_id, timeslot1_id = individual.genes.get(class1_id, (None, None))
                room2_id, timeslot2_id = individual.genes.get(class2_id, (None, None))
                
                if not (room1_id and room2_id and timeslot1_id and timeslot2_id):
                    continue
                
                days1, start1, length1 = time_slots_map.get(class1_id, (None, None, None))
                days2, start2, length2 = time_slots_map.get(class2_id, (None, None, None))
                
                if not (days1 and start1 is not None and days2 and start2 is not None):
                    continue
                
                # Verificar si son consecutivas (BTB)
                end1 = start1 + length1
                end2 = start2 + length2
                
                # Verificar si comparten días
                share_day = any(days1[k] == '1' and days2[k] == '1' for k in range(min(len(days1), len(days2))))
                
                if share_day:
                    # Son consecutivas si end1 == start2 o end2 == start1
                    is_back_to_back = (end1 == start2) or (end2 == start1)
                    
                    if is_back_to_back:
                        # Calcular distancia entre aulas
                        distance = self._calculate_distance(room1_id, room2_id)
                        
                        # Penalización según preferencia y distancia
                        if preference == 'PROHIBITED':
                            if distance > 200:  # >200 metros
                                penalty += 100.0  # Penalización alta
                            elif distance > 50:
                                penalty += 20.0
                            else:
                                penalty += 2.0
                        elif preference == 'STRONGLY_DISCOURAGED':
                            if distance > 200:
                                penalty += 50.0
                            elif distance > 50:
                                penalty += 10.0
                            else:
                                penalty += 1.0
                        elif preference == 'DISCOURAGED':
                            if distance > 200:
                                penalty += 20.0
                            elif distance > 50:
                                penalty += 5.0
                            else:
                                penalty += 0.5
        
        return penalty
    
    def _evaluate_diff_time_constraint(self, class_ids: List[int], individual, time_slots_map: Dict, preference: str) -> float:
        """
        Evalúa restricción DIFF_TIME.
        Penaliza clases que se solapan (deberían estar en horarios diferentes).
        """
        penalty = 0.0
        
        for i in range(len(class_ids)):
            for j in range(i + 1, len(class_ids)):
                class1_id = class_ids[i]
                class2_id = class_ids[j]
                
                days1, start1, length1 = time_slots_map.get(class1_id, (None, None, None))
                days2, start2, length2 = time_slots_map.get(class2_id, (None, None, None))
                
                if not (days1 and start1 is not None and days2 and start2 is not None):
                    continue
                
                # Verificar solapamiento
                share_day = any(days1[k] == '1' and days2[k] == '1' for k in range(min(len(days1), len(days2))))
                
                if share_day:
                    end1 = start1 + length1
                    end2 = start2 + length2
                    overlaps = not (end1 <= start2 or end2 <= start1)
                    
                    if overlaps:
                        # Penalizar según preferencia
                        if preference == 'REQUIRED':
                            penalty += 50.0
                        elif preference == 'STRONGLY_PREFERRED':
                            penalty += 20.0
                        elif preference == 'PREFERRED':
                            penalty += 10.0
        
        return penalty
    
    def _evaluate_same_time_constraint(self, class_ids: List[int], individual, time_slots_map: Dict, preference: str) -> float:
        """
        Evalúa restricción SAME_TIME.
        Penaliza clases que NO se solapan (deberían estar al mismo tiempo).
        """
        penalty = 0.0
        
        for i in range(len(class_ids)):
            for j in range(i + 1, len(class_ids)):
                class1_id = class_ids[i]
                class2_id = class_ids[j]
                
                days1, start1, length1 = time_slots_map.get(class1_id, (None, None, None))
                days2, start2, length2 = time_slots_map.get(class2_id, (None, None, None))
                
                if not (days1 and start1 is not None and days2 and start2 is not None):
                    continue
                
                # Verificar si NO se solapan
                share_day = any(days1[k] == '1' and days2[k] == '1' for k in range(min(len(days1), len(days2))))
                
                if share_day:
                    end1 = start1 + length1
                    end2 = start2 + length2
                    overlaps = not (end1 <= start2 or end2 <= start1)
                    
                    if not overlaps:
                        # Penalizar si NO se solapan (deberían estar al mismo tiempo)
                        if preference == 'REQUIRED':
                            penalty += 50.0
                        elif preference == 'STRONGLY_PREFERRED':
                            penalty += 20.0
                        elif preference == 'PREFERRED':
                            penalty += 10.0
        
        return penalty
    
    def _calculate_distance(self, room1_id: int, room2_id: int) -> float:
        """
        Calcula distancia euclidiana entre dos aulas.
        Retorna distancia en metros.
        """
        loc1 = self.room_locations.get(room1_id, (0.0, 0.0))
        loc2 = self.room_locations.get(room2_id, (0.0, 0.0))
        
        x1, y1 = loc1
        x2, y2 = loc2
        
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) * 10  # * 10 para convertir a metros
        
        return distance
    
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
                'instructor_gaps_penalty': self._check_instructor_gaps(individual),
                'group_constraints_penalty': self._check_group_constraints(individual)
            },
            'total_fitness': individual.fitness
        }
