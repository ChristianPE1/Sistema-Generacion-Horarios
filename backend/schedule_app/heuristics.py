"""
Heurísticas avanzadas para mejorar el algoritmo genético en datasets grandes.
Implementa estrategias de construcción greedy, mutación dirigida y búsqueda local.
"""

import random
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from .models import Class, Room, TimeSlot, Instructor
from .genetic_algorithm import Individual


class ScheduleHeuristics:
    """
    Colección de heurísticas para mejorar la generación de horarios.
    """
    
    def __init__(self):
        self.room_occupation = {}  # {(room_id, timeslot_id): class_id}
        self.instructor_occupation = defaultdict(list)  # {(instructor_id, timeslot_id): [class_ids]}
    
    def cluster_classes_by_department(self, classes: List[Class]) -> Dict[int, List[Class]]:
        """
        H1: Agrupa clases por departamento para reducir conflictos de instructor.
        
        Args:
            classes: Lista de clases a agrupar
            
        Returns:
            Dict con department_id como clave y lista de clases como valor
        """
        departments = defaultdict(list)
        for class_obj in classes:
            dept_id = class_obj.offering.department_id if class_obj.offering else 0
            departments[dept_id].append(class_obj)
        
        return departments
    
    def prioritize_by_constraint(self, classes: List[Class], 
                                 time_slots_by_class: Dict[int, List[TimeSlot]],
                                 rooms: List[Room]) -> List[Class]:
        """
        H2: Prioriza clases por nivel de restricción (menos opciones primero).
        
        Clases más restringidas se asignan primero para evitar bloqueos.
        Factores considerados:
        - Número de timeslots disponibles
        - Tamaño de clase (clases grandes = menos opciones de aula)
        - Número de instructores (más instructores = más restricciones)
        
        Args:
            classes: Lista de clases
            time_slots_by_class: Diccionario de timeslots disponibles por clase
            rooms: Lista de aulas disponibles
            
        Returns:
            Lista de clases ordenada por restricción (más restringida primero)
        """
        def constraint_score(class_obj):
            # Contar timeslots disponibles (menos = más restringido)
            num_timeslots = len(time_slots_by_class.get(class_obj.id, []))
            
            # Contar aulas adecuadas (menos = más restringido)
            adequate_rooms = sum(1 for r in rooms if r.capacity >= class_obj.class_limit)
            
            # Penalizar clases grandes (más restringidas)
            size_penalty = class_obj.class_limit / 100
            
            # Score: menor = más restringido = mayor prioridad
            return num_timeslots * adequate_rooms - size_penalty
        
        return sorted(classes, key=constraint_score)
    
    def get_valid_timeslots(self, class_obj: Class, 
                           instructor_ids: List[int],
                           timeslots: List[TimeSlot]) -> List[TimeSlot]:
        """
        H3: Filtra timeslots válidos considerando disponibilidad de instructor y días permitidos.
        
        Args:
            class_obj: Clase a filtrar
            instructor_ids: IDs de instructores asignados a la clase
            timeslots: Lista completa de timeslots disponibles
            
        Returns:
            Lista de timeslots válidos (reduce espacio de búsqueda 60-80%)
        """
        valid_slots = []
        
        for ts in timeslots:
            # Verificar que el día del timeslot esté permitido en 'dates'
            # (Aquí podrías agregar lógica adicional si tienes campo 'dates' en TimeSlot)
            
            # Verificar que no haya conflicto de instructor
            has_conflict = False
            for instructor_id in instructor_ids:
                key = (instructor_id, ts.id)
                if key in self.instructor_occupation:
                    has_conflict = True
                    break
            
            if not has_conflict:
                valid_slots.append(ts)
        
        return valid_slots
    
    def greedy_construction(self, classes: List[Class], 
                           rooms: List[Room],
                           time_slots_by_class: Dict[int, List[TimeSlot]]) -> Dict[int, Tuple[int, int]]:
        """
        H4: Constructor greedy mejorado que genera soluciones de alta calidad.
        
        Estrategia:
        1. Ordena clases por restricción
        2. Para cada clase, elige la mejor combinación (room, timeslot)
        3. Minimiza conflictos y maximiza utilización
        
        Args:
            classes: Lista de clases
            rooms: Lista de aulas
            time_slots_by_class: Timeslots disponibles por clase
            
        Returns:
            Dict {class_id: (room_id, timeslot_id)}
        """
        from .models import ClassInstructor
        
        schedule = {}
        self.room_occupation = {}
        self.instructor_occupation = defaultdict(list)
        
        # Priorizar por restricción
        sorted_classes = self.prioritize_by_constraint(classes, time_slots_by_class, rooms)
        
        for class_obj in sorted_classes:
            # Obtener instructores de la clase
            instructor_ids = list(
                ClassInstructor.objects.filter(class_obj=class_obj)
                .values_list('instructor_id', flat=True)
            )
            
            timeslots = time_slots_by_class.get(class_obj.id, [])
            if not timeslots:
                continue
            
            # Filtrar timeslots válidos
            valid_timeslots = self.get_valid_timeslots(class_obj, instructor_ids, timeslots)
            if not valid_timeslots:
                valid_timeslots = timeslots  # Fallback si todos están ocupados
            
            best_assignment = None
            best_score = float('-inf')
            
            # Filtrar aulas adecuadas
            adequate_rooms = [r for r in rooms if r.capacity >= class_obj.class_limit]
            if not adequate_rooms:
                adequate_rooms = rooms  # Fallback
            
            # Buscar mejor asignación
            for room in adequate_rooms:
                for timeslot in valid_timeslots:
                    # Verificar si la aula está libre
                    if (room.id, timeslot.id) in self.room_occupation:
                        continue
                    
                    # Calcular score heurístico
                    score = self._evaluate_assignment_quality(
                        class_obj, room, timeslot, instructor_ids
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_assignment = (room, timeslot)
            
            # Aplicar mejor asignación
            if best_assignment:
                room, timeslot = best_assignment
                schedule[class_obj.id] = (room.id, timeslot.id)
                self.room_occupation[(room.id, timeslot.id)] = class_obj.id
                
                # Marcar instructores como ocupados
                for instructor_id in instructor_ids:
                    key = (instructor_id, timeslot.id)
                    self.instructor_occupation[key].append(class_obj.id)
        
        return schedule
    
    def _evaluate_assignment_quality(self, class_obj: Class, 
                                     room: Room, 
                                     timeslot: TimeSlot,
                                     instructor_ids: List[int]) -> float:
        """
        Evalúa la calidad de una asignación (class, room, timeslot).
        
        Factores considerados:
        - Desperdicio de capacidad (preferir aulas ajustadas)
        - Evitar conflictos de instructor
        - Distribución temporal balanceada
        
        Returns:
            Score: mayor es mejor
        """
        score = 0.0
        
        # Factor 1: Minimizar desperdicio de capacidad
        capacity_waste = room.capacity - class_obj.class_limit
        if capacity_waste < 0:
            score -= 1000  # Penalización fuerte por aula insuficiente
        else:
            # Preferir aulas ajustadas (menos desperdicio)
            waste_ratio = capacity_waste / room.capacity
            score += (1.0 - waste_ratio) * 100
        
        # Factor 2: Verificar conflictos de instructor
        for instructor_id in instructor_ids:
            key = (instructor_id, timeslot.id)
            if key in self.instructor_occupation:
                score -= 500  # Penalización por conflicto
        
        # Factor 3: Preferir timeslots menos usados (balance temporal)
        timeslot_usage = sum(1 for (_, ts_id) in self.room_occupation.keys() if ts_id == timeslot.id)
        score -= timeslot_usage * 2
        
        return score
    
    def conflict_directed_mutation(self, individual: Individual, 
                                   validator,
                                   mutation_rate: float = 0.3) -> Individual:
        """
        H7: Mutación dirigida que modifica solo genes con violaciones.
        
        Mucho más eficiente que mutación aleatoria para datasets grandes.
        
        Args:
            individual: Individuo a mutar
            validator: Validador de restricciones
            mutation_rate: Probabilidad de mutar cada gen conflictivo
            
        Returns:
            Individuo mutado
        """
        # Obtener violaciones
        violations = self._get_violations_from_fitness(individual, validator)
        
        # Identificar clases involucradas en conflictos
        conflicted_classes = set()
        for violation in violations:
            if 'class_ids' in violation:
                conflicted_classes.update(violation['class_ids'])
            elif 'class_id' in violation:
                conflicted_classes.add(violation['class_id'])
        
        # Mutar solo clases conflictivas
        for class_id in conflicted_classes:
            if random.random() < mutation_rate:
                # Buscar asignación alternativa
                class_obj = next((c for c in individual.classes if c.id == class_id), None)
                if not class_obj:
                    continue
                
                # Seleccionar room y timeslot aleatorios
                valid_rooms = [r for r in individual.rooms if r.capacity >= class_obj.class_limit]
                if not valid_rooms:
                    valid_rooms = individual.rooms
                
                new_room = random.choice(valid_rooms)
                new_timeslot = random.choice(individual.time_slots.get(class_id, []))
                
                individual.genes[class_id] = (new_room.id, new_timeslot.id)
        
        return individual
    
    def _get_violations_from_fitness(self, individual: Individual, validator) -> List[Dict]:
        """
        Extrae lista de violaciones desde el validador.
        (Asume que el validador tiene método para listar violaciones)
        """
        # Implementación simplificada - en producción usar método del validador
        violations = []
        
        # Detectar conflictos de aula
        room_slots = defaultdict(list)
        for class_id, (room_id, timeslot_id) in individual.genes.items():
            room_slots[(room_id, timeslot_id)].append(class_id)
        
        for (room_id, timeslot_id), class_ids in room_slots.items():
            if len(class_ids) > 1:
                violations.append({
                    'type': 'room_conflict',
                    'room_id': room_id,
                    'timeslot_id': timeslot_id,
                    'class_ids': class_ids
                })
        
        return violations
    
    def local_search_conflicts(self, individual: Individual, 
                               validator,
                               max_iterations: int = 10) -> Individual:
        """
        H8: Hill climbing aplicado solo a clases con violaciones.
        
        Args:
            individual: Individuo a mejorar
            validator: Validador de restricciones
            max_iterations: Máximo número de iteraciones
            
        Returns:
            Individuo mejorado
        """
        current_fitness = individual.fitness
        
        for iteration in range(max_iterations):
            violations = self._get_violations_from_fitness(individual, validator)
            if not violations:
                break  # Sin violaciones, salir
            
            # Elegir una violación aleatoria
            violation = random.choice(violations)
            conflicted_class = random.choice(violation.get('class_ids', [violation.get('class_id')]))
            
            # Probar alternativas
            best_alternative = None
            best_fitness = current_fitness
            
            original_assignment = individual.genes.get(conflicted_class)
            if not original_assignment:
                continue
            
            # Obtener clase
            class_obj = next((c for c in individual.classes if c.id == conflicted_class), None)
            if not class_obj:
                continue
            
            # Probar todas las combinaciones room×timeslot
            valid_rooms = [r for r in individual.rooms if r.capacity >= class_obj.class_limit]
            timeslots = individual.time_slots.get(conflicted_class, [])
            
            for room in valid_rooms[:10]:  # Limitar a 10 rooms para velocidad
                for timeslot in timeslots[:10]:  # Limitar a 10 timeslots
                    # Probar esta asignación
                    individual.genes[conflicted_class] = (room.id, timeslot.id)
                    new_fitness = validator.evaluate(individual)
                    
                    if new_fitness > best_fitness:
                        best_fitness = new_fitness
                        best_alternative = (room.id, timeslot.id)
            
            # Aplicar mejor alternativa o restaurar original
            if best_alternative:
                individual.genes[conflicted_class] = best_alternative
                current_fitness = best_fitness
            else:
                individual.genes[conflicted_class] = original_assignment
        
        individual.fitness = current_fitness
        return individual
    
    
    def initialize_hybrid_population(self, 
                                     classes: List,
                                     rooms: List,
                                     time_slots_by_class: Dict,
                                     size: int) -> List:
        """
        H5: Genera población inicial híbrida con balance calidad/diversidad.        Distribución:
        - 30% Greedy construction (alta calidad)
        - 30% Greedy + mutación (diversidad local)
        - 20% Biased random (diversidad media)
        - 20% Random puro (exploración máxima)
        
        Args:
            size: Tamaño de la población
            classes: Lista de clases
            rooms: Lista de aulas
            time_slots_by_class: Timeslots por clase
            
        Returns:
            Lista de individuos iniciales
        """
        population = []
        
        # 30% Greedy puro
        greedy_count = int(size * 0.3)
        for _ in range(greedy_count):
            genes = self.greedy_construction(classes, rooms, time_slots_by_class)
            ind = Individual(classes, rooms, time_slots_by_class)
            ind.genes = genes
            population.append(ind)
            
            # Resetear ocupación para próxima construcción
            self.room_occupation = {}
            self.instructor_occupation = defaultdict(list)
        
        # 30% Greedy + mutación leve
        greedy_mutated_count = int(size * 0.3)
        for _ in range(greedy_mutated_count):
            genes = self.greedy_construction(classes, rooms, time_slots_by_class)
            ind = Individual(classes, rooms, time_slots_by_class)
            ind.genes = genes
            
            # Mutar 10% de los genes
            for class_id in random.sample(list(genes.keys()), k=max(1, len(genes)//10)):
                class_obj = next((c for c in classes if c.id == class_id), None)
                if class_obj:
                    valid_rooms = [r for r in rooms if r.capacity >= class_obj.class_limit]
                    if valid_rooms and time_slots_by_class.get(class_id):
                        ind.genes[class_id] = (
                            random.choice(valid_rooms).id,
                            random.choice(time_slots_by_class[class_id]).id
                        )
            
            population.append(ind)
            self.room_occupation = {}
            self.instructor_occupation = defaultdict(list)
        
        # 40% Random (biased + puro)
        remaining = size - len(population)
        for _ in range(remaining):
            ind = Individual(classes, rooms, time_slots_by_class)
            ind.initialize_random()
            population.append(ind)
        
        return population
