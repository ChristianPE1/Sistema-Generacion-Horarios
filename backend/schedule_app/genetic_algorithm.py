
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
    
    def repair(self, validator: 'ConstraintValidator'):
        """
        Operador de reparación inteligente MEJORADO.
        Corrige violaciones de capacidad Y conflictos de aula.
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
        
        # 2. Detectar y resolver conflictos de aula
        room_schedule = defaultdict(list)  # {(room_id, timeslot_id): [class_ids]}
        
        for class_id, (room_id, timeslot_id) in self.genes.items():
            if room_id and timeslot_id:
                room_schedule[(room_id, timeslot_id)].append(class_id)
        
        # Encontrar conflictos (más de 1 clase en misma aula/tiempo)
        conflicts = [(key, classes) for key, classes in room_schedule.items() if len(classes) > 1]
        
        # Resolver conflictos: reasignar clases conflictivas a otras aulas
        for (room_id, timeslot_id), conflicting_classes in conflicts:
            # Mantener la primera clase, reasignar las demás
            for class_id in conflicting_classes[1:]:
                class_obj = next((c for c in self.classes if c.id == class_id), None)
                if not class_obj:
                    continue
                
                # Buscar aula alternativa con capacidad adecuada
                available_rooms = [r for r in self.rooms 
                                 if validator.room_capacities.get(r.id, 0) >= class_obj.class_limit
                                 and (r.id, timeslot_id) not in room_schedule]
                
                if available_rooms:
                    # Elegir aula con capacidad más cercana
                    available_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
                    new_room = available_rooms[0]
                    self.genes[class_id] = (new_room.id, timeslot_id)
                    room_schedule[(new_room.id, timeslot_id)].append(class_id)
                else:
                    # Si no hay aulas disponibles, intentar cambiar el timeslot
                    available_slots = self.time_slots.get(class_id, [])
                    if available_slots and len(available_slots) > 1:
                        # Buscar timeslot alternativo
                        for alt_slot in available_slots:
                            if alt_slot.id != timeslot_id:
                                suitable_rooms = [r for r in self.rooms 
                                                if validator.room_capacities.get(r.id, 0) >= class_obj.class_limit]
                                if suitable_rooms:
                                    suitable_rooms.sort(key=lambda r: abs(r.capacity - class_obj.class_limit))
                                    self.genes[class_id] = (suitable_rooms[0].id, alt_slot.id)
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
        self.stagnation_threshold = 30  # Reducido de 50 a 30 generaciones
        
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
        
        # Estrategia 4: Reparar el mejor individuo
        print(f"   • Reparando mejor individuo...")
        if self.best_individual:
            best_clone = self.best_individual.clone()
            best_clone.repair(validator)
            best_clone.calculate_fitness(validator)
            
            # Si mejoró, reemplazar al peor de la elite
            if best_clone.fitness > self.best_individual.fitness:
                self.population[self.elitism_size - 1] = best_clone
                print(f"     [OK] Reparación exitosa: {self.best_individual.fitness:.0f} → {best_clone.fitness:.0f}")
            else:
                print(f"     [WARNING] Reparación sin mejora significativa")
        
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
                
                # Reparación habilitada (10% de probabilidad)
                if random.random() < 0.1:
                    child1.repair(validator)
                if random.random() < 0.1:
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
            
            # Early stopping basado en BASE_FITNESS
            # Calcular BASE_FITNESS actual
            num_classes = len(self.population[0].genes) if self.population else 0
            BASE_FITNESS = num_classes * 500.0
            BASE_FITNESS = max(50000.0, min(300000.0, BASE_FITNESS))
            target_fitness = BASE_FITNESS * 0.90  # 90% del BASE
            
            if self.best_fitness_history[-1] >= target_fitness:
                print(f"\n[GOAL] ¡Fitness excelente alcanzado! ({self.best_fitness_history[-1]:.0f})")
                print(f"   Deteniendo en generación {generation + 1}/{self.generations}")
                sys.stdout.flush()
                break
        
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
