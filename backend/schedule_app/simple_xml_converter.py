"""
Convertidor simplificado JSON a XML limpio
Solo incluye campos necesarios para generación de horarios
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from typing import Dict, List


class SimpleJSONToXMLConverter:
    """Convierte JSON a XML limpio (sin campos innecesarios)"""
    
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = None
        self.config = None
        
    def load_json(self):
        """Carga el archivo JSON"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.data = data
            self.config = data.get('configuracion_general', {})
    
    def time_to_slot(self, time_str: str) -> int:
        """Convierte HH:MM a slot (slots de 5 min)"""
        inicio = datetime.strptime(self.config.get('inicio_jornada', '07:00'), '%H:%M')
        tiempo = datetime.strptime(time_str, '%H:%M')
        diff_minutes = int((tiempo - inicio).total_seconds() / 60)
        return diff_minutes // 5
    
    def minutes_to_slots(self, minutes: int) -> int:
        """Convierte minutos a slots"""
        return minutes // 5
    
    def generate_time_slots_for_course(self, course: Dict) -> List[Dict]:
        """Genera slots respetando bloques de 50 min y máx 3 consecutivos"""
        slots = []
        
        duracion_bloque = self.config.get('duracion_bloque_min', 50)
        max_bloques_consecutivos = self.config.get('max_bloques_consecutivos_por_sesion', 3)
        descanso = self.config.get('descanso_entre_bloques_min', 10)
        
        # Calcular horas totales
        horas_teoria = course.get('horas_teoria', 0)
        horas_practica = course.get('horas_practica', 0)
        horas_lab = course.get('horas_lab', 0)
        
        total_horas = horas_teoria + horas_practica + horas_lab
        bloques_necesarios = int(total_horas)
        
        # Distribuir en sesiones
        sesiones = []
        bloques_restantes = bloques_necesarios
        
        while bloques_restantes > 0:
            bloques_en_sesion = min(bloques_restantes, max_bloques_consecutivos)
            sesiones.append({
                'bloques': bloques_en_sesion,
                'es_lab': horas_lab > 0 and bloques_restantes == int(horas_lab)
            })
            bloques_restantes -= bloques_en_sesion
        
        # Patrones de días
        dias_patterns = ['1010100', '0101010', '1111100', '1100000', '0011000']
        
        # Horarios de inicio
        inicio_dt = datetime.strptime(self.config.get('inicio_jornada', '07:00'), '%H:%M')
        fin_dt = datetime.strptime(self.config.get('fin_jornada', '20:10'), '%H:%M')
        
        horarios_inicio = []
        current_time = inicio_dt
        while current_time < fin_dt:
            horarios_inicio.append(current_time.strftime('%H:%M'))
            current_time += timedelta(hours=2)
        
        # Generar slots
        for dias in dias_patterns:
            for hora_inicio in horarios_inicio:
                for sesion_info in sesiones:
                    num_bloques = sesion_info['bloques']
                    es_lab = sesion_info['es_lab']
                    
                    # Duración: (bloques * 50) + (bloques-1) * descanso
                    duracion_total_min = (num_bloques * duracion_bloque) + ((num_bloques - 1) * descanso)
                    
                    slots.append({
                        'days': dias,
                        'start': self.time_to_slot(hora_inicio),
                        'length': self.minutes_to_slots(duracion_total_min),
                        'num_bloques': num_bloques,
                        'es_lab': es_lab
                    })
        
        return slots
    
    def convert_to_xml(self, output_path: str = None) -> str:
        """Convierte a XML limpio"""
        if not self.data:
            self.load_json()
        
        # Elemento raíz
        root = ET.Element('timetable')
        root.set('version', '3.0')
        root.set('created', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Salas
        rooms_elem = ET.SubElement(root, 'rooms')
        for sala in self.data.get('salas', []):
            room = ET.SubElement(rooms_elem, 'room')
            room.set('id', str(sala['id']))
            room.set('capacity', str(sala['capacidad']))
            room.set('type', str(sala.get('tipo', 'normal')))
        
        # Instructores
        instructors_elem = ET.SubElement(root, 'instructors')
        for profesor in self.data.get('profesores', []):
            instructor = ET.SubElement(instructors_elem, 'instructor')
            instructor.set('id', str(profesor['id']))
            instructor.set('name', str(profesor['nombre']))
        
        # Clases
        classes_elem = ET.SubElement(root, 'classes')
        
        for curso in self.data.get('cursos', []):
            class_elem = ET.SubElement(classes_elem, 'class')
            class_elem.set('id', str(curso['codigo']))
            class_elem.set('name', str(curso['nombre']))
            class_elem.set('students', str(curso['num_estudiantes']))
            class_elem.set('instructor', str(curso['profesor_id']))
            
            # Tipo de clase
            if curso.get('requiere_lab', 0) > 0:
                class_elem.set('type', 'lab')
            else:
                class_elem.set('type', 'normal')
            
            # Time slots
            time_slots = self.generate_time_slots_for_course(curso)
            for slot in time_slots:
                time_elem = ET.SubElement(class_elem, 'timeslot')
                time_elem.set('days', str(slot['days']))
                time_elem.set('start', str(slot['start']))
                time_elem.set('length', str(slot['length']))
                time_elem.set('blocks', str(slot['num_bloques']))
                if slot['es_lab']:
                    time_elem.set('is_lab', 'true')
        
        # Convertir a string
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ')
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
        
        return pretty_xml


def convert_json_to_clean_xml(json_path: str, output_path: str = None):
    """Función helper para conversión"""
    converter = SimpleJSONToXMLConverter(json_path)
    return converter.convert_to_xml(output_path)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python simple_xml_converter.py <archivo_json> [archivo_xml_salida]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    xml_file = sys.argv[2] if len(sys.argv) > 2 else json_file.replace('.json', '_clean.xml')
    
    convert_json_to_clean_xml(json_file, xml_file)
    print(f"XML limpio generado: {xml_file}")
