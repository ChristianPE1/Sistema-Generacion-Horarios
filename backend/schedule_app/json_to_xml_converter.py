"""
Convertidor de datos JSON (datos_horarios.json) a formato XML compatible con el sistema
Genera archivos XML en el formato esperado por el parser xml_parser.py
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from typing import Dict, List


class JSONToXMLConverter:
    """Convierte el formato JSON de la carrera al formato XML de Purdue"""
    
    def __init__(self, json_path: str):
        """
        Args:
            json_path: Ruta al archivo datos_horarios.json
        """
        self.json_path = json_path
        self.data = None
        self.config = None
        
        # Mapeo de días a índices (lunes=0, martes=1, etc.)
        self.day_map = {
            'lunes': 0,
            'martes': 1,
            'miercoles': 2,
            'jueves': 3,
            'viernes': 4,
            'sabado': 5,
            'domingo': 6
        }
        
    def load_json(self):
        """Carga el archivo JSON"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.data = data
            self.config = data.get('configuracion_general', {})
            
    def time_to_slot(self, time_str: str) -> int:
        """
        Convierte tiempo HH:MM a slot número (slots de 5 minutos)
        Por ejemplo: 07:00 = slot 0, 07:05 = slot 1, etc.
        
        Args:
            time_str: Tiempo en formato "HH:MM"
            
        Returns:
            Número de slot (cada slot = 5 minutos desde inicio jornada)
        """
        inicio = datetime.strptime(self.config.get('inicio_jornada', '07:00'), '%H:%M')
        tiempo = datetime.strptime(time_str, '%H:%M')
        
        diff_minutes = int((tiempo - inicio).total_seconds() / 60)
        return diff_minutes // 5  # Slots de 5 minutos
    
    def minutes_to_slots(self, minutes: int) -> int:
        """
        Convierte minutos a número de slots (cada slot = 5 minutos)
        
        Args:
            minutes: Número de minutos
            
        Returns:
            Número de slots
        """
        return minutes // 5
    
    def generate_time_slots_for_course(self, course: Dict, class_id: int) -> List[Dict]:
        """
        Genera slots de tiempo para un curso respetando bloques de 50 min
        
        Args:
            course: Diccionario con datos del curso
            class_id: ID único de la clase
            
        Returns:
            Lista de diccionarios con información de slots de tiempo
        """
        slots = []
        
        # Configuración de bloques
        duracion_bloque = self.config.get('duracion_bloque_min', 50)
        max_bloques_consecutivos = self.config.get('max_bloques_consecutivos_por_sesion', 3)
        descanso = self.config.get('descanso_entre_bloques_min', 10)
        
        # Calcular total de horas por tipo
        horas_teoria = course.get('horas_teoria', 0)
        horas_practica = course.get('horas_practica', 0)
        horas_lab = course.get('horas_lab', 0)
        
        # Convertir horas semanales a bloques (1 hora = 60 min, aproximadamente 1 bloque de 50 min)
        total_horas_semana = horas_teoria + horas_practica + horas_lab
        
        # Calcular número de sesiones necesarias
        # Cada sesión puede tener hasta max_bloques_consecutivos bloques
        bloques_necesarios = int(total_horas_semana)  # 1 hora ≈ 1 bloque de 50 min
        
        # Distribuir en sesiones
        sesiones = []
        bloques_restantes = bloques_necesarios
        
        while bloques_restantes > 0:
            bloques_en_sesion = min(bloques_restantes, max_bloques_consecutivos)
            sesiones.append(bloques_en_sesion)
            bloques_restantes -= bloques_en_sesion
        
        # Generar slots para cada sesión
        slot_id_counter = class_id * 100  # Base única por clase
        
        # Patrones de días comunes (puedes expandir según necesites)
        dias_patterns = [
            '1010100',  # Lunes-Miércoles-Viernes
            '0101010',  # Martes-Jueves-Sábado  
            '1111100',  # Lunes a Viernes
            '1100000',  # Lunes-Martes
            '0011000',  # Miércoles-Jueves
        ]
        
        # Horarios de inicio comunes (cada 2 horas desde inicio jornada)
        inicio_jornada = self.config.get('inicio_jornada', '07:00')
        fin_jornada = self.config.get('fin_jornada', '20:10')
        
        inicio_dt = datetime.strptime(inicio_jornada, '%H:%M')
        fin_dt = datetime.strptime(fin_jornada, '%H:%M')
        
        horarios_inicio = []
        current_time = inicio_dt
        while current_time < fin_dt:
            horarios_inicio.append(current_time.strftime('%H:%M'))
            current_time += timedelta(hours=2)  # Cada 2 horas
        
        # Crear slots para cada combinación
        for dias in dias_patterns:
            for hora_inicio in horarios_inicio:
                for num_bloques in sesiones:
                    # Calcular duración total de la sesión
                    # (bloques * duración) + (bloques-1) * descanso
                    duracion_total = (num_bloques * duracion_bloque) + ((num_bloques - 1) * descanso)
                    
                    slot_info = {
                        'id': slot_id_counter,
                        'days': dias,
                        'start_time': self.time_to_slot(hora_inicio),
                        'length': self.minutes_to_slots(duracion_total),
                        'num_bloques': num_bloques,
                        'duracion_bloque_min': duracion_bloque
                    }
                    
                    slots.append(slot_info)
                    slot_id_counter += 1
        
        return slots
    
    def convert_to_xml(self, output_path: str = None) -> str:
        """
        Convierte el JSON a XML en formato Purdue compatible
        
        Args:
            output_path: Ruta donde guardar el XML (opcional)
            
        Returns:
            String con el XML generado
        """
        if not self.data:
            self.load_json()
        
        # Crear elemento raíz
        root = ET.Element('timetable')
        root.set('version', '2.4')
        root.set('initiative', 'UNSA-CS')
        root.set('term', '2025')
        root.set('year', '2025')
        root.set('created', datetime.now().strftime('%a %b %d %H:%M:%S %Y'))
        root.set('nrDays', '7')
        root.set('slotsPerDay', '288')  # 24h * 60min / 5min = 288 slots
        
        # Crear sección de salas
        rooms_elem = ET.SubElement(root, 'rooms')
        for idx, sala in enumerate(self.data.get('salas', []), start=1):
            room = ET.SubElement(rooms_elem, 'room')
            room.set('id', str(idx))
            room.set('constraint', 'true')
            room.set('capacity', str(sala.get('capacidad', 30)))
            
            # Location dummy (no tenemos coordenadas reales)
            room.set('location', f'100,{100 + idx * 10}')
        
        # Crear sección de clases
        classes_elem = ET.SubElement(root, 'classes')
        
        class_id_counter = 1
        offering_id_counter = 1
        
        for curso in self.data.get('cursos', []):
            # Crear elemento clase
            class_elem = ET.SubElement(classes_elem, 'class')
            class_elem.set('id', str(class_id_counter))
            class_elem.set('offering', str(offering_id_counter))
            class_elem.set('config', str(class_id_counter))
            class_elem.set('committed', 'false')
            class_elem.set('subpart', str(class_id_counter))
            class_elem.set('classLimit', str(curso.get('num_estudiantes', 30)))
            class_elem.set('department', '1')  # Departamento único
            class_elem.set('scheduler', '1')
            
            # Dates (patrón de 180 días hábiles - simplificado)
            dates_pattern = '0' * 50 + '1' * 100 + '0' * 30  # Patrón simple
            class_elem.set('dates', dates_pattern)
            
            # Agregar nombre del curso
            course_elem = ET.SubElement(class_elem, 'course')
            course_elem.set('name', curso.get('nombre', ''))
            course_elem.set('code', curso.get('codigo', ''))
            
            # Agregar profesor como instructor
            instructor_elem = ET.SubElement(class_elem, 'instructor')
            instructor_elem.set('id', curso.get('profesor_id', 'P000'))
            instructor_elem.set('name', '')  # Se llenará desde la lista de profesores
            
            # Generar time slots para esta clase
            time_slots = self.generate_time_slots_for_course(curso, class_id_counter)
            
            for slot_info in time_slots:
                time_elem = ET.SubElement(class_elem, 'time')
                time_elem.set('days', slot_info['days'])
                time_elem.set('start', str(slot_info['start_time']))
                time_elem.set('length', str(slot_info['length']))
                time_elem.set('breakTime', '0')
                time_elem.set('pattern', slot_info['days'])
                time_elem.set('preference', '0')
                
                # Agregar metadata sobre bloques
                time_elem.set('num_bloques', str(slot_info['num_bloques']))
                time_elem.set('duracion_bloque_min', str(slot_info['duracion_bloque_min']))
            
            # Agregar requerimientos de sala
            if curso.get('requiere_lab', 0) > 0:
                room_req = ET.SubElement(class_elem, 'room')
                room_req.set('requirement', 'lab')
            
            class_id_counter += 1
            offering_id_counter += 1
        
        # Crear sección de instructores
        instructors_elem = ET.SubElement(root, 'instructors')
        for profesor in self.data.get('profesores', []):
            instructor = ET.SubElement(instructors_elem, 'instructor')
            instructor.set('id', profesor.get('id', ''))
            instructor.set('name', profesor.get('nombre', ''))
            instructor.set('department', profesor.get('departamento', 'Sistemas'))
        
        # Secciones vacías (para compatibilidad)
        ET.SubElement(root, 'groupConstraints')
        ET.SubElement(root, 'students')
        
        # Convertir a string con formato bonito
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ')
        
        # Guardar si se especifica ruta
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            print(f"[INFO] XML generado en: {output_path}")
        
        return pretty_xml


def convert_json_to_xml(json_path: str, output_path: str = None):
    """
    Función helper para convertir JSON a XML
    
    Args:
        json_path: Ruta al archivo JSON
        output_path: Ruta donde guardar el XML (opcional)
        
    Returns:
        String con el XML generado
    """
    converter = JSONToXMLConverter(json_path)
    return converter.convert_to_xml(output_path)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python json_to_xml_converter.py <archivo_json> [archivo_xml_salida]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    xml_file = sys.argv[2] if len(sys.argv) > 2 else json_file.replace('.json', '.xml')
    
    convert_json_to_xml(json_file, xml_file)
    print(f"Conversión completada: {json_file} -> {xml_file}")
