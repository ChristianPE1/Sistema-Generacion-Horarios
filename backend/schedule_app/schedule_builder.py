import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import time
import json
import random


@dataclass
class Room:
    id: str
    capacity: int
    room_type: str


@dataclass
class Instructor:
    id: str
    name: str
    status: str


@dataclass
class ClassInfo:
    id: str
    name: str
    code: str
    students: int
    instructor_id: str
    class_type: str
    hours: int
    year: int


@dataclass
class Config:
    days: List[str]
    block_duration: int
    break_duration: int
    start_time: str
    end_time: str
    max_consecutive: int


@dataclass
class TimeSlot:
    day: str
    block: int
    
    def __hash__(self):
        return hash((self.day, self.block))
    
    def __eq__(self, other):
        return self.day == other.day and self.block == other.block


@dataclass
class Assignment:
    class_info: ClassInfo
    room: Room
    timeslots: List[TimeSlot] = field(default_factory=list)


class ScheduleBuilder:
    # Generador de horarios usando enfoque constructivo.
    
    def __init__(self, rooms: List[Room], instructors: List[Instructor], classes: List[ClassInfo], config: Config, constraints: dict = None):
        self.rooms = rooms
        self.instructors = instructors
        self.classes = classes
        self.config = config
        self.constraints = constraints or {}
        
        self.instructor_map = {i.id: i for i in instructors}
        
        # Aplicar restricciones específicas si existen
        aula_constraints = self.constraints.get('aulas', {})
        lab_constraints = self.constraints.get('laboratorios', {})
        
        # Calcular bloques por día basado en el rango más amplio posible
        # Esto asegura que tengamos suficientes bloques para el tipo de aula que más necesita
        aula_start = aula_constraints.get('start_time', self.config.start_time)
        aula_end = aula_constraints.get('end_time', self.config.end_time)
        lab_start = lab_constraints.get('start_time', self.config.start_time)  
        lab_end = lab_constraints.get('end_time', self.config.end_time)
        
        # Calcular rangos para determinar el máximo
        aula_start_h, aula_start_m = map(int, aula_start.split(':'))
        aula_end_h, aula_end_m = map(int, aula_end.split(':'))
        lab_start_h, lab_start_m = map(int, lab_start.split(':'))
        lab_end_h, lab_end_m = map(int, lab_end.split(':'))
        
        # Usar el rango más temprano de inicio y más tarde de fin
        global_start_h = min(aula_start_h, lab_start_h)
        global_start_m = min(aula_start_m, lab_start_m) if aula_start_h == lab_start_h else (aula_start_m if aula_start_h < lab_start_h else lab_start_m)
        global_end_h = max(aula_end_h, lab_end_h)
        global_end_m = max(aula_end_m, lab_end_m) if aula_end_h == lab_end_h else (aula_end_m if aula_end_h > lab_end_h else lab_end_m)
        
        # Actualizar config para usar el rango global
        self.config.start_time = f"{global_start_h:02d}:{global_start_m:02d}"
        self.config.end_time = f"{global_end_h:02d}:{global_end_m:02d}"
        
        # Calcular bloques totales
        total_minutes = (global_end_h * 60 + global_end_m) - (global_start_h * 60 + global_start_m)
        self.blocks_per_day = total_minutes // (config.block_duration + config.break_duration)
        
        # Calcular offsets para cada tipo de aula (bloques desde el inicio global)
        block_duration_total = config.block_duration + config.break_duration
        self.aula_start_offset = ((aula_start_h * 60 + aula_start_m) - (global_start_h * 60 + global_start_m)) // block_duration_total
        self.aula_end_offset = self.aula_start_offset + (((aula_end_h * 60 + aula_end_m) - (aula_start_h * 60 + aula_start_m)) // block_duration_total)
        
        self.lab_start_offset = ((lab_start_h * 60 + lab_start_m) - (global_start_h * 60 + global_start_m)) // block_duration_total
        self.lab_end_offset = self.lab_start_offset + (((lab_end_h * 60 + lab_end_m) - (lab_start_h * 60 + lab_start_m)) // block_duration_total)
        
        # Estado de ocupación
        self.room_occupied: Dict[Tuple[str, str, int], str] = {}  # (room_id, day, block) -> class_id
        self.instructor_occupied: Dict[Tuple[str, str, int], str] = {}  # (inst_id, day, block) -> class_id
        
        # Track de clases asignadas por código para verificar consecutivos
        # Formato: (code, day, block) -> class_type ('teoria', 'practica', 'laboratorio')
        self.code_slots: Dict[Tuple[str, str, int], str] = {}
        
        # Contador de uso de aulas para equilibrar
        self.room_usage: Dict[str, int] = {r.id: 0 for r in rooms}
    
    def _count_consecutive_theory_practice(self, code: str, day: str, block: int) -> int:
        # Cuenta cuántos bloques consecutivos de teoría/práctica del mismo código hay alrededor de un bloque dado. Laboratorio NO cuenta.
        count = 0
        
        # Contar hacia atrás
        for b in range(block - 1, -1, -1):
            key = (code, day, b)
            if key in self.code_slots:
                class_type = self.code_slots[key]
                if class_type != 'laboratorio':
                    count += 1
                else:
                    break  # Laboratorio rompe la secuencia
            else:
                break
        
        # Contar hacia adelante
        for b in range(block + 1, self.blocks_per_day):
            key = (code, day, b)
            if key in self.code_slots:
                class_type = self.code_slots[key]
                if class_type != 'laboratorio':
                    count += 1
                else:
                    break
            else:
                break
        
        return count
    
    def _get_blocks_needed(self, class_info: ClassInfo) -> int:
        # Calcula bloques de 50 min necesarios para las horas.
        return max(1, (class_info.hours * 60) // self.config.block_duration)
    
    def _get_valid_rooms(self, class_info: ClassInfo) -> List[Room]:
        # Obtiene salas válidas para una clase, ordenadas por:
        # 1. Mínima diferencia entre capacidad y estudiantes (mejor ajuste)
        # 2. Menor uso actual (equilibrar carga entre aulas)
        
        if class_info.class_type == 'laboratorio' and any(r.room_type == 'laboratorio' for r in self.rooms):
            rooms = [r for r in self.rooms if r.room_type == 'laboratorio' and r.capacity >= class_info.students]
            if not rooms:
                rooms = [r for r in self.rooms if r.room_type == 'aula' and r.capacity >= class_info.students]
        else:
            rooms = [r for r in self.rooms if r.room_type == 'aula' and r.capacity >= class_info.students]
        
        if not rooms:
            rooms = self.rooms[:]
        
        # Ordenar por: 1) Menor diferencia capacidad-estudiantes, 2) Menor uso
        rooms = sorted(rooms, key=lambda r: (
            r.capacity - class_info.students,  # Mejor ajuste primero
            self.room_usage.get(r.id, 0)  # Menos usado primero
        ))
        
        return rooms
    
    def _is_slot_free(self, room: Room, day: str, block: int, instructor_id: str, class_info: ClassInfo = None) -> bool:
        # Verifica si un slot está libre para asignar.
        
        # Verificar que el bloque esté dentro del rango válido para el tipo de aula
        if room.room_type == 'laboratorio':
            if block < self.lab_start_offset or block >= self.lab_end_offset:
                return False
        else:  # aulas
            if block < self.aula_start_offset or block >= self.aula_end_offset:
                return False
        
        # Verificar sala
        if (room.id, day, block) in self.room_occupied:
            return False
        
        # Verificar instructor (si tiene uno asignado)
        if instructor_id != '0':
            if (instructor_id, day, block) in self.instructor_occupied:
                return False
        
        # Verificar límite de consecutivos para teoría/práctica
        if class_info and class_info.class_type != 'laboratorio':
            consecutive = self._count_consecutive_theory_practice(class_info.code, day, block)
            # Si ya hay max_consecutive bloques, no podemos agregar más
            if consecutive >= self.config.max_consecutive:
                return False
        
        return True
    
    def _find_consecutive_slots(self, room: Room, day: str, start_block: int, count: int, instructor_id: str, class_info: ClassInfo = None) -> List[TimeSlot]:
        # Busca slots consecutivos libres.
        if start_block + count > self.blocks_per_day:
            return []
        
        slots = []
        for i in range(count):
            block = start_block + i
            if not self._is_slot_free(room, day, block, instructor_id, class_info):
                return []
            slots.append(TimeSlot(day=day, block=block))
        
        return slots
    
    def _assign_slots(self, class_info: ClassInfo, room: Room, slots: List[TimeSlot]) -> None:
        # Marca slots como ocupados.
        for slot in slots:
            self.room_occupied[(room.id, slot.day, slot.block)] = class_info.id
            
            if class_info.instructor_id != '0':
                self.instructor_occupied[(class_info.instructor_id, slot.day, slot.block)] = class_info.id
            
            # Registrar slot por código para tracking de consecutivos
            self.code_slots[(class_info.code, slot.day, slot.block)] = class_info.class_type
        
        # Incrementar contador de uso del aula
        self.room_usage[room.id] = self.room_usage.get(room.id, 0) + len(slots)
    
    def _try_assign_class(self, class_info: ClassInfo) -> Optional[Assignment]:
        # Intenta asignar una clase al mejor slot disponible.
        blocks_needed = self._get_blocks_needed(class_info)
        valid_rooms = self._get_valid_rooms(class_info)
        max_consec = self.config.max_consecutive
        
        # Determinar rangos válidos según tipo de aula
        if class_info.class_type == 'laboratorio':
            max_consec = 4
            start_offset = self.lab_start_offset
            end_offset = self.lab_end_offset
        else:
            max_consec = self.config.max_consecutive
            start_offset = self.aula_start_offset
            end_offset = self.aula_end_offset
        
        # ESTRATEGIA ÓPTIMA: Preferir 2 bloques consecutivos
        optimal_block_size = 2  # Óptimo es 2 bloques seguidos
        
        # Intentar asignar todos los bloques en un solo día primero
        if blocks_needed <= max_consec:
            for room in valid_rooms:
                for day in self.config.days:
                    # Usar rango específico para el tipo de aula
                    for start_block in range(start_offset, end_offset - blocks_needed + 1):
                        slots = self._find_consecutive_slots(
                            room, day, start_block, blocks_needed,
                            class_info.instructor_id, class_info
                        )
                        if slots:
                            assignment = Assignment(
                                class_info=class_info,
                                room=room,
                                timeslots=slots
                            )
                            self._assign_slots(class_info, room, slots)
                            return assignment
        
        # Si se necesita más bloques que el máximo consecutivo, distribuir en bloques óptimos de 2
        if blocks_needed > max_consec or (class_info.class_type != 'laboratorio' and blocks_needed > optimal_block_size):
            for room in valid_rooms:
                all_slots = []
                remaining = blocks_needed
                
                for day in self.config.days:
                    if remaining <= 0:
                        break
                    
                    # Para teoría/práctica preferir bloques de 2, para lab hasta 4
                    if class_info.class_type == 'laboratorio':
                        blocks_this_day = min(remaining, max_consec)
                    else:
                        # Óptimo: 2 bloques, máximo: max_consecutive
                        blocks_this_day = min(remaining, optimal_block_size)
                    
                    # Usar rango específico para el tipo de aula
                    for start_block in range(start_offset, end_offset - blocks_this_day + 1):
                        slots = self._find_consecutive_slots(
                            room, day, start_block, blocks_this_day,
                            class_info.instructor_id, class_info
                        )
                        if slots:
                            all_slots.extend(slots)
                            remaining -= len(slots)
                            break
                
                if len(all_slots) >= blocks_needed:
                    assignment = Assignment(
                        class_info=class_info,
                        room=room,
                        timeslots=all_slots[:blocks_needed]
                    )
                    self._assign_slots(class_info, room, assignment.timeslots)
                    return assignment
        
        return None
    
    def generate(self) -> Dict:
        # Genera el horario completo.
        start_time = time.time()
        
        # Ordenar clases por dificultad (más restricciones primero)
        sorted_classes = sorted(self.classes, key=lambda c: (
            -self._get_blocks_needed(c),  # Más horas primero
            -c.students,  # Más estudiantes primero
            c.instructor_id != '0',  # Con instructor asignado primero
            c.class_type == 'laboratorio'  # Laboratorios después
        ))
        
        assignments = []
        unassigned = []
        conflicts = 0
        
        for class_info in sorted_classes:
            assignment = self._try_assign_class(class_info)
            if assignment:
                assignments.append(assignment)
            else:
                unassigned.append(class_info)
                conflicts += 1
        
        # Intentar asignar las clases que no se pudieron asignar inicialmente con un enfoque más flexible
        for class_info in unassigned[:]:
            # Relajar restricción de año para clases no asignadas
            assignment = self._try_assign_flexible(class_info)
            if assignment:
                assignments.append(assignment)
                unassigned.remove(class_info)
                conflicts -= 1
        
        elapsed_time = time.time() - start_time
        
        # Calcular fitness
        fitness = 1000 - (conflicts * 100)
        
        return {
            'assignments': [self._to_dict(a) for a in assignments],
            'fitness_score': max(0, fitness),
            'conflict_count': len(unassigned),
            'generation_time_ms': int(elapsed_time * 1000),
            'generations_run': 1,
            'classes_assigned': len(assignments),
            'classes_total': len(self.classes),
            'unassigned': [c.name for c in unassigned]
        }
    
    def _try_assign_flexible(self, class_info: ClassInfo) -> Optional[Assignment]:
        # Asignación más flexible para clases difíciles.
        blocks_needed = self._get_blocks_needed(class_info)
        
        # Usar TODAS las salas que caben
        all_rooms = [r for r in self.rooms if r.capacity >= class_info.students]
        if not all_rooms:
            all_rooms = self.rooms[:]
        
        # Intentar con cualquier sala y cualquier slot libre
        for room in all_rooms:
            all_slots = []
            
            for day in self.config.days:
                if len(all_slots) >= blocks_needed:
                    break
                
                for block in range(self.blocks_per_day):
                    if len(all_slots) >= blocks_needed:
                        break
                    
                    # Solo verificar sala (ignorar instructor y año)
                    if (room.id, day, block) not in self.room_occupied:
                        all_slots.append(TimeSlot(day=day, block=block))
            
            if len(all_slots) >= blocks_needed:
                assignment = Assignment(
                    class_info=class_info,
                    room=room,
                    timeslots=all_slots[:blocks_needed]
                )
                self._assign_slots(class_info, room, assignment.timeslots)
                return assignment
        
        return None
    
    def _get_time_str(self, block: int) -> Tuple[str, str]:
        # Convierte bloque a hora inicio/fin.
        start_h, start_m = map(int, self.config.start_time.split(':'))
        block_total = self.config.block_duration + self.config.break_duration
        
        start_minutes = start_h * 60 + start_m + block * block_total
        end_minutes = start_minutes + self.config.block_duration
        
        start_str = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        end_str = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        
        return start_str, end_str
    
    def _to_dict(self, assignment: Assignment) -> Dict:
        # Convierte asignación a diccionario.
        instructor = self.instructor_map.get(assignment.class_info.instructor_id)
        
        schedule_list = []
        for slot in assignment.timeslots:
            start, end = self._get_time_str(slot.block)
            schedule_list.append({
                'day': slot.day,
                'block': slot.block,
                'start': start,
                'end': end
            })
        
        return {
            'class_id': assignment.class_info.id,
            'class_name': assignment.class_info.name,
            'class_type': assignment.class_info.class_type,
            'year': assignment.class_info.year,
            'room': {
                'id': assignment.room.id,
                'type': assignment.room.room_type
            },
            'instructor': {
                'id': assignment.class_info.instructor_id,
                'name': instructor.name if instructor else 'Por Contratar'
            },
            'schedule': schedule_list
        }


def load_from_xml(xml_path: str) -> Tuple[List[Room], List[Instructor], List[ClassInfo], Config]:
    # Carga datos desde XML
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    rooms = []
    for room_elem in root.findall('.//room'):
        rooms.append(Room(
            id=room_elem.get('id'),
            capacity=int(room_elem.get('capacity', 30)),
            room_type=room_elem.get('type', 'aula')
        ))
    
    instructors = []
    for inst_elem in root.findall('.//instructor'):
        instructors.append(Instructor(
            id=inst_elem.get('id'),
            name=inst_elem.get('name', f'Instructor_{inst_elem.get("id")}'),
            status=inst_elem.get('status', 'assigned')
        ))
    
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


def generate_from_xml(xml_path: str, **kwargs) -> Dict:
    # Genera horario desde archivo XML.
    rooms, instructors, classes, config = load_from_xml(xml_path)
    builder = ScheduleBuilder(rooms, instructors, classes, config)
    return builder.generate()


if __name__ == '__main__':
    import os
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Probar con escuela.xml
    test_file = os.path.join(base_dir, 'escuela.xml')
    
    if os.path.exists(test_file):
        print(f"Generando horario desde: {test_file}")
        result = generate_from_xml(test_file)
        
        print(f"\n=== RESULTADO ===")
        print(f"  Clases asignadas: {result['classes_assigned']}/{result['classes_total']}")
        print(f"  Sin asignar: {result['conflict_count']}")
        print(f"  Fitness: {result['fitness_score']}")
        print(f"  Tiempo: {result['generation_time_ms']} ms")
        
        if result['unassigned']:
            print(f"\nClases sin asignar:")
            for name in result['unassigned']:
                print(f"  - {name}")
        
        # Guardar resultado
        output_file = os.path.join(base_dir, 'horario_generado.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nHorario guardado en: {output_file}")
    else:
        print(f"No se encontró: {test_file}")
