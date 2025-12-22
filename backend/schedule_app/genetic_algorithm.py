
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
        """Inicialización simple y rápida - estilo greedy optimizado"""
        # Cachear instructores una sola vez
        from .models import ClassInstructor
        class_instructors_map = {}
        class_ids = [c.id for c in self.classes]
        all_class_instructors = ClassInstructor.objects.filter(
            class_obj_id__in=class_ids
        ).values_list('class_obj_id', 'instructor_id')
        
        for class_id, instructor_id in all_class_instructors:
            if class_id not in class_instructors_map:
                class_instructors_map[class_id] = []
            class_instructors_map[class_id].append(instructor_id)
        
        # Ordenar clases por tamaño (greedy: asignar grandes primero)
        sorted_classes = sorted(self.classes, key=lambda c: c.class_limit, reverse=True)
        
        # Pre-clasificar aulas por capacidad
        rooms_by_capacity = sorted(self.rooms, key=lambda r: r.capacity)
        
        for class_obj in sorted_classes:
            # Filtrar aulas por capacidad (heurística)
            # Asignación simple y rápida
            available_slots = self.time_slots.get(class_obj.id, [])
            if not available_slots:
                # Buscar aula mínima que cumpla capacidad
                suitable_room = next((r for r in rooms_by_capacity if r.capacity >= class_obj.class_limit), 
                                    rooms_by_capacity[0] if rooms_by_capacity else None)
                self.genes[class_obj.id] = (suitable_room.id if suitable_room else None, None)
                continue
            
            # Seleccionar aula adecuada (greedy: primera que cumple capacidad)
            suitable_room = next((r for r in rooms_by_capacity if r.capacity >= class_obj.class_limit),
                                rooms_by_capacity[0] if rooms_by_capacity else None)
            
            # Seleccionar slot aleatorio
            selected_slot = random.choice(available_slots)
            
            # Asignar directamente (sin verificaciones pesadas en inicialización)
            self.genes[class_obj.id] = (suitable_room.id if suitable_room else None, selected_slot.id)
    
    def calculate_fitness(self, validator: 'ConstraintValidator'):
        self.fitness = validator.evaluate(self)
        return self.fitness
    
    def clone(self):
        """Crea una copia del individuo"""
        new_individual = Individual(self.classes, self.rooms, self.time_slots)
        new_individual.genes = self.genes.copy()
        new_individual.fitness = self.fitness
        return new_individual
    
    def repair(self, validator: 'ConstraintValidator', max_iterations=1):
        """
        Reparación simplificada - solo corrige violaciones críticas de capacidad.
        """
        # Solo reparar violaciones de capacidad (lo más importante)
        for class_id, (room_id, timeslot_id) in list(self.genes.items()):
            if room_id and timeslot_id:
                class_obj = next((c for c in self.classes if c.id == class_id), None)
                if class_obj:
                    room_capacity = validator.room_capacities.get(room_id, float('inf'))
                    if room_capacity < class_obj.class_limit:
                        # Buscar primera aula con capacidad suficiente
                        for r in self.rooms:
                            if validator.room_capacities.get(r.id, 0) >= class_obj.class_limit:
                                self.genes[class_id] = (r.id, timeslot_id)
                                break


class GeneticAlgorithm:
    """
    Implementación del Algoritmo Genético para generación de horarios.
    """
    
    def __init__(self, 
                 population_size: int = 50,  # Reducido para velocidad
                 generations: int = 100,  # Reducido para velocidad
                 mutation_rate: float = 0.15,  # Simplificado
                 crossover_rate: float = 0.70,  # Reducido
                 elitism_size: int = 5,  # Reducido
                 tournament_size: int = 3):
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
        self.initial_mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_size = elitism_size
        self.tournament_size = tournament_size
        
        self.population: List[Individual] = []
        self.best_individual: Individual = None
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        
        # Control de estancamiento simplificado
        self.stagnation_counter = 0
        self.last_best_fitness = float('-inf')
        self.stagnation_threshold = 30  # Más rápido
    
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
        Operador de mutación simple y rápido.
        Cambia aleatoriamente aula o tiempo.
        """
        for class_id in individual.genes:
            if random.random() < self.mutation_rate:
                current_room_id, current_time_id = individual.genes[class_id]
                
                # 50% mutar aula, 50% mutar tiempo
                if random.random() < 0.5:
                    # Mutar aula
                    new_room = random.choice(individual.rooms)
                    individual.genes[class_id] = (new_room.id, current_time_id)
                else:
                    # Mutar tiempo
                    available_slots = individual.time_slots.get(class_id, [])
                    if available_slots:
                        new_slot = random.choice(available_slots)
                        individual.genes[class_id] = (current_room_id, new_slot.id)
    
    def _apply_diversity_boost(self, validator: 'ConstraintValidator'):
        """
        Estrategia simple de diversidad: inyectar nuevos individuos aleatorios.
        """
        import sys
        print(f"\n[BOOST] Inyectando diversidad...")
        sys.stdout.flush()
        
        # Reemplazar 30% de la población (excepto elite)
        num_to_replace = int(self.population_size * 0.3)
        elite_size = self.elitism_size
        
        # Generar nuevos individuos
        for i in range(elite_size, min(elite_size + num_to_replace, self.population_size)):
            new_individual = Individual(
                self.population[0].classes,
                self.population[0].rooms,
                self.population[0].time_slots
            )
            new_individual.initialize_random()
            self.population[i] = new_individual
        
        # Re-evaluar
        self.evaluate_population(validator)
        print(f"[OK] Diversidad restaurada")
        sys.stdout.flush()
    
    def evolve(self, validator: 'ConstraintValidator', on_generation=None) -> Individual:
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
        
        if on_generation:
            on_generation(0, self.best_fitness_history[0])
        
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
                
                # Reparación solo cada 5 generaciones (reducir carga)
                if generation % 5 == 0:
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
            
            # Log de progreso (cada 5 generaciones)
            if (generation + 1) % 5 == 0:
                elapsed = time.time() - start_time
                avg_time_per_gen = elapsed / (generation + 1)
                remaining_time = avg_time_per_gen * (self.generations - generation - 1)
                
                # Mostrar indicador de estancamiento
                stagnation_indicator = ""
                if self.stagnation_counter > 20:
                    stagnation_indicator = " [WARNING]"
                
                print(f"Gen {generation + 1}/{self.generations} | "
                      f"Mejor: {self.best_fitness_history[-1]:.0f} | "
                      f"Promedio: {self.avg_fitness_history[-1]:.0f} | "
                      f"Tiempo: {elapsed:.0f}s | ETA: {remaining_time:.0f}s{stagnation_indicator}")
                sys.stdout.flush()
                
                if on_generation:
                    on_generation(generation + 1, self.best_fitness_history[-1])
        
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