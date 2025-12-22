"""
API Views para generación de horarios con Algoritmo Genético.

Endpoints:
- POST /api/generate/from-xml/ - Genera horario desde archivo XML
- POST /api/generate/from-json/ - Genera horario desde archivo JSON  
- GET /api/datasets/ - Lista datasets disponibles (escuela.xml, purdue_clean.xml)
"""
import os
import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .schedule_builder import load_from_xml
from .xml_cleaner import clean_purdue_xml, json_to_xml
from .schedule_generator import ScheduleGenerator
from .models import Room, Instructor, Course, Class, TimeSlot, ClassInstructor, ClassRoom, Schedule, ScheduleAssignment

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_dataset_path(name: str) -> str:
    """Obtiene la ruta completa de un dataset."""
    return os.path.join(BASE_DIR, name)


def import_xml_to_db(xml_path: str, max_classes: int = None) -> dict:
    """
    Importa datos desde XML a la base de datos y retorna estadísticas.
    Usa el formato purdue_clean.xml.
    """
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    stats = {'rooms': 0, 'instructors': 0, 'courses': 0, 'classes': 0, 'time_slots': 0}
    
    with transaction.atomic():
        # Limpiar datos existentes (orden correcto por dependencias FK)
        ScheduleAssignment.objects.all().delete()
        Schedule.objects.all().delete()
        TimeSlot.objects.all().delete()
        ClassRoom.objects.all().delete()
        ClassInstructor.objects.all().delete()
        Class.objects.all().delete()
        Course.objects.all().delete()
        Instructor.objects.all().delete()
        Room.objects.all().delete()
        
        room_map = {}
        instructor_map = {}
        course_map = {}
        
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
        
        # 2. Importar Instructors
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
        
        # 3. Importar Classes (formato purdue_clean)
        classes_elem = root.find('classes')
        if classes_elem is not None:
            class_list = list(classes_elem.findall('class'))
            if max_classes:
                class_list = class_list[:max_classes]
            
            course_id_counter = 1
            class_id_counter = 1  # Contador para IDs únicos de clases
            
            for class_elem in class_list:
                class_name = class_elem.get('name', f'Course {class_id_counter}')
                class_code = class_elem.get('code', str(class_id_counter))
                students = int(class_elem.get('students', 30))
                instructor_id = class_elem.get('instructor')
                hours = int(class_elem.get('hours', 1))
                
                # Crear o obtener curso
                if class_code not in course_map:
                    course = Course.objects.create(
                        xml_id=course_id_counter,
                        name=class_name,
                        code=class_code
                    )
                    course_map[class_code] = course
                    stats['courses'] += 1
                    course_id_counter += 1
                else:
                    course = course_map[class_code]
                
                # Crear clase con ID único generado
                class_obj = Class.objects.create(
                    xml_id=class_id_counter,
                    offering=course,
                    class_limit=students
                )
                class_id_counter += 1
                stats['classes'] += 1
                
                # Asociar instructor
                if instructor_id and instructor_id != '0':
                    instructor = instructor_map.get(int(instructor_id))
                    if instructor:
                        ClassInstructor.objects.create(
                            class_obj=class_obj,
                            instructor=instructor
                        )
                
                # Crear time slots por defecto
                days_patterns = ['1000000', '0100000', '0010000', '0001000', '0000100']
                start_times = list(range(84, 216, 12))
                
                for i, days in enumerate(days_patterns):
                    start_time = start_times[i % len(start_times)]
                    TimeSlot.objects.create(
                        class_obj=class_obj,
                        days=days,
                        start_time=start_time,
                        length=hours * 12,
                        break_time=0,
                        preference=0.0
                    )
                    stats['time_slots'] += 1
    
    return stats


