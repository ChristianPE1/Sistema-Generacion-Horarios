"""
Algoritmo Genético Optimizado para Generación de Horarios.

Este módulo genera horarios SIN depender de timeslots predefinidos.
El AG encuentra la configuración óptima de días y horas para cada clase.

Reglas:
- Bloques de 50 minutos
- Máximo 3 bloques consecutivos del mismo curso
- 10 min de descanso entre cursos diferentes
- Laboratorios no cuentan como consecutivos de teoría
- Sin conflictos de sala, profesor o año de estudiantes
"""
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import time
import json


@dataclass
class Room:
    id: str
    capacity: int
    room_type: str  # 'aula' o 'laboratorio'


@dataclass
class Instructor:
    id: str
    name: str
    status: str  # 'assigned' o 'pending'


@dataclass
class ClassInfo:
    id: str
    name: str
    code: str
    students: int
    instructor_id: str
    class_type: str  # 'teoria', 'practica', 'laboratorio'
    hours: int
    year: int


@dataclass
class Config:
    days: List[str]
    block_duration: int  # minutos
    break_duration: int  # minutos
    start_time: str
    end_time: str
    max_consecutive: int


@dataclass
class TimeSlot:
    day: str
    block: int  # índice del bloque (0-based)
    start_time: str
    end_time: str


@dataclass
class Assignment:
    class_id: str
    class_name: str
    room_id: str
    instructor_id: str
    timeslots: List[TimeSlot]
    class_type: str
    year: int


