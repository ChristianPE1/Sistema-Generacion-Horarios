
import random
import numpy as np
from typing import List, Tuple, Dict, Set
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from .models import Class, Room, TimeSlot, Instructor
from .constraints import ConstraintValidator


class Individual:
    """
    Representa un individuo en la población (una solución candidata).
    Cada individuo es un cromosoma que contiene asignaciones de clase-aula-tiempo.
    """
    
    def __init__(self, classes: List[Class], rooms: List[Room], time_slots: Dict[int, List[TimeSlot]]):
        self.classes = classes
        self.rooms = rooms
        self.time_slots = time_slots  # {class_id: [TimeSlot]}
        self.genes = {}  # {class_id: (room_id, timeslot_id)}
        self.fitness = 0.0
        
    def initialize_random(self):
        """Inicialización inteligente con heurística de capacidad y evitación de conflictos"""
        # Rastrear ocupación para evitar conflictos básicos
        room_occupation = {}  # {(room_id, timeslot_id): set(class_ids)}
        instructor_occupation = {}  # {(instructor_id, timeslot_id): set(class_ids)}
        
        # Obtener instructores por clase (OPTIMIZADO: una sola query)
        from .models import ClassInstructor
        class_instructors_map = {}
        
        # Cargar todos los instructores de una vez
        class_ids = [c.id for c in self.classes]
        all_class_instructors = ClassInstructor.objects.filter(
            class_obj_id__in=class_ids
        ).values_list('class_obj_id', 'instructor_id')
        
        # Organizar en mapa
        for class_id, instructor_id in all_class_instructors:
            if class_id not in class_instructors_map:
                class_instructors_map[class_id] = []
            class_instructors_map[class_id].append(instructor_id)
        
        # Ordenar clases por límite (asignar primero las más grandes)
        sorted_classes = sorted(self.classes, key=lambda c: c.class_limit, reverse=True)
        
        for class_obj in sorted_classes:
            # Filtrar aulas por capacidad (heurística)
            suitable_rooms = [r for r in self.rooms if r.capacity >= class_obj.class_limit]
            if not suitable_rooms:
                suitable_rooms = self.rooms  # Fallback a todas las aulas
            
            # Preferir aulas cercanas a la capacidad necesaria
            suitable_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
            
            # Asignar slot de tiempo aleatorio de los disponibles para la clase
            available_slots = self.time_slots.get(class_obj.id, [])
            if not available_slots:
                # Si no hay slots, asignar None
                self.genes[class_obj.id] = (suitable_rooms[0].id if suitable_rooms else None, None)
                continue
            
            # Intentar encontrar asignación sin conflictos (máximo 20 intentos - optimizado)
            assigned = False
            best_assignment = None
            
            # Estrategia 1: Buscar slot completamente libre (sin conflictos)
            for attempt in range(20):  # Reducido de 50 a 20 para velocidad
                # Rotar entre aulas para mayor diversidad
                room = suitable_rooms[attempt % len(suitable_rooms)] if suitable_rooms else None
                time_slot = random.choice(available_slots)
                
                if not room or not time_slot:
                    continue
                
                # Verificar si hay conflicto de aula
                room_key = (room.id, time_slot.id)
                has_room_conflict = room_key in room_occupation
                
                # Verificar si hay conflicto de instructor
                has_instructor_conflict = False
                instructors = class_instructors_map.get(class_obj.id, [])
                for instructor_id in instructors:
                    inst_key = (instructor_id, time_slot.id)
                    if inst_key in instructor_occupation:
                        has_instructor_conflict = True
                        break
                
                # Si no hay conflictos, asignar y registrar
                if not has_room_conflict and not has_instructor_conflict:
                    self.genes[class_obj.id] = (room.id, time_slot.id)
                    room_occupation[room_key] = {class_obj.id}
                    for instructor_id in instructors:
                        instructor_occupation[(instructor_id, time_slot.id)] = {class_obj.id}
                    assigned = True
                    break
                
                # Guardar como backup (solo conflicto de aula, no de instructor)
                if not has_instructor_conflict and best_assignment is None:
                    best_assignment = (room, time_slot)
            
            # Estrategia 2: Si no se pudo evitar conflictos, usar backup o random
            if not assigned:
                if best_assignment:
                    room, time_slot = best_assignment
                else:
                    # Buscar timeslot con MENOS conflictos
                    min_conflicts = float('inf')
                    best_room = suitable_rooms[0] if suitable_rooms else None
                    best_slot = None
                    
                    for _ in range(10):  # Muestreo de slots (reducido de 20 a 10)
                        test_room = random.choice(suitable_rooms) if suitable_rooms else None
                        test_slot = random.choice(available_slots)
                        
                        if test_room and test_slot:
                            conflicts = 0
                            room_key = (test_room.id, test_slot.id)
                            if room_key in room_occupation:
                                conflicts += len(room_occupation[room_key])
                            
                            instructors = class_instructors_map.get(class_obj.id, [])
                            for instructor_id in instructors:
                                inst_key = (instructor_id, test_slot.id)
                                if inst_key in instructor_occupation:
                                    conflicts += 1
                            
                            if conflicts < min_conflicts:
                                min_conflicts = conflicts
                                best_room = test_room
                                best_slot = test_slot
                    
                    room = best_room
                    time_slot = best_slot
                
                # Asignar y REGISTRAR (esto es crítico)
                if room and time_slot:
                    self.genes[class_obj.id] = (room.id, time_slot.id)
                    room_key = (room.id, time_slot.id)
                    if room_key not in room_occupation:
                        room_occupation[room_key] = set()
                    room_occupation[room_key].add(class_obj.id)
                    
                    instructors = class_instructors_map.get(class_obj.id, [])
                    for instructor_id in instructors:
                        inst_key = (instructor_id, time_slot.id)
                        if inst_key not in instructor_occupation:
                            instructor_occupation[inst_key] = set()
                        instructor_occupation[inst_key].add(class_obj.id)
                else:
                    # Último recurso
                    self.genes[class_obj.id] = (suitable_rooms[0].id if suitable_rooms else None, None)
    
    def calculate_fitness(self, validator: 'ConstraintValidator'):
        self.fitness = validator.evaluate(self)
        return self.fitness
    
    def clone(self):
        """Crea una copia del individuo"""
        new_individual = Individual(self.classes, self.rooms, self.time_slots)
        new_individual.genes = self.genes.copy()
        new_individual.fitness = self.fitness
        return new_individual
    
    def repair(self, validator: 'ConstraintValidator', max_iterations=3):
        """
        Operador de reparación inteligente MEJORADO.
        Corrige violaciones de capacidad Y conflictos de aula ITERATIVAMENTE.
        """
        from collections import defaultdict
        
        # 1. Reparar violaciones de capacidad
        for class_id, (room_id, timeslot_id) in list(self.genes.items()):
            if room_id and timeslot_id:
                class_obj = next((c for c in self.classes if c.id == class_id), None)
                if class_obj:
                    room_capacity = validator.room_capacities.get(room_id, float('inf'))
                    if room_capacity < class_obj.class_limit:
                        # Buscar aula con capacidad adecuada
                        suitable_rooms = [r for r in self.rooms 
                                        if validator.room_capacities.get(r.id, 0) >= class_obj.class_limit]
                        if suitable_rooms:
                            # Elegir la más cercana en capacidad
                            suitable_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
                            self.genes[class_id] = (suitable_rooms[0].id, timeslot_id)
        
        # 2. Detectar y resolver conflictos de aula CONSIDERANDO DÍAS (ITERATIVO)
        for iteration in range(max_iterations):
            # Construir mapa: {room_id: [(class_id, timeslot_obj)]}
            room_schedule = defaultdict(list)
            
            # Cargar todos los timeslots de una vez (optimización)
            timeslot_map = {}  # {timeslot_id: TimeSlot}
            timeslot_ids = [ts_id for _, ts_id in self.genes.values() if ts_id]
            if timeslot_ids:
                from .models import TimeSlot as TS
                for ts in TS.objects.filter(id__in=timeslot_ids):
                    timeslot_map[ts.id] = ts
            
            for class_id, (room_id, timeslot_id) in self.genes.items():
                if room_id and timeslot_id and timeslot_id in timeslot_map:
                    room_schedule[room_id].append((class_id, timeslot_map[timeslot_id]))
            
            # Encontrar conflictos REALES (mismo aula, días que se solapan, horas que se solapan)
            conflicts_to_fix = []
            for room_id, assignments in room_schedule.items():
                for i in range(len(assignments)):
                    for j in range(i + 1, len(assignments)):
                        class1_id, ts1 = assignments[i]
                        class2_id, ts2 = assignments[j]
                        
                        # Verificar si días se solapan
                        days_overlap = any(d1 == '1' and d2 == '1' 
                                          for d1, d2 in zip(ts1.days, ts2.days))
                        
                        if days_overlap:
                            # Verificar si horarios se solapan
                            end1 = ts1.start_time + ts1.length
                            end2 = ts2.start_time + ts2.length
                            time_overlap = not (end1 <= ts2.start_time or end2 <= ts1.start_time)
                            
                            if time_overlap:
                                # CONFLICTO REAL
                                conflicts_to_fix.append((room_id, class1_id, class2_id, ts1.id, ts2.id))
            
            # Si no hay conflictos, salir del bucle
            if len(conflicts_to_fix) == 0:
                break
            
            # Resolver conflictos: reasignar clases conflictivas
            for room_id, class1_id, class2_id, ts1_id, ts2_id in conflicts_to_fix:
                # Mantener class1, reasignar class2
                class_id = class2_id
                timeslot_id = ts2_id
                class_obj = next((c for c in self.classes if c.id == class_id), None)
                if not class_obj:
                    continue
                
                # Obtener el timeslot actual
                current_timeslot = timeslot_map.get(timeslot_id)
                if not current_timeslot:
                    continue
                
                # Buscar aula alternativa que esté LIBRE en ese timeslot
                assigned_room = False
                candidate_rooms = [r for r in self.rooms 
                                 if validator.room_capacities.get(r.id, 0) >= class_obj.class_limit
                                 and r.id != room_id]  # Diferente a la que causa conflicto
                
                # Ordenar por capacidad más cercana
                candidate_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
                
                for candidate_room in candidate_rooms:
                    # Verificar si esta aula está libre en el timeslot actual
                    is_free = True
                    for other_class_id, (other_room_id, other_ts_id) in self.genes.items():
                        if other_class_id == class_id:
                            continue  # No comparar consigo mismo
                        if other_room_id == candidate_room.id and other_ts_id in timeslot_map:
                            other_ts = timeslot_map[other_ts_id]
                            # Verificar si días se solapan
                            days_overlap = any(d1 == '1' and d2 == '1' 
                                              for d1, d2 in zip(current_timeslot.days, other_ts.days))
                            if days_overlap:
                                # Verificar si horarios se solapan
                                end_current = current_timeslot.start_time + current_timeslot.length
                                end_other = other_ts.start_time + other_ts.length
                                time_overlap = not (end_current <= other_ts.start_time or end_other <= current_timeslot.start_time)
                                if time_overlap:
                                    is_free = False
                                    break
                    
                    if is_free:
                        # Asignar esta aula libre
                        self.genes[class_id] = (candidate_room.id, timeslot_id)
                        assigned_room = True
                        break
                
                # Si no encontró aula libre, intentar cambiar el timeslot
                if not assigned_room:
                    available_slots = self.time_slots.get(class_id, [])
                    if available_slots and len(available_slots) > 1:
                        # Buscar timeslot alternativo con aula disponible
                        for alt_slot in available_slots:
                            if alt_slot.id != timeslot_id:
                                # Buscar aula libre para este timeslot alternativo
                                for candidate_room in self.rooms:
                                    if validator.room_capacities.get(candidate_room.id, 0) < class_obj.class_limit:
                                        continue  # Capacidad insuficiente
                                    
                                    # Verificar si esta aula está libre en el nuevo timeslot
                                    is_free = True
                                    for other_class_id, (other_room_id, other_ts_id) in self.genes.items():
                                        if other_class_id == class_id:
                                            continue
                                        if other_room_id == candidate_room.id and other_ts_id in timeslot_map:
                                            other_ts = timeslot_map[other_ts_id]
                                            days_overlap = any(d1 == '1' and d2 == '1' 
                                                              for d1, d2 in zip(alt_slot.days, other_ts.days))
                                            if days_overlap:
                                                end_alt = alt_slot.start_time + alt_slot.length
                                                end_other = other_ts.start_time + other_ts.length
                                                time_overlap = not (end_alt <= other_ts.start_time or end_other <= alt_slot.start_time)
                                                if time_overlap:
                                                    is_free = False
                                                    break
                                    
                                    if is_free:
                                        self.genes[class_id] = (candidate_room.id, alt_slot.id)
                                        assigned_room = True
                                        break
                                
                                if assigned_room:
                                    break


