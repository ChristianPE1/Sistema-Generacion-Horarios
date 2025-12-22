"""
Script para importar datos XML y probar el algoritmo genético.
"""

import os
import sys
import django
import time
import xml.etree.ElementTree as ET

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_system.settings')
django.setup()

from django.db import transaction
from schedule_app.models import (
    Room, Instructor, Course, Class, ClassInstructor,
    ClassRoom, TimeSlot, Student, StudentClass,
    GroupConstraint, GroupConstraintClass
)


def import_xml_file(xml_path):
    """Importa datos desde archivo XML directamente - soporta purdue_clean.xml"""
    print(f"\n[INFO] Importando {xml_path}...")
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    stats = {
        'rooms': 0,
        'instructors': 0,
        'courses': 0,
        'classes': 0,
        'time_slots': 0,
    }
    
    with transaction.atomic():
        # Limpiar datos existentes
        print("[INFO] Limpiando datos existentes...")
        TimeSlot.objects.all().delete()
        ClassInstructor.objects.all().delete()
        ClassRoom.objects.all().delete()
        Class.objects.all().delete()
        Course.objects.all().delete()
        Instructor.objects.all().delete()
        Room.objects.all().delete()
        
        # Crear diccionarios para mapeo rápido
        room_map = {}  # xml_id -> room_obj
        instructor_map = {}  # xml_id -> instructor_obj
        course_map = {}  # xml_id -> course_obj
        
        # 1. Importar Rooms
        rooms_elem = root.find('rooms')
        if rooms_elem is not None:
            for room_elem in rooms_elem.findall('room'):
                xml_id = int(room_elem.get('id'))
                room = Room.objects.create(
                    xml_id=xml_id,
                    capacity=int(room_elem.get('capacity', 30)),
                    location=room_elem.get('location', ''),
                    is_constraint=room_elem.get('constraint', 'false').lower() == 'true'
                )
                room_map[xml_id] = room
                stats['rooms'] += 1
        
        print(f"  ✓ Aulas: {stats['rooms']}")
        
        # 2. Importar Instructors (de sección instructors o extraer de clases)
        instructors_elem = root.find('instructors')
        if instructors_elem is not None:
            for instructor_elem in instructors_elem.findall('instructor'):
                xml_id = int(instructor_elem.get('id'))
                instructor = Instructor.objects.create(
                    xml_id=xml_id,
                    name=instructor_elem.get('name', f'Instructor {xml_id}')
                )
                instructor_map[xml_id] = instructor
                stats['instructors'] += 1
        
        print(f"  ✓ Instructores: {stats['instructors']}")
        
        # 3. Importar Classes (formato purdue_clean: elemento simple sin hijos)
        classes_elem = root.find('classes')
        max_classes = 100  # Limitar para pruebas rápidas
        
        if classes_elem is not None:
            class_list = list(classes_elem.findall('class'))[:max_classes]
            
            for class_elem in class_list:
                class_id = int(class_elem.get('id'))
                class_name = class_elem.get('name', f'Course {class_id}')
                class_code = class_elem.get('code', str(class_id))
                students = int(class_elem.get('students', 30))
                instructor_id = class_elem.get('instructor')
                hours = int(class_elem.get('hours', 1))
                
                # Crear o obtener curso
                if class_code not in course_map:
                    course = Course.objects.create(
                        xml_id=class_id,
                        name=class_name,
                        code=class_code
                    )
                    course_map[class_code] = course
                    stats['courses'] += 1
                else:
                    course = course_map[class_code]
                
                # Crear clase
                class_obj = Class.objects.create(
                    xml_id=class_id,
                    offering=course,
                    class_limit=students
                )
                stats['classes'] += 1
                
                # Asociar instructor si existe
                if instructor_id and instructor_id != '0':
                    instructor = instructor_map.get(int(instructor_id))
                    if instructor:
                        ClassInstructor.objects.create(
                            class_obj=class_obj,
                            instructor=instructor
                        )
                
                # Crear time slots por defecto (como lo hace el sistema)
                # Generar slots para todos los días y horas disponibles
                days_patterns = ['1000000', '0100000', '0010000', '0001000', '0000100']
                start_times = list(range(84, 216, 12))  # 7AM a 6PM (cada hora)
                
                # Crear 5 opciones de timeslots por clase (uno por cada día)
                for i, days in enumerate(days_patterns):
                    start_time = start_times[i % len(start_times)]
                    TimeSlot.objects.create(
                        class_obj=class_obj,
                        days=days,
                        start_time=start_time,
                        length=hours * 12,  # 12 slots = 1 hora
                        break_time=0,
                        preference=0.0
                    )
                    stats['time_slots'] += 1
        
        print(f"  ✓ Cursos: {stats['courses']}")
        print(f"  ✓ Clases: {stats['classes']} (limitado a {max_classes} para pruebas)")
        print(f"  ✓ Time Slots: {stats['time_slots']}")
    
    print(f"\n[OK] Importación completada!")
    return stats


