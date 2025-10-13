
import random
import numpy as np
from typing import List, Tuple, Dict, Set
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
        
        # Obtener instructores por clase
        from .models import ClassInstructor
        class_instructors_map = {}
        for class_obj in self.classes:
            instructors = ClassInstructor.objects.filter(
                class_obj=class_obj
            ).values_list('instructor_id', flat=True)
            class_instructors_map[class_obj.id] = list(instructors)
        
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
            
            # Intentar encontrar asignación sin conflictos (máximo 10 intentos)
            assigned = False
            for attempt in range(10):
                room = suitable_rooms[min(attempt, len(suitable_rooms)-1)] if suitable_rooms else None
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
                
                # Si no hay conflictos, asignar
                if not has_room_conflict and not has_instructor_conflict:
                    self.genes[class_obj.id] = (room.id, time_slot.id)
                    room_occupation[room_key] = {class_obj.id}
                    for instructor_id in instructors:
                        instructor_occupation[(instructor_id, time_slot.id)] = {class_obj.id}
                    assigned = True
                    break
            
            # Si no se pudo asignar sin conflictos, asignar de todas formas
            if not assigned:
                room = suitable_rooms[0] if suitable_rooms else None
                time_slot = random.choice(available_slots) if available_slots else None
                self.genes[class_obj.id] = (room.id if room else None, time_slot.id if time_slot else None)
    
    def calculate_fitness(self, validator: 'ConstraintValidator'):
        self.fitness = validator.evaluate(self)
        return self.fitness
    
    def clone(self):
        """Crea una copia del individuo"""
        new_individual = Individual(self.classes, self.rooms, self.time_slots)
        new_individual.genes = self.genes.copy()
        new_individual.fitness = self.fitness
        return new_individual


class GeneticAlgorithm:
    """
    Implementación del Algoritmo Genético para generación de horarios.
    """
    
    def __init__(self, 
                 population_size: int = 100,
                 generations: int = 200,
                 mutation_rate: float = 0.15,
                 crossover_rate: float = 0.80,
                 elitism_size: int = 10,
                 tournament_size: int = 5):
        """
        population_size: Tamaño de la población
        generations: Número de generaciones
        mutation_rate: Probabilidad de mutación (0-1) - Reducida para estabilidad
        crossover_rate: Probabilidad de cruce (0-1) - Reducida para estabilidad
        elitism_size: Número de mejores individuos que pasan directamente
        tournament_size: Tamaño del torneo para selección - Reducido para diversidad
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_size = elitism_size
        self.tournament_size = tournament_size
        
        self.population: List[Individual] = []
        self.best_individual: Individual = None
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
    
    def initialize_population(self, classes: List[Class], rooms: List[Room], 
                            time_slots: Dict[int, List[TimeSlot]]):
        """Crea la población inicial con individuos aleatorios"""
        self.population = []
        for _ in range(self.population_size):
            individual = Individual(classes, rooms, time_slots)
            individual.initialize_random()
            self.population.append(individual)
    
    def evaluate_population(self, validator: 'ConstraintValidator'):
        """Evalúa el fitness de toda la población"""
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
        """
        for class_id in individual.genes:
            if random.random() < self.mutation_rate:
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
    
    def evolve(self, validator: 'ConstraintValidator') -> Individual:
        """
        Ejecuta el proceso evolutivo completo.
        Retorna el mejor individuo encontrado.
        """
        # Evaluar población inicial
        self.evaluate_population(validator)
        
        for generation in range(self.generations):
            new_population = []
            
            # Elitismo: mantener los mejores individuos
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
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            self.population = new_population
            self.evaluate_population(validator)
            
            # Log de progreso (cada 2 generaciones)
            if (generation + 1) % 2 == 0:
                print(f"Generación {generation + 1}/{self.generations} - "
                      f"Mejor Fitness: {self.best_fitness_history[-1]:.2f} - "
                      f"Fitness Promedio: {self.avg_fitness_history[-1]:.2f}")
        
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