class GeneticAlgorithm:
    """
    Implementación del Algoritmo Genético para generación de horarios.
    """
    
    def __init__(self, 
                 population_size: int = 100,
                 generations: int = 200,
                 mutation_rate: float = 0.20,  # Aumentado de 0.15 a 0.20 para mayor exploración
                 crossover_rate: float = 0.80,
                 elitism_size: int = 10,
                 tournament_size: int = 5):
        """
        population_size: Tamaño de la población
        generations: Número de generaciones
        mutation_rate: Probabilidad de mutación (0-1)
        crossover_rate: Probabilidad de cruce (0-1)
        elitism_size: Número de mejores individuos que pasan directamente
        tournament_size: Tamaño del torneo para selección - Reducido para diversidad
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.initial_mutation_rate = mutation_rate  # Guardar tasa inicial
        self.crossover_rate = crossover_rate
        self.elitism_size = elitism_size
        self.tournament_size = tournament_size
        
        self.population: List[Individual] = []
        self.best_individual: Individual = None
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        
        # Control de estancamiento (REDUCIDO para actuar más rápido)
        self.stagnation_counter = 0
        self.last_best_fitness = float('-inf')
        self.stagnation_threshold = 50  # Aumentado a 50 para datasets grandes
        
        # Optimización: Caching y batch processing
        self.use_batch_evaluation = True
    
    def initialize_population(self, classes: List[Class], rooms: List[Room], 
                            time_slots: Dict[int, List[TimeSlot]]):
        """Crea la población inicial con individuos aleatorios"""
        self.population = []
        for _ in range(self.population_size):
            individual = Individual(classes, rooms, time_slots)
            individual.initialize_random()
            self.population.append(individual)
    
    def evaluate_population(self, validator: 'ConstraintValidator'):
        """Evalúa el fitness de toda la población (OPTIMIZADO)"""
        # Evaluación secuencial optimizada (más rápido que threads por GIL)
        for individual in self.population:
            individual.calculate_fitness(validator)
        
        # Ordenar por fitness (mayor a menor)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Actualizar mejor individuo
        if not self.best_individual or self.population[0].fitness > self.best_individual.fitness:
            self.best_individual = self.population[0].clone()
        
        # Guardar estadísticas
        self.best_fitness_history.append(self.population[0].fitness)
        avg_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
        self.avg_fitness_history.append(avg_fitness)
    
    def tournament_selection(self) -> Individual:
        """
        Selección por torneo: elige k individuos aleatorios y retorna el mejor
        """
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda x: x.fitness)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """
        Operador de cruce: Combina dos padres para crear dos hijos.
        Usa cruce de un punto.
        """
        if random.random() > self.crossover_rate:
            return parent1.clone(), parent2.clone()
        
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        # Cruce de un punto
        class_ids = list(parent1.genes.keys())
        if len(class_ids) > 1:
            crossover_point = random.randint(1, len(class_ids) - 1)
            
            for i, class_id in enumerate(class_ids):
                if i >= crossover_point:
                    child1.genes[class_id] = parent2.genes[class_id]
                    child2.genes[class_id] = parent1.genes[class_id]
        
        return child1, child2
    
    def mutate(self, individual: Individual):
        """
        Operador de mutación inteligente con heurística.
        Puede cambiar el aula, el horario, o ambos.
        Incluye búsqueda local después de la mutación.
        """
        mutated = False
        for class_id in individual.genes:
            if random.random() < self.mutation_rate:
                mutated = True
                # Decidir qué mutar: aula, tiempo, o ambos
                mutation_type = random.choice(['room', 'time', 'both'])
                
                current_room_id, current_time_id = individual.genes[class_id]
                class_obj = next((c for c in individual.classes if c.id == class_id), None)
                
                if mutation_type in ['room', 'both'] and class_obj:
                    # Mutación inteligente: priorizar aulas con capacidad adecuada
                    suitable_rooms = [r for r in individual.rooms if r.capacity >= class_obj.class_limit]
                    if not suitable_rooms:
                        suitable_rooms = individual.rooms
                    
                    # 70% probabilidad de elegir aula óptima, 30% aleatoria (exploración)
                    if random.random() < 0.7 and suitable_rooms:
                        suitable_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
                        new_room = suitable_rooms[0]
                    else:
                        new_room = random.choice(individual.rooms)
                    current_room_id = new_room.id
                
                if mutation_type in ['time', 'both']:
                    # Mutar tiempo
                    if class_obj:
                        available_slots = individual.time_slots.get(class_id, [])
                        if available_slots:
                            new_time = random.choice(available_slots)
                            current_time_id = new_time.id
                
                individual.genes[class_id] = (current_room_id, current_time_id)
        
        # Búsqueda local desactivada temporalmente por lentitud
        # if mutated and random.random() < 0.1:
        #     self._local_search(individual)
    
    def _local_search(self, individual: Individual):
        """
        Búsqueda local SIMPLIFICADA: Solo prueba cambios de aula.
        """
        max_iterations = 3  # Reducido de 5 a 3
        
        for _ in range(max_iterations):
            # Seleccionar clase aleatoria
            class_ids = list(individual.genes.keys())
            if not class_ids:
                break
            
            class_id = random.choice(class_ids)
            current_room_id, current_time_id = individual.genes[class_id]
            
            # Probar cambiar solo aula (más rápido)
            class_obj = next((c for c in individual.classes if c.id == class_id), None)
            if not class_obj:
                continue
            
            # Probar aula aleatoria con capacidad adecuada
            suitable_rooms = [r for r in individual.rooms if r.capacity >= class_obj.class_limit]
            if suitable_rooms:
                test_room = random.choice(suitable_rooms[:min(3, len(suitable_rooms))])  # Reducido de 5 a 3
                individual.genes[class_id] = (test_room.id, current_time_id)
    
    def _apply_diversity_boost(self, validator: 'ConstraintValidator'):
        """
        Aplica múltiples estrategias para romper el estancamiento:
        1. Aumentar tasa de mutación temporalmente
        2. Inyectar nuevos individuos aleatorios
        3. Aplicar mutación intensa a parte de la población
        """
        import sys

        print(f"\nBOOST (estancamiento detectado)")
        sys.stdout.flush()
        
        # Estrategia 1: Aumentar tasa de mutación temporalmente (50% más)
        old_mutation_rate = self.mutation_rate
        self.mutation_rate = min(0.5, self.mutation_rate * 1.5)
        print(f"   • Mutación aumentada: {old_mutation_rate:.2f} → {self.mutation_rate:.2f}")
        
        # Estrategia 2: Reemplazar 20% de la población con individuos nuevos
        num_to_replace = int(self.population_size * 0.2)
        print(f"   • Inyectando {num_to_replace} individuos nuevos")
        
        # Mantener elite (mejores 10%)
        elite_size = int(self.population_size * 0.1)
        elite = self.population[:elite_size]
        
        # Generar nuevos individuos
        new_individuals = []
        for _ in range(num_to_replace):
            individual = Individual(
                [c for c in self.population[0].classes],
                [r for r in self.population[0].rooms],
                self.population[0].time_slots
            )
            individual.initialize_random()
            new_individuals.append(individual)
        
        # Reconstruir población: elite + nuevos + resto
        rest = self.population[elite_size:self.population_size - num_to_replace]
        self.population = elite + new_individuals + rest
        
        # Estrategia 3: Aplicar mutación fuerte a 30% de la población
        num_to_mutate = int(self.population_size * 0.3)
        print(f"   • Mutación intensa aplicada a {num_to_mutate} individuos")
        for i in range(num_to_mutate):
            # Mutación múltiple (3-5 genes)
            idx = elite_size + i  # No mutar elite
            if idx < len(self.population):
                for _ in range(random.randint(3, 5)):
                    self.mutate(self.population[idx])
        
        # Estrategia 4: Hill Climbing AGRESIVO sobre el mejor individuo
        print(f"   • Hill Climbing agresivo...")
        if self.best_individual:
            best_clone = self.best_individual.clone()
            
            # Intentar reasignar clases conflictivas 50 veces
            improved = False
            for attempt in range(50):
                # Reparar conflictos
                best_clone.repair(validator)
                
                # Intentar mover clases aleatoriamente
                classes_to_move = random.sample(list(best_clone.genes.keys()), 
                                               min(20, len(best_clone.genes)))
                
                for class_id in classes_to_move:
                    current_room, current_time = best_clone.genes[class_id]
                    
                    # Intentar timeslot diferente
                    available_slots = best_clone.time_slots.get(class_id, [])
                    if available_slots and len(available_slots) > 1:
                        # Elegir slot aleatorio diferente
                        new_slot = random.choice(available_slots)
                        if new_slot.id != current_time:
                            # Elegir aula adecuada
                            class_obj = next((c for c in best_clone.classes if c.id == class_id), None)
                            if class_obj:
                                suitable_rooms = [r for r in best_clone.rooms 
                                                if r.capacity >= class_obj.class_limit]
                                if suitable_rooms:
                                    new_room = random.choice(suitable_rooms[:5])  # Top 5
                                    best_clone.genes[class_id] = (new_room.id, new_slot.id)
                
                # Evaluar y ver si mejoró
                best_clone.calculate_fitness(validator)
                if best_clone.fitness > self.best_individual.fitness:
                    self.population[0] = best_clone
                    self.best_individual = best_clone
                    improved = True
                    print(f"     [OK] Hill Climbing mejoró: {self.best_individual.fitness:.0f} → {best_clone.fitness:.0f}")
                    break
            
            if not improved:
                print(f"     [WARNING] Hill Climbing sin mejora tras 50 intentos")
        
        # Re-evaluar población
        self.evaluate_population(validator)
        
        print(f"   [OK] Diversidad restaurada - Mejor fitness: {self.best_fitness_history[-1]:.0f}")
        sys.stdout.flush()
    
    def evolve(self, validator: 'ConstraintValidator') -> Individual:
        """
        Ejecuta el proceso evolutivo completo.
        Retorna el mejor individuo encontrado.
        """
        import sys
        import time
        start_time = time.time()
        
        # Evaluar población inicial
        print(f"\n[WAIT] Inicializando población de {self.population_size} individuos...")
        sys.stdout.flush()
        self.evaluate_population(validator)
        print(f"[OK] Población inicial evaluada - Mejor fitness: {self.best_fitness_history[0]:.2f}")
        sys.stdout.flush()
        
        for generation in range(self.generations):
            new_population = []
            
            # mantener los mejores individuos
            elite = self.population[:self.elitism_size]
            new_population.extend([ind.clone() for ind in elite])
            
            # Generar nueva población
            while len(new_population) < self.population_size:
                # Selección
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                # Cruce
                child1, child2 = self.crossover(parent1, parent2)
                
                # Mutación
                self.mutate(child1)
                self.mutate(child2)
                
                # Reparación SIEMPRE activada (crítico para eliminar conflictos)
                child1.repair(validator)
                child2.repair(validator)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            self.population = new_population
            self.evaluate_population(validator)
            
            # **DETECCIÓN DE ESTANCAMIENTO**
            current_best = self.best_fitness_history[-1]
            improvement = current_best - self.last_best_fitness
            
            if improvement > 1.0:  # Mejora significativa (>1 punto)
                self.stagnation_counter = 0
                self.last_best_fitness = current_best
            else:
                self.stagnation_counter += 1
            
            # **ESTRATEGIAS ANTI-ESTANCAMIENTO**
            if self.stagnation_counter >= self.stagnation_threshold:
                self._apply_diversity_boost(validator)
                self.stagnation_counter = 0  # Resetear contador
            
            # Reducir gradualmente mutación después de boost (decay suave)
            if self.mutation_rate > self.initial_mutation_rate:
                self.mutation_rate = max(self.initial_mutation_rate, 
                                        self.mutation_rate * 0.98)  # Decay 2% por gen
            
            # Log de progreso (cada 2 generaciones)
            if (generation + 1) % 2 == 0:
                elapsed = time.time() - start_time
                avg_time_per_gen = elapsed / (generation + 1)
                remaining_time = avg_time_per_gen * (self.generations - generation - 1)
                
                # Mostrar indicador de estancamiento
                stagnation_indicator = ""
                if self.stagnation_counter > 30:
                    stagnation_indicator = " [WARNING]ESTANCADO"
                elif self.stagnation_counter > 20:
                    stagnation_indicator = " ⏸️"
                
                print(f"Gen {generation + 1}/{self.generations} | "
                      f"Mejor: {self.best_fitness_history[-1]:.0f} | "
                      f"Promedio: {self.avg_fitness_history[-1]:.0f} | "
                      f"Tiempo: {elapsed:.0f}s | ETA: {remaining_time:.0f}s{stagnation_indicator}")
                sys.stdout.flush()  # Forzar salida inmediata
            
            # NO HAY PARADA PREMATURA - Siempre completar todas las generaciones solicitadas
            # El usuario espera que se completen TODAS las generaciones para maximizar la calidad
        
        total_time = time.time() - start_time
        print(f"\n[OK] Evolución completada en {total_time:.1f} segundos")
        sys.stdout.flush()
        
        return self.best_individual
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas del proceso evolutivo"""
        return {
            'best_fitness': self.best_individual.fitness if self.best_individual else 0,
            'final_avg_fitness': self.avg_fitness_history[-1] if self.avg_fitness_history else 0,
            'generations': len(self.best_fitness_history),
            'best_fitness_history': self.best_fitness_history,
            'avg_fitness_history': self.avg_fitness_history,
            'improvement': (self.best_fitness_history[-1] - self.best_fitness_history[0]) 
                          if len(self.best_fitness_history) > 0 else 0
        }
