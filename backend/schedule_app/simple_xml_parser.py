"""
Parser XML simplificado - Lee solo campos necesarios
"""

import xml.etree.ElementTree as ET
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class RoomData:
    id: str
    capacity: int
    room_type: str = 'normal'


@dataclass
class InstructorData:
    id: str
    name: str


@dataclass
class TimeSlotData:
    days: str
    start: int
    length: int
    blocks: int
    is_lab: bool = False


@dataclass
class ClassData:
    id: str
    name: str
    students: int
    instructor: str
    class_type: str
    timeslots: List[TimeSlotData]


class SimpleXMLParser:
    """Parser XML simplificado"""
    
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.rooms: List[RoomData] = []
        self.instructors: List[InstructorData] = []
        self.classes: List[ClassData] = []
    
    def parse(self):
        """Lee el XML"""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        
        # Parsear salas
        rooms_elem = root.find('rooms')
        if rooms_elem is not None:
            for room_elem in rooms_elem.findall('room'):
                self.rooms.append(RoomData(
                    id=room_elem.get('id'),
                    capacity=int(room_elem.get('capacity', 30)),
                    room_type=room_elem.get('type', 'normal')
                ))
        
        # Parsear instructores
        instructors_elem = root.find('instructors')
        if instructors_elem is not None:
            for inst_elem in instructors_elem.findall('instructor'):
                self.instructors.append(InstructorData(
                    id=inst_elem.get('id'),
                    name=inst_elem.get('name', '')
                ))
        
        # Parsear clases
        classes_elem = root.find('classes')
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                timeslots = []
                
                for ts_elem in class_elem.findall('timeslot'):
                    timeslots.append(TimeSlotData(
                        days=ts_elem.get('days', '0000000'),
                        start=int(ts_elem.get('start', 0)),
                        length=int(ts_elem.get('length', 0)),
                        blocks=int(ts_elem.get('blocks', 1)),
                        is_lab=ts_elem.get('is_lab', 'false') == 'true'
                    ))
                
                self.classes.append(ClassData(
                    id=class_elem.get('id'),
                    name=class_elem.get('name', ''),
                    students=int(class_elem.get('students', 30)),
                    instructor=class_elem.get('instructor', ''),
                    class_type=class_elem.get('type', 'normal'),
                    timeslots=timeslots
                ))
    
    def get_summary(self) -> Dict:
        """Retorna resumen de datos"""
        return {
            'rooms': len(self.rooms),
            'instructors': len(self.instructors),
            'classes': len(self.classes),
            'total_timeslots': sum(len(c.timeslots) for c in self.classes)
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python simple_xml_parser.py <archivo_xml>")
        sys.exit(1)
    
    parser = SimpleXMLParser(sys.argv[1])
    parser.parse()
    
    summary = parser.get_summary()
    print(f"\nResumen del XML:")
    print(f"  Salas: {summary['rooms']}")
    print(f"  Instructores: {summary['instructors']}")
    print(f"  Clases: {summary['classes']}")
    print(f"  Time slots: {summary['total_timeslots']}")