class GeneticScheduler:
    """Algoritmo Genético para generación de horarios."""
    
    def __init__(self, rooms: List[Room], instructors: List[Instructor], 
                 classes: List[ClassInfo], config: Config):
        self.rooms = rooms
        self.instructors = instructors
        self.classes = classes
        self.config = config
        
        # Crear mapa de instructores
        self.instructor_map = {i.id: i for i in instructors}
        
        # Calcular bloques disponibles por día
        self.blocks_per_day = self._calculate_blocks_per_day()
        self.all_timeslots = self._generate_all_timeslots()
        
        # Separar aulas y laboratorios
        self.aulas = [r for r in rooms if r.room_type == 'aula']
        self.labs = [r for r in rooms if r.room_type == 'laboratorio']
    
    def _calculate_blocks_per_day(self) -> int:
        """Calcula cuántos bloques de 50 min caben en un día."""
        start_h, start_m = map(int, self.config.start_time.split(':'))
        end_h, end_m = map(int, self.config.end_time.split(':'))
        
        total_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
        block_with_break = self.config.block_duration + self.config.break_duration
        
        return total_minutes // block_with_break
    
    def _generate_all_timeslots(self) -> List[TimeSlot]:
        """Genera todos los timeslots posibles."""
        slots = []
        start_h, start_m = map(int, self.config.start_time.split(':'))
        
        for day in self.config.days:
            for block_idx in range(self.blocks_per_day):
                block_start = start_h * 60 + start_m + block_idx * (self.config.block_duration + self.config.break_duration)
                block_end = block_start + self.config.block_duration
                
                start_str = f"{block_start // 60:02d}:{block_start % 60:02d}"
                end_str = f"{block_end // 60:02d}:{block_end % 60:02d}"
                
                slots.append(TimeSlot(day=day, block=block_idx, start_time=start_str, end_time=end_str))
        
        return slots
    
    def _create_individual(self) -> List[Assignment]:
        """Crea un individuo (horario completo) aleatorio."""
        assignments = []
        
        for cls in self.classes:
            # Calcular bloques necesarios
            blocks_needed = max(1, (cls.hours * 60) // self.config.block_duration)
            
            # Seleccionar sala apropiada
            if cls.class_type == 'laboratorio' and self.labs:
                valid_rooms = [r for r in self.labs if r.capacity >= cls.students]
            else:
                valid_rooms = [r for r in self.aulas if r.capacity >= cls.students]
            
            if not valid_rooms:
                valid_rooms = [r for r in self.rooms if r.capacity >= cls.students]
            if not valid_rooms:
                valid_rooms = self.rooms  # Último recurso
            
            room = random.choice(valid_rooms)
            
            # Distribuir bloques (intentar consecutivos, máx 3)
            timeslots = self._assign_timeslots(blocks_needed)
            
            assignments.append(Assignment(
                class_id=cls.id,
                class_name=cls.name,
                room_id=room.id,
                instructor_id=cls.instructor_id,
                timeslots=timeslots,
                class_type=cls.class_type,
                year=cls.year
            ))
        
        return assignments
    
    def _assign_timeslots(self, blocks_needed: int) -> List[TimeSlot]:
        """Asigna timeslots para una clase, respetando max_consecutive."""
        timeslots = []
        blocks_remaining = blocks_needed
        max_consec = self.config.max_consecutive
        
        # Elegir días aleatorios
        available_days = list(self.config.days)
        
        while blocks_remaining > 0 and available_days:
            day = random.choice(available_days)
            
            # Cuántos bloques poner este día
            blocks_this_day = min(blocks_remaining, max_consec)
            
            # Elegir bloque de inicio
            max_start = self.blocks_per_day - blocks_this_day
            if max_start < 0:
                blocks_this_day = self.blocks_per_day
                max_start = 0
            
            start_block = random.randint(0, max_start)
            
            # Agregar timeslots
            for i in range(blocks_this_day):
                block_idx = start_block + i
                # Encontrar timeslot correspondiente
                for slot in self.all_timeslots:
                    if slot.day == day and slot.block == block_idx:
                        timeslots.append(slot)
                        break
            
            blocks_remaining -= blocks_this_day
            # Evitar poner más en el mismo día
            if blocks_remaining > 0:
                available_days = [d for d in available_days if d != day]
                if not available_days:
                    available_days = list(self.config.days)
        
        return timeslots
    
    def _calculate_fitness(self, individual: List[Assignment]) -> Tuple[float, int]:
        """
        Calcula el fitness de un horario.
        
        Retorna (fitness_score, conflict_count)
        Mayor fitness = mejor horario
        """
        conflicts = 0
        score = 1000.0  # Base score
        
        # Crear estructuras para detección de conflictos
        # Key: (day, block) -> Value: {room_id: assignment, instructor_id: assignment, year: [assignments]}
        room_schedule = {}  # (day, block, room_id) -> assignment
        instructor_schedule = {}  # (day, block, instructor_id) -> assignment
        year_schedule = {}  # (day, block, year) -> [assignments]
        
        for assignment in individual:
            for slot in assignment.timeslots:
                key_day_block = (slot.day, slot.block)
                
                # Conflicto de sala
                room_key = (slot.day, slot.block, assignment.room_id)
                if room_key in room_schedule:
                    conflicts += 1
                    score -= 100
                else:
                    room_schedule[room_key] = assignment
                
                # Conflicto de instructor
                if assignment.instructor_id != '0':  # Si no es "por contratar"
                    inst_key = (slot.day, slot.block, assignment.instructor_id)
                    if inst_key in instructor_schedule:
                        conflicts += 1
                        score -= 100
                    else:
                        instructor_schedule[inst_key] = assignment
                
                # Conflicto de año (estudiantes)
                year_key = (slot.day, slot.block, assignment.year)
                if year_key not in year_schedule:
                    year_schedule[year_key] = []
                
                # Verificar si ya hay otra clase del mismo año
                same_year = year_schedule[year_key]
                if same_year:
                    # Solo es conflicto si son clases diferentes del mismo año
                    for other in same_year:
                        if other.class_id != assignment.class_id:
                            conflicts += 1
                            score -= 50
                
                year_schedule[year_key].append(assignment)
        
        # Bonus por distribución balanceada
        days_used = {}
        for assignment in individual:
            for slot in assignment.timeslots:
                days_used[slot.day] = days_used.get(slot.day, 0) + 1
        
        if days_used:
            avg_per_day = sum(days_used.values()) / len(self.config.days)
            variance = sum((v - avg_per_day) ** 2 for v in days_used.values())
            if variance < 10:
                score += 50  # Bonus por buena distribución
        
        # Bonus por respetar max_consecutive
        for assignment in individual:
            if self._check_consecutive_ok(assignment):
                score += 5
            else:
                conflicts += 1
                score -= 30
        
        return (max(0, score), conflicts)
    
    def _check_consecutive_ok(self, assignment: Assignment) -> bool:
        """Verifica que no haya más de max_consecutive bloques seguidos."""
        if not assignment.timeslots:
            return True
        
        # Laboratorios pueden tener más consecutivos
        if assignment.class_type == 'laboratorio':
            return True
        
        # Agrupar por día
        by_day = {}
        for slot in assignment.timeslots:
            if slot.day not in by_day:
                by_day[slot.day] = []
            by_day[slot.day].append(slot.block)
        
        # Verificar consecutivos
        for day, blocks in by_day.items():
            blocks_sorted = sorted(blocks)
            consecutive = 1
            for i in range(1, len(blocks_sorted)):
                if blocks_sorted[i] == blocks_sorted[i-1] + 1:
                    consecutive += 1
                    if consecutive > self.config.max_consecutive:
                        return False
                else:
                    consecutive = 1
        
        return True
    
    def _crossover(self, parent1: List[Assignment], parent2: List[Assignment]) -> List[Assignment]:
        """Cruce de dos padres para crear un hijo."""
        child = []
        for i in range(len(parent1)):
            # 50% de cada padre
            if random.random() < 0.5:
                child.append(Assignment(
                    class_id=parent1[i].class_id,
                    class_name=parent1[i].class_name,
                    room_id=parent1[i].room_id,
                    instructor_id=parent1[i].instructor_id,
                    timeslots=parent1[i].timeslots[:],
                    class_type=parent1[i].class_type,
                    year=parent1[i].year
                ))
            else:
                child.append(Assignment(
                    class_id=parent2[i].class_id,
                    class_name=parent2[i].class_name,
                    room_id=parent2[i].room_id,
                    instructor_id=parent2[i].instructor_id,
                    timeslots=parent2[i].timeslots[:],
                    class_type=parent2[i].class_type,
                    year=parent2[i].year
                ))
        return child
    
    def _mutate(self, individual: List[Assignment], mutation_rate: float) -> List[Assignment]:
        """Aplica mutación a un individuo."""
        for i, assignment in enumerate(individual):
            if random.random() < mutation_rate:
                # Tipo de mutación
                mutation_type = random.choice(['room', 'timeslot', 'both'])
                
                cls = next((c for c in self.classes if c.id == assignment.class_id), None)
                if not cls:
                    continue
                
                if mutation_type in ['room', 'both']:
                    # Cambiar sala
                    if assignment.class_type == 'laboratorio' and self.labs:
                        valid_rooms = [r for r in self.labs if r.capacity >= cls.students]
                    else:
                        valid_rooms = [r for r in self.aulas if r.capacity >= cls.students]
                    
                    if valid_rooms:
                        individual[i].room_id = random.choice(valid_rooms).id
                
                if mutation_type in ['timeslot', 'both']:
                    # Cambiar timeslots
                    blocks_needed = len(assignment.timeslots)
                    if blocks_needed > 0:
                        individual[i].timeslots = self._assign_timeslots(blocks_needed)
        
        return individual
    
    def generate(self, population_size: int = 50, generations: int = 100,
                 mutation_rate: float = 0.1, crossover_rate: float = 0.8) -> Dict:
        """
        Ejecuta el algoritmo genético.
        
        Returns:
            Dict con el mejor horario encontrado y estadísticas
        """
        start_time = time.time()
        
        # Crear población inicial
        population = [self._create_individual() for _ in range(population_size)]
        
        # Evaluar población inicial
        evaluated = [(ind, self._calculate_fitness(ind)) for ind in population]
        evaluated.sort(key=lambda x: x[1][0], reverse=True)
        
        best_ever = evaluated[0]
        
        # Evolución
        for gen in range(generations):
            # Selección (tournament selection)
            new_population = []
            
            # Elitismo: mantener los 2 mejores
            new_population.append(evaluated[0][0])
            if len(evaluated) > 1:
                new_population.append(evaluated[1][0])
            
            while len(new_population) < population_size:
                # Tournament selection
                tournament_size = min(5, len(evaluated))
                tournament = random.sample(evaluated, tournament_size)
                parent1 = max(tournament, key=lambda x: x[1][0])[0]
                
                tournament = random.sample(evaluated, tournament_size)
                parent2 = max(tournament, key=lambda x: x[1][0])[0]
                
                # Crossover
                if random.random() < crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = [Assignment(
                        class_id=a.class_id,
                        class_name=a.class_name,
                        room_id=a.room_id,
                        instructor_id=a.instructor_id,
                        timeslots=a.timeslots[:],
                        class_type=a.class_type,
                        year=a.year
                    ) for a in parent1]
                
                # Mutación
                child = self._mutate(child, mutation_rate)
                new_population.append(child)
            
            # Evaluar nueva población
            population = new_population
            evaluated = [(ind, self._calculate_fitness(ind)) for ind in population]
            evaluated.sort(key=lambda x: x[1][0], reverse=True)
            
            # Actualizar mejor global
            if evaluated[0][1][0] > best_ever[1][0]:
                best_ever = evaluated[0]
            
            # Early stopping si encontramos solución perfecta
            if best_ever[1][1] == 0:  # Sin conflictos
                break
        
        elapsed_time = time.time() - start_time
        
        # Convertir mejor solución a formato de salida
        best_schedule, (fitness, conflicts) = best_ever
        
        return {
            'assignments': [self._assignment_to_dict(a) for a in best_schedule],
            'fitness_score': fitness,
            'conflict_count': conflicts,
            'generation_time_ms': int(elapsed_time * 1000),
            'generations_run': gen + 1,
            'classes_assigned': len(best_schedule)
        }
    
    def _assignment_to_dict(self, assignment: Assignment) -> Dict:
        """Convierte una asignación a diccionario."""
        instructor = self.instructor_map.get(assignment.instructor_id)
        room = next((r for r in self.rooms if r.id == assignment.room_id), None)
        
        return {
            'class_id': assignment.class_id,
            'class_name': assignment.class_name,
            'class_type': assignment.class_type,
            'year': assignment.year,
            'room': {
                'id': assignment.room_id,
                'type': room.room_type if room else 'aula'
            },
            'instructor': {
                'id': assignment.instructor_id,
                'name': instructor.name if instructor else 'Por Contratar'
            },
            'schedule': [
                {
                    'day': slot.day,
                    'block': slot.block,
                    'start': slot.start_time,
                    'end': slot.end_time
                }
                for slot in assignment.timeslots
            ]
        }


def load_from_xml(xml_path: str) -> Tuple[List[Room], List[Instructor], List[ClassInfo], Config]:
    """Carga datos desde XML limpio."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Rooms
    rooms = []
    for room_elem in root.findall('.//room'):
        rooms.append(Room(
            id=room_elem.get('id'),
            capacity=int(room_elem.get('capacity', 30)),
            room_type=room_elem.get('type', 'aula')
        ))
    
    # Instructors
    instructors = []
    for inst_elem in root.findall('.//instructor'):
        instructors.append(Instructor(
            id=inst_elem.get('id'),
            name=inst_elem.get('name', f'Instructor_{inst_elem.get("id")}'),
            status=inst_elem.get('status', 'assigned')
        ))
    
    # Classes
    classes = []
    for cls_elem in root.findall('.//class'):
        classes.append(ClassInfo(
            id=cls_elem.get('id'),
            name=cls_elem.get('name', f'Class_{cls_elem.get("id")}'),
            code=cls_elem.get('code', cls_elem.get('id')),
            students=int(cls_elem.get('students', 30)),
            instructor_id=cls_elem.get('instructor', '0'),
            class_type=cls_elem.get('type', 'teoria'),
            hours=int(cls_elem.get('hours', 2)),
            year=int(cls_elem.get('year', 1))
        ))
    
    # Config
    config_elem = root.find('.//config')
    if config_elem is not None:
        config = Config(
            days=config_elem.get('days', 'lunes,martes,miercoles,jueves,viernes').split(','),
            block_duration=int(config_elem.get('block_duration', 50)),
            break_duration=int(config_elem.get('break_duration', 10)),
            start_time=config_elem.get('start_time', '07:00'),
            end_time=config_elem.get('end_time', '20:00'),
            max_consecutive=int(config_elem.get('max_consecutive', 3))
        )
    else:
        config = Config(
            days=['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
            block_duration=50,
            break_duration=10,
            start_time='07:00',
            end_time='20:00',
            max_consecutive=3
        )
    
    return rooms, instructors, classes, config


def generate_from_xml(xml_path: str, population_size: int = 50, 
                      generations: int = 100) -> Dict:
    """Genera horario desde archivo XML."""
    rooms, instructors, classes, config = load_from_xml(xml_path)
    
    scheduler = GeneticScheduler(rooms, instructors, classes, config)
    return scheduler.generate(
        population_size=population_size,
        generations=generations
    )


if __name__ == '__main__':
    import sys
    import os
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Probar con escuela.xml si existe
    test_file = os.path.join(base_dir, 'escuela.xml')
    if not os.path.exists(test_file):
        test_file = os.path.join(base_dir, 'purdue_clean.xml')
    
    if os.path.exists(test_file):
        print(f"Generando horario desde: {test_file}")
        result = generate_from_xml(test_file, population_size=50, generations=100)
        
        print(f"\nResultado:")
        print(f"  - Fitness: {result['fitness_score']}")
        print(f"  - Conflictos: {result['conflict_count']}")
        print(f"  - Tiempo: {result['generation_time_ms']} ms")
        print(f"  - Clases asignadas: {result['classes_assigned']}")
        
        # Guardar resultado
        output_file = os.path.join(base_dir, 'horario_generado.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nHorario guardado en: {output_file}")
    else:
        print("No se encontró archivo XML para probar")
