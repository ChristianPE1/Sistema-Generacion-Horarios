"""
Limpiador de XML Purdue - Mantiene las 896 clases originales,
elimina información innecesaria (timeslots, students, location, groupConstraints).

El algoritmo genético debe ENCONTRAR los timeslots óptimos, no vienen predefinidos.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom


def clean_purdue_xml(input_path: str, output_path: str) -> dict:
    """
    Limpia el XML de Purdue manteniendo solo:
    - rooms: id, capacity (sin location, sharing)
    - instructors: id, name (extraído de clases)
    - classes: id, name (offering), students (classLimit), instructor, type
    
    ELIMINA:
    - timeslots (el AG los genera)
    - location de rooms
    - sharing patterns
    - students enrollments
    - groupConstraints
    - dates, committed, config, subpart, department, scheduler
    - room preferences
    """
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    # Crear nuevo XML limpio
    clean_root = ET.Element('timetable')
    clean_root.set('version', '3.0')
    clean_root.set('type', 'purdue')
    clean_root.set('source', 'pu-fal07-llr.xml')
    
    # === ROOMS (solo únicos) ===
    rooms_elem = ET.SubElement(clean_root, 'rooms')
    rooms_data = {}
    
    for room in root.findall('.//room'):
        room_id = room.get('id')
        capacity = room.get('capacity', '30')
        
        # Solo agregar si no existe ya (evitar duplicados)
        if room_id not in rooms_data:
            clean_room = ET.SubElement(rooms_elem, 'room')
            clean_room.set('id', room_id)
            clean_room.set('capacity', capacity)
            clean_room.set('type', 'aula')  # Por defecto aula
            rooms_data[room_id] = int(capacity)
    
    # === INSTRUCTORS (extraer de clases) ===
    instructors_elem = ET.SubElement(clean_root, 'instructors')
    instructors_found = set()
    
    for cls in root.findall('.//class'):
        instructor_elem = cls.find('instructor')
        if instructor_elem is not None:
            inst_id = instructor_elem.get('id')
            if inst_id and inst_id not in instructors_found:
                instructors_found.add(inst_id)
                clean_inst = ET.SubElement(instructors_elem, 'instructor')
                clean_inst.set('id', inst_id)
                clean_inst.set('name', f'Instructor_{inst_id}')
                clean_inst.set('status', 'assigned')
    
    # Añadir placeholder para clases sin instructor
    clean_inst = ET.SubElement(instructors_elem, 'instructor')
    clean_inst.set('id', '0')
    clean_inst.set('name', 'Por_Contratar')
    clean_inst.set('status', 'pending')
    
    # === CLASSES ===
    classes_elem = ET.SubElement(clean_root, 'classes')
    class_count = 0
    
    for cls in root.findall('.//class'):
        class_id = cls.get('id')
        offering_id = cls.get('offering', class_id)
        class_limit = cls.get('classLimit', '30')
        
        # Determinar tipo basado en el nombre/offering
        class_type = 'teoria'
        
        # Buscar instructor
        instructor_elem = cls.find('instructor')
        instructor_id = instructor_elem.get('id') if instructor_elem is not None else '0'
        
        # Calcular horas (basado en timeslots disponibles)
        # Por ahora asumimos 3 horas estándar, el AG decidirá distribución
        hours = 3
        time_elems = cls.findall('time')
        if time_elems:
            # Usar el length del primer timeslot como referencia
            length = int(time_elems[0].get('length', '12'))
            # length 12 = 60 min = 1 hora aprox
            hours = max(1, length // 10)
        
        # Crear clase limpia (SIN timeslots predefinidos)
        clean_class = ET.SubElement(classes_elem, 'class')
        clean_class.set('id', class_id)
        clean_class.set('name', f'Course_{offering_id}')
        clean_class.set('code', offering_id)
        clean_class.set('students', class_limit)
        clean_class.set('instructor', instructor_id)
        clean_class.set('type', class_type)
        clean_class.set('hours', str(hours))
        clean_class.set('year', '0')  # 0 = sin año específico (no hay conflicto de estudiantes)
        # NO añadimos timeslots - el AG los genera
        
        class_count += 1
    
    # === CONFIGURACIÓN ===
    config_elem = ET.SubElement(clean_root, 'config')
    config_elem.set('days', 'lunes,martes,miercoles,jueves,viernes')
    config_elem.set('block_duration', '50')
    config_elem.set('break_duration', '10')
    config_elem.set('start_time', '07:00')
    config_elem.set('end_time', '20:00')
    config_elem.set('max_consecutive', '3')
    
    # Escribir XML formateado
    xml_str = ET.tostring(clean_root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    # Eliminar línea de declaración duplicada
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return {
        'rooms': len(rooms_data),
        'instructors': len(instructors_found) + 1,
        'classes': class_count,
        'source': input_path,
        'output': output_path
    }


def json_to_xml(json_path: str, output_path: str) -> dict:
    """
    Convierte el JSON de la escuela a formato XML limpio.
    """
    import json
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Crear XML
    root = ET.Element('timetable')
    root.set('version', '3.0')
    root.set('type', 'escuela')
    root.set('source', 'datos_horarios.json')
    
    # === ROOMS ===
    rooms_elem = ET.SubElement(root, 'rooms')
    for sala in data.get('salas', []):
        room = ET.SubElement(rooms_elem, 'room')
        room.set('id', str(sala['id']))
        room.set('capacity', str(sala.get('capacidad', 30)))
        room.set('type', 'laboratorio' if sala.get('tipo', 1) == 2 else 'aula')
    
    # === INSTRUCTORS ===
    instructors_elem = ET.SubElement(root, 'instructors')
    for prof in data.get('profesores', []):
        inst = ET.SubElement(instructors_elem, 'instructor')
        inst.set('id', prof['id'])
        inst.set('name', prof.get('nombre', prof['id']))
        # Si el nombre contiene "Contrato" está por contratar
        status = 'pending' if 'contrato' in prof.get('nombre', '').lower() else 'assigned'
        inst.set('status', status)
    
    # === CLASSES ===
    classes_elem = ET.SubElement(root, 'classes')
    class_id = 1
    
    for curso in data.get('cursos', []):
        # Crear sesiones según tipo
        horas_teoria = curso.get('horas_teoria', 0)
        horas_practica = curso.get('horas_practica', 0)
        horas_lab = curso.get('horas_lab', 0)
        
        base_name = curso.get('nombre', f'Curso_{curso["codigo"]}')
        
        # Sesión de teoría
        if horas_teoria > 0:
            cls = ET.SubElement(classes_elem, 'class')
            cls.set('id', str(class_id))
            cls.set('name', f'{base_name} - Teoría')
            cls.set('code', str(curso.get('codigo', class_id)))
            cls.set('students', str(curso.get('num_estudiantes', 30)))
            cls.set('instructor', str(curso.get('profesor_id', '0')))
            cls.set('type', 'teoria')
            cls.set('hours', str(horas_teoria))
            cls.set('year', str(curso.get('anio', 1)))
            class_id += 1
        
        # Sesión de práctica
        if horas_practica > 0:
            cls = ET.SubElement(classes_elem, 'class')
            cls.set('id', str(class_id))
            cls.set('name', f'{base_name} - Práctica')
            cls.set('code', str(curso.get('codigo', class_id)))
            cls.set('students', str(curso.get('num_estudiantes', 30)))
            cls.set('instructor', str(curso.get('profesor_id', '0')))
            cls.set('type', 'practica')
            cls.set('hours', str(horas_practica))
            cls.set('year', str(curso.get('anio', 1)))
            class_id += 1
        
        # Sesión de laboratorio
        if horas_lab > 0:
            cls = ET.SubElement(classes_elem, 'class')
            cls.set('id', str(class_id))
            cls.set('name', f'{base_name} - Laboratorio')
            cls.set('code', str(curso.get('codigo', class_id)))
            cls.set('students', str(curso.get('num_estudiantes', 30)))
            cls.set('instructor', str(curso.get('profesor_id', '0')))
            cls.set('type', 'laboratorio')
            cls.set('hours', str(horas_lab))
            cls.set('year', str(curso.get('anio', 1)))
            class_id += 1
    
    # === CONFIG ===
    config = data.get('configuracion_general', {})
    config_elem = ET.SubElement(root, 'config')
    config_elem.set('days', ','.join(config.get('dias', ['lunes','martes','miercoles','jueves','viernes'])))
    config_elem.set('block_duration', str(config.get('duracion_bloque_min', 50)))
    config_elem.set('break_duration', str(config.get('descanso_entre_bloques_min', 10)))
    config_elem.set('start_time', config.get('inicio_jornada', '07:00'))
    config_elem.set('end_time', config.get('fin_jornada', '20:00'))
    config_elem.set('max_consecutive', str(config.get('max_bloques_consecutivos_por_sesion', 3)))
    
    # Escribir
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return {
        'rooms': len(data.get('salas', [])),
        'instructors': len(data.get('profesores', [])),
        'classes': class_id - 1,
        'courses': len(data.get('cursos', [])),
        'source': json_path,
        'output': output_path
    }


if __name__ == '__main__':
    import sys
    import os
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("=" * 60)
    print("LIMPIADOR DE ARCHIVOS XML")
    print("=" * 60)
    
    # 1. Limpiar XML de Purdue
    purdue_input = os.path.join(base_dir, 'pu-fal07-llr.xml')
    purdue_output = os.path.join(base_dir, 'purdue_clean.xml')
    
    if os.path.exists(purdue_input):
        print(f"\n[1] Limpiando XML de Purdue...")
        stats = clean_purdue_xml(purdue_input, purdue_output)
        print(f"    - Salas: {stats['rooms']}")
        print(f"    - Instructores: {stats['instructors']}")
        print(f"    - Clases: {stats['classes']}")
        print(f"    - Salida: {stats['output']}")
    else:
        print(f"[!] No se encontró: {purdue_input}")
    
    # 2. Convertir JSON de escuela a XML
    json_input = os.path.join(base_dir, 'datos_horarios.json')
    escuela_output = os.path.join(base_dir, 'escuela.xml')
    
    if os.path.exists(json_input):
        print(f"\n[2] Convirtiendo JSON de escuela a XML...")
        stats = json_to_xml(json_input, escuela_output)
        print(f"    - Salas: {stats['rooms']}")
        print(f"    - Instructores: {stats['instructors']}")
        print(f"    - Cursos base: {stats['courses']}")
        print(f"    - Clases (sesiones): {stats['classes']}")
        print(f"    - Salida: {stats['output']}")
    else:
        print(f"[!] No se encontró: {json_input}")
    
    print("\n" + "=" * 60)
    print("COMPLETADO")
    print("=" * 60)