def test_genetic_algorithm():
    """Prueba el algoritmo genético"""
    from schedule_app.schedule_generator import ScheduleGenerator
    
    print("\n" + "="*60)
    print("PRUEBA DEL ALGORITMO GENÉTICO")
    print("="*60)
    
    # Prueba 1: Pocas generaciones
    print("\n--- PRUEBA 1: 15 generaciones, población 40 ---")
    
    generator = ScheduleGenerator(
        population_size=40,
        generations=15,
        mutation_rate=0.15,
        crossover_rate=0.70,
        elitism_size=4,
        tournament_size=3
    )
    
    generator.load_data()
    
    start_time = time.time()
    result = generator.generate(
        schedule_name=f"Test Genético {time.strftime('%H:%M:%S')}",
        description="Prueba de algoritmo genético optimizado"
    )
    elapsed = time.time() - start_time
    
    print(f"\n✓ Horario generado!")
    print(f"  - Tiempo: {elapsed:.2f}s")
    print(f"  - Fitness: {result.fitness_score:.2f}")
    print(f"  - Conflictos: {result.conflict_count}")
    print(f"  - Tiempo por generación: {elapsed/15:.2f}s")
    
    # Prueba 2: Más generaciones si fue rápido
    if elapsed < 60:
        print("\n--- PRUEBA 2: 30 generaciones, población 50 ---")
        
        generator2 = ScheduleGenerator(
            population_size=50,
            generations=30,
            mutation_rate=0.15,
            crossover_rate=0.70,
            elitism_size=5,
            tournament_size=3
        )
        generator2.load_data()
        
        start_time2 = time.time()
        result2 = generator2.generate(
            schedule_name=f"Test Genético 2 {time.strftime('%H:%M:%S')}",
            description="Segunda prueba"
        )
        elapsed2 = time.time() - start_time2
        
        print(f"\n✓ Horario generado!")
        print(f"  - Tiempo: {elapsed2:.2f}s")
        print(f"  - Fitness: {result2.fitness_score:.2f}")
        print(f"  - Conflictos: {result2.conflict_count}")
        print(f"  - Tiempo por generación: {elapsed2/30:.2f}s")
        
        mejora = result.conflict_count - result2.conflict_count
        print(f"\n  → Mejora: {mejora} conflictos menos con más generaciones")
    
    return result


if __name__ == '__main__':
    # Determinar archivo XML a usar
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Buscar archivos XML disponibles (preferir Purdue con IDs numéricos)
    xml_files = [
        os.path.join(base_dir, 'pu-fal07-llr.xml'),
        os.path.join(base_dir, 'purdue_clean.xml'),
    ]
    
    xml_file = None
    for f in xml_files:
        if os.path.exists(f):
            xml_file = f
            break
    
    if not xml_file:
        print("[ERROR] No se encontró ningún archivo XML")
        sys.exit(1)
    
    # Verificar si hay datos
    num_classes = Class.objects.count()
    if num_classes == 0:
        print("[INFO] Base de datos vacía, importando XML...")
        import_xml_file(xml_file)
    else:
        print(f"[INFO] Ya hay {num_classes} clases en la BD")
        resp = input("¿Reimportar datos? (s/N): ").strip().lower()
        if resp == 's':
            import_xml_file(xml_file)
    
    # Ejecutar pruebas
    test_genetic_algorithm()