def generate_with_genetic_algorithm(
    xml_path: str,
    population_size: int = 50,
    generations: int = 100,
    max_classes: int = 200
) -> dict:
    """
    Genera horario usando Algoritmo Genético real.
    
    1. Importa datos del XML a la BD
    2. Ejecuta el algoritmo genético
    3. Retorna resultados
    """
    start_time = time.time()
    
    # Importar datos a la BD (limitar clases para velocidad)
    stats = import_xml_to_db(xml_path, max_classes=max_classes)
    
    # Crear generador con parámetros
    generator = ScheduleGenerator(
        population_size=population_size,
        generations=generations,
        mutation_rate=0.15
    )
    
    # Cargar datos
    generator.load_data()
    
    # Generar horario
    schedule = generator.generate(schedule_name="Horario Genético")
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Obtener asignaciones
    from .models import ScheduleAssignment
    assignments_db = ScheduleAssignment.objects.filter(schedule=schedule)
    
    # Formatear resultado en el formato que espera el frontend
    assignments = []
    for assignment in assignments_db:
        # Convertir days pattern (1000000) a día de la semana
        days_str = assignment.time_slot.days if assignment.time_slot else "0000000"
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        day = 'Lunes'
        for i, d in enumerate(days_str):
            if d == '1':
                day = day_names[i]
                break
        
        # Convertir start_time a hora HH:MM
        start_time = assignment.time_slot.start_time if assignment.time_slot else 0
        start_hour = 7 + (start_time // 12)  # Cada 12 slots = 1 hora, empezando a las 7
        start_min = (start_time % 12) * 5  # Cada slot = 5 minutos
        end_slots = start_time + (assignment.time_slot.length if assignment.time_slot else 12)
        end_hour = 7 + (end_slots // 12)
        end_min = (end_slots % 12) * 5
        
        # Buscar instructor si existe
        instructor_name = "Sin asignar"
        instructor_id = "0"
        class_instructors = ClassInstructor.objects.filter(class_obj=assignment.class_obj)
        if class_instructors.exists():
            instructor = class_instructors.first().instructor
            instructor_name = instructor.name
            instructor_id = str(instructor.xml_id)
        
        assignments.append({
            'class_id': str(assignment.class_obj.xml_id),
            'class_name': assignment.class_obj.offering.name if assignment.class_obj.offering else f"Clase {assignment.class_obj.xml_id}",
            'class_type': 'teoria',
            'year': 1,
            'room': {
                'id': str(assignment.room.xml_id) if assignment.room else "0",
                'type': 'aula'
            },
            'instructor': {
                'id': instructor_id,
                'name': instructor_name
            },
            'schedule': [{
                'day': day,
                'block': start_time // 12 + 1,
                'start': f"{start_hour:02d}:{start_min:02d}",
                'end': f"{end_hour:02d}:{end_min:02d}"
            }]
        })
    
    # Calcular conflictos
    conflict_count = schedule.conflict_count if hasattr(schedule, 'conflict_count') else 0
    fitness_score = schedule.fitness_score if hasattr(schedule, 'fitness_score') else 0
    
    return {
        'assignments': assignments,
        'classes_assigned': len(assignments),
        'classes_total': stats['classes'],
        'conflict_count': conflict_count,
        'fitness_score': fitness_score,
        'generation_time_ms': elapsed_ms,
        'generations_run': generations,
        'algorithm': 'genetic',
        'parameters': {
            'population_size': population_size,
            'generations': generations
        },
        'stats': stats,
        'unassigned': []
    }


def get_dataset_path(name: str) -> str:
    """Obtiene la ruta completa de un dataset."""
    return os.path.join(BASE_DIR, name)


@csrf_exempt
@require_http_methods(["GET"])
def list_datasets(request):
    """Lista los datasets disponibles para generación."""
    datasets = []
    
    # Buscar XMLs limpios
    for filename in ['escuela.xml', 'purdue_clean.xml']:
        filepath = get_dataset_path(filename)
        if os.path.exists(filepath):
            # Leer info básica
            try:
                rooms, instructors, classes, config = load_from_xml(filepath)
                datasets.append({
                    'name': filename,
                    'path': filepath,
                    'type': 'xml',
                    'stats': {
                        'rooms': len(rooms),
                        'instructors': len(instructors),
                        'classes': len(classes)
                    }
                })
            except Exception as e:
                datasets.append({
                    'name': filename,
                    'path': filepath,
                    'type': 'xml',
                    'error': str(e)
                })
    
    # Buscar JSON de escuela
    json_path = get_dataset_path('datos_horarios.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            datasets.append({
                'name': 'datos_horarios.json',
                'path': json_path,
                'type': 'json',
                'stats': {
                    'rooms': len(data.get('salas', [])),
                    'instructors': len(data.get('profesores', [])),
                    'courses': len(data.get('cursos', []))
                }
            })
        except Exception as e:
            datasets.append({
                'name': 'datos_horarios.json',
                'path': json_path,
                'type': 'json',
                'error': str(e)
            })
    
    return JsonResponse({
        'success': True,
        'datasets': datasets
    })


@csrf_exempt
@require_http_methods(["POST"])
def generate_schedule(request):
    """
    Genera un horario usando el Algoritmo Genético.
    
    Body JSON:
    {
        "dataset": "escuela.xml" | "purdue_clean.xml",
        "name": "Nombre del horario",
        "population_size": 50,
        "generations": 100
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    
    dataset = data.get('dataset', 'escuela.xml')
    name = data.get('name', 'Horario Generado')
    population_size = int(data.get('population_size', 50))
    generations = int(data.get('generations', 100))
    
    # Validar parámetros
    if population_size < 10 or population_size > 500:
        population_size = 50
    if generations < 10 or generations > 500:
        generations = 100
    
    # Obtener path del dataset
    xml_path = get_dataset_path(dataset)
    
    # Si es JSON, convertir a XML primero
    if dataset.endswith('.json'):
        json_path = xml_path
        xml_path = get_dataset_path('temp_converted.xml')
        try:
            json_to_xml(json_path, xml_path)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error convirtiendo JSON: {str(e)}'
            }, status=400)
    
    if not os.path.exists(xml_path):
        # Intentar crear los XMLs si no existen
        try:
            _ensure_datasets_exist()
            if not os.path.exists(xml_path):
                return JsonResponse({
                    'success': False,
                    'error': f'Dataset no encontrado: {dataset}'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creando datasets: {str(e)}'
            }, status=500)
    
    try:
        # Generar horario usando Algoritmo Genético
        result = generate_with_genetic_algorithm(
            xml_path,
            population_size=population_size,
            generations=generations
        )
        
        result['name'] = name
        result['dataset'] = dataset
        
        # Guardar resultado en archivo JSON
        output_path = get_dataset_path('ultimo_horario.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Guardar en base de datos
        try:
            from .models import Schedule
            schedule = Schedule.objects.create(
                name=name,
                dataset=dataset,
                fitness_score=result.get('fitness_score', 0),
                conflict_count=result.get('conflict_count', 0),
                classes_assigned=result.get('classes_assigned', 0),
                classes_total=result.get('classes_total', 0),
                generation_time_ms=result.get('generation_time_ms', 0),
                status='completed',
                schedule_data=result
            )
            result['db_id'] = schedule.id
        except Exception as db_err:
            # Si falla el guardado en BD, continuar sin error
            print(f"Error guardando en BD: {db_err}")
        
        return JsonResponse({
            'success': True,
            'schedule': result
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_from_upload(request):
    """
    Genera horario desde archivo subido.
    
    Form data:
    - file: Archivo XML o JSON
    - name: Nombre del horario
    - population_size: Tamaño de población (opcional)
    - generations: Número de generaciones (opcional)
    """
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No se proporcionó archivo'
        }, status=400)
    
    uploaded_file = request.FILES['file']
    name = request.POST.get('name', 'Horario Generado')
    population_size = int(request.POST.get('population_size', 50))
    generations = int(request.POST.get('generations', 100))
    
    # Guardar archivo temporalmente
    temp_path = get_dataset_path(f'temp_upload_{uploaded_file.name}')
    xml_path = temp_path
    
    with open(temp_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    
    try:
        # Si es JSON, convertir a XML
        if uploaded_file.name.endswith('.json'):
            xml_path = get_dataset_path('temp_converted.xml')
            json_to_xml(temp_path, xml_path)
        
        # Generar horario
        result = generate_from_xml(
            xml_path,
            population_size=population_size,
            generations=generations
        )
        
        result['name'] = name
        result['source_file'] = uploaded_file.name
        
        return JsonResponse({
            'success': True,
            'schedule': result
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
    finally:
        # Limpiar archivos temporales
        if os.path.exists(temp_path):
            os.remove(temp_path)
        converted_path = get_dataset_path('temp_converted.xml')
        if os.path.exists(converted_path):
            os.remove(converted_path)


@csrf_exempt
@require_http_methods(["POST"])
def prepare_datasets(request):
    """
    Prepara los datasets (limpia XMLs y convierte JSON).
    Llamar una vez para crear los archivos limpios.
    """
    results = {}
    
    # 1. Limpiar XML de Purdue
    purdue_input = get_dataset_path('pu-fal07-llr.xml')
    purdue_output = get_dataset_path('purdue_clean.xml')
    
    if os.path.exists(purdue_input):
        try:
            stats = clean_purdue_xml(purdue_input, purdue_output)
            results['purdue'] = {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            results['purdue'] = {
                'success': False,
                'error': str(e)
            }
    else:
        results['purdue'] = {
            'success': False,
            'error': 'Archivo pu-fal07-llr.xml no encontrado'
        }
    
    # 2. Convertir JSON de escuela
    json_input = get_dataset_path('datos_horarios.json')
    escuela_output = get_dataset_path('escuela.xml')
    
    if os.path.exists(json_input):
        try:
            stats = json_to_xml(json_input, escuela_output)
            results['escuela'] = {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            results['escuela'] = {
                'success': False,
                'error': str(e)
            }
    else:
        results['escuela'] = {
            'success': False,
            'error': 'Archivo datos_horarios.json no encontrado'
        }
    
    return JsonResponse({
        'success': all(r.get('success', False) for r in results.values()),
        'results': results
    })


def _ensure_datasets_exist():
    """Asegura que los datasets existan."""
    purdue_clean = get_dataset_path('purdue_clean.xml')
    escuela_xml = get_dataset_path('escuela.xml')
    
    if not os.path.exists(purdue_clean):
        purdue_input = get_dataset_path('pu-fal07-llr.xml')
        if os.path.exists(purdue_input):
            clean_purdue_xml(purdue_input, purdue_clean)
    
    if not os.path.exists(escuela_xml):
        json_input = get_dataset_path('datos_horarios.json')
        if os.path.exists(json_input):
            json_to_xml(json_input, escuela_xml)


@csrf_exempt
@require_http_methods(["GET"])
def get_last_schedule(request):
    """Obtiene el último horario generado."""
    output_path = get_dataset_path('ultimo_horario.json')
    
    if not os.path.exists(output_path):
        return JsonResponse({
            'success': False,
            'error': 'No hay horarios generados'
        }, status=404)
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
        
        return JsonResponse({
            'success': True,
            'schedule': schedule
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_saved_schedules(request):
    """Lista los horarios guardados en la base de datos."""
    from .models import Schedule
    
    schedules = Schedule.objects.all().order_by('-created_at')[:20]
    
    data = []
    for s in schedules:
        data.append({
            'id': s.id,
            'name': s.name,
            'dataset': s.dataset,
            'fitness_score': s.fitness_score,
            'conflict_count': s.conflict_count,
            'classes_assigned': s.classes_assigned,
            'classes_total': s.classes_total,
            'generation_time_ms': s.generation_time_ms,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'status': s.status
        })
    
    return JsonResponse({
        'success': True,
        'schedules': data
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_saved_schedule(request, schedule_id):
    """Obtiene un horario específico guardado en la BD."""
    from .models import Schedule
    
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        return JsonResponse({
            'success': True,
            'schedule': schedule.schedule_data
        })
    except Schedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Horario no encontrado'
        }, status=404)
