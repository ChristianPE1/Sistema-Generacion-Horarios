import os
import json
import time
import random
import copy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Schedule
from .schedule_builder import ScheduleBuilder, load_from_xml
from .xml_cleaner import clean_purdue_xml, json_to_xml

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===============================
# CONFIGURACIÓN DE RESTRICCIONES
# ===============================

# Restricciones por defecto
DEFAULT_CONSTRAINTS = {
    # Restricciones para aulas normales
    'aulas': {
        'max_classes_per_day': None,      # None = sin límite
        'max_classes_per_week': None,     # None = sin límite
        'start_time': '07:00',            # Hora inicio jornada
        'end_time': '20:00',              # Hora fin jornada
    },
    # Restricciones para laboratorios
    'laboratorios': {
        'max_classes_per_day': None,
        'max_classes_per_week': None,
        'start_time': '07:00',
        'end_time': '20:00',
    },
    # Restricciones generales
    'general': {
        'max_consecutive_blocks': 3,       # Máx bloques consecutivos teoría/práctica
        'max_consecutive_lab_blocks': 4,   # Máx bloques consecutivos laboratorio
        'break_duration_minutes': 10,      # Descanso entre bloques
        'block_duration_minutes': 50,      # Duración de cada bloque
    }
}


def get_dataset_path(name: str) -> str:
    # Obtiene la ruta completa de un dataset.
    return os.path.join(BASE_DIR, name)


def _ensure_datasets_exist():
    # Asegura que los datasets existan.
    purdue_clean_path = get_dataset_path('purdue_clean.xml')
    purdue_original = get_dataset_path('pu-fal07-llr.xml')
    
    if not os.path.exists(purdue_clean_path) and os.path.exists(purdue_original):
        try:
            clean_purdue_xml(purdue_original, purdue_clean_path)
        except Exception as e:
            print(f"Error limpiando Purdue XML: {e}")


def _save_schedule_to_db(schedule_data: dict) -> Schedule:
    # Guarda un horario en la base de datos y retorna el objeto Schedule.
    schedule = Schedule.objects.create(
        name=schedule_data.get('name', 'Horario Generado'),
        dataset=schedule_data.get('dataset', 'unknown'),
        fitness_score=schedule_data.get('fitness_score', 0),
        conflict_count=schedule_data.get('conflict_count', 0),
        classes_assigned=schedule_data.get('classes_assigned', 0),
        classes_total=schedule_data.get('classes_total', 0),
        generation_time_ms=schedule_data.get('generation_time_ms', 0),
        status='completed',
        schedule_data=schedule_data  # Guardar datos completos como JSON
    )
    return schedule


# ===============================
# ALGORITMO GENÉTICO - IMPLEMENTACIÓN
# ===============================

def generate_with_genetic_algorithm(xml_path: str, population_size: int = 50, generations: int = 100,constraints: dict = None) -> dict:
    start_time = time.time()
    
    # Merge constraints con defaults
    active_constraints = copy.deepcopy(DEFAULT_CONSTRAINTS)
    if constraints:
        for key in constraints:
            if key in active_constraints:
                active_constraints[key].update(constraints[key])
    
    # ===============================
    # FASE 1: INICIALIZACIÓN GREEDY
    # ===============================
    rooms, instructors, classes, config = load_from_xml(xml_path)
    
    builder = ScheduleBuilder(rooms, instructors, classes, config, constraints=active_constraints)
    
    greedy_result = builder.generate()
    
    if not greedy_result['assignments']:
        greedy_result['algorithm'] = 'greedy (sin asignaciones)'
        greedy_result['constraints_applied'] = active_constraints
        return greedy_result
    
    # Preparar datos para AG
    room_list = [{'id': r.id, 'type': r.room_type, 'capacity': r.capacity} for r in rooms]
    
    greedy_fitness = _evaluate_fitness(greedy_result['assignments'], room_list, config)
    greedy_time = time.time() - start_time
    
    # ===============================
    # FASE 2: ALGORITMO GENÉTICO
    # ===============================
    ga_start = time.time()
    
    # Crear población inicial
    population = []
    base_assignments = greedy_result['assignments']
    
    # Primer individuo = solución greedy original
    population.append({
        'assignments': copy.deepcopy(base_assignments),
        'fitness': greedy_fitness
    })
    
    # Generar resto de la población con mutaciones
    for i in range(population_size - 1):
        mutated = _create_mutant(base_assignments, room_list, mutation_rate=0.1 + (i * 0.01))
        fitness = _evaluate_fitness(mutated, room_list, config)
        population.append({
            'assignments': mutated,
            'fitness': fitness
        })
    
    # Tracking
    best_individual = max(population, key=lambda x: x['fitness'])
    best_fitness = best_individual['fitness']
    best_assignments = copy.deepcopy(best_individual['assignments'])
    
    generations_without_improvement = 0
    final_gen = 0
    
    # ===============================
    # LOOP EVOLUTIVO
    # ===============================
    for gen in range(generations):
        final_gen = gen
        
        population.sort(key=lambda x: -x['fitness'])
        
        # Elitismo
        elite_count = max(2, population_size // 10)
        new_population = population[:elite_count]
        
        # Generar nuevos individuos
        while len(new_population) < population_size:
            parent1 = _tournament_selection(population, tournament_size=3)
            parent2 = _tournament_selection(population, tournament_size=3)
            
            # Cruce
            if random.random() < 0.7:
                child_assignments = _crossover(
                    parent1['assignments'], 
                    parent2['assignments'],
                    room_list
                )
            else:
                child_assignments = copy.deepcopy(parent1['assignments'])
            
            # Mutación adaptativa
            mutation_rate = 0.15 + (0.1 * (generations_without_improvement / 20))
            mutation_rate = min(0.4, mutation_rate)
            
            child_assignments = _mutate(child_assignments, room_list, mutation_rate)
            child_fitness = _evaluate_fitness(child_assignments, room_list, config)
            
            new_population.append({
                'assignments': child_assignments,
                'fitness': child_fitness
            })
        
        population = new_population
        
        # Actualizar mejor solución
        current_best = max(population, key=lambda x: x['fitness'])
        if current_best['fitness'] > best_fitness:
            best_fitness = current_best['fitness']
            best_assignments = copy.deepcopy(current_best['assignments'])
            generations_without_improvement = 0
        else:
            generations_without_improvement += 1
        
        # Parada temprana
        if generations_without_improvement >= 30 and gen > generations // 2:
            break
    
    ga_time = time.time() - ga_start
    total_time = time.time() - start_time
    
    # Estadísticas
    improvement = ((best_fitness - greedy_fitness) / max(greedy_fitness, 1)) * 100
    room_usage = _calculate_room_usage(best_assignments)
    
    return {
        'assignments': best_assignments,
        'fitness_score': round(best_fitness, 2),
        'conflict_count': greedy_result['conflict_count'],
        'generation_time_ms': int(total_time * 1000),
        'generations_run': final_gen + 1,
        'classes_assigned': len(best_assignments),
        'classes_total': greedy_result['classes_total'],
        'unassigned': greedy_result['unassigned'],
        'algorithm': 'greedy+genetic',
        'constraints_applied': active_constraints,
        'stats': {
            'greedy_fitness': round(greedy_fitness, 2),
            'greedy_time_ms': int(greedy_time * 1000),
            'ga_time_ms': int(ga_time * 1000),
            'final_fitness': round(best_fitness, 2),
            'improvement_percent': round(improvement, 2),
            'room_usage': room_usage
        }
    }


def _create_mutant(assignments: list, room_list: list, mutation_rate: float = 0.2) -> list:
    # Crea una copia mutada de las asignaciones.
    mutated = copy.deepcopy(assignments)
    
    for assignment in mutated:
        if random.random() < mutation_rate:
            current_type = assignment['room'].get('type', 'aula')
            compatible_rooms = [r for r in room_list if r['type'] == current_type or r['type'] == 'aula']
            
            if compatible_rooms:
                new_room = random.choice(compatible_rooms)
                assignment['room'] = {'id': new_room['id'], 'type': new_room['type']}
    
    return mutated


def _tournament_selection(population: list, tournament_size: int = 3) -> dict:
    # Selección por torneo.
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda x: x['fitness'])


def _crossover(parent1_assignments: list, parent2_assignments: list, room_list: list) -> list:
    # Cruce de dos puntos.
    if len(parent1_assignments) <= 2:
        return copy.deepcopy(parent1_assignments)
    
    child = copy.deepcopy(parent1_assignments)
    size = len(child)
    point1 = random.randint(0, size // 2)
    point2 = random.randint(size // 2, size - 1)
    
    for i in range(point1, min(point2 + 1, len(parent2_assignments))):
        if i < len(child):
            child[i]['room'] = copy.deepcopy(parent2_assignments[i]['room'])
    
    return child


def _mutate(assignments: list, room_list: list, mutation_rate: float = 0.15) -> list:
    # Mutación con equilibrio de aulas.
    mutated = copy.deepcopy(assignments)
    
    room_usage = {}
    for a in mutated:
        room_id = a['room']['id']
        room_usage[room_id] = room_usage.get(room_id, 0) + 1
    
    if room_usage:
        avg_usage = sum(room_usage.values()) / len(room_usage)
        overloaded = [r for r, u in room_usage.items() if u > avg_usage * 1.3]
        underused = [r for r in [room['id'] for room in room_list] if room_usage.get(r, 0) < avg_usage * 0.7]
    else:
        overloaded = []
        underused = []
    
    for assignment in mutated:
        current_room = assignment['room']['id']
        effective_rate = mutation_rate * 2 if current_room in overloaded else mutation_rate
        
        if random.random() < effective_rate:
            current_type = assignment['room'].get('type', 'aula')
            
            compatible_underused = [r for r in room_list if r['id'] in underused and (r['type'] == current_type or r['type'] == 'aula')]
            
            if compatible_underused and random.random() < 0.7:
                new_room = random.choice(compatible_underused)
            else:
                compatible_rooms = [r for r in room_list if r['type'] == current_type or r['type'] == 'aula']
                if compatible_rooms:
                    new_room = random.choice(compatible_rooms)
                else:
                    continue
            
            assignment['room'] = {'id': new_room['id'], 'type': new_room['type']}
    
    return mutated


def _evaluate_fitness(assignments: list, room_list: list, config) -> float:
    # Evalúa calidad de solución.
    if not assignments:
        return 0.0
    
    fitness = 1000.0
    
    # Equilibrio de uso de aulas
    room_usage = {}
    for a in assignments:
        room_id = a['room']['id']
        room_usage[room_id] = room_usage.get(room_id, 0) + len(a.get('schedule', []))
    
    all_rooms = [r['id'] for r in room_list]
    for room_id in all_rooms:
        if room_id not in room_usage:
            room_usage[room_id] = 0
    
    if room_usage:
        usages = list(room_usage.values())
        avg_usage = sum(usages) / len(usages)
        variance = sum((u - avg_usage) ** 2 for u in usages) / len(usages)
        std_dev = variance ** 0.5
        
        fitness -= std_dev * 5
        empty_rooms = sum(1 for u in usages if u == 0)
        fitness -= empty_rooms * 20
        
        if std_dev < avg_usage * 0.2:
            fitness += 50
    
    # Conflictos
    room_slots = {}
    for a in assignments:
        room_id = a['room']['id']
        for slot in a.get('schedule', []):
            key = (room_id, slot.get('day', ''), slot.get('block', 0))
            if key in room_slots:
                fitness -= 100
            room_slots[key] = True
    
    fitness += len(assignments) * 2
    
    return max(0, fitness)


def _calculate_room_usage(assignments: list) -> dict:
    # Estadísticas de uso de aulas.
    room_usage = {}
    for a in assignments:
        room_id = a['room']['id']
        slots = len(a.get('schedule', []))
        room_usage[room_id] = room_usage.get(room_id, 0) + slots
    
    if not room_usage:
        return {'total_rooms_used': 0, 'avg_usage': 0, 'std_dev': 0}
    
    usages = list(room_usage.values())
    avg = sum(usages) / len(usages)
    variance = sum((u - avg) ** 2 for u in usages) / len(usages)
    std_dev = variance ** 0.5
    
    return {
        'total_rooms_used': len(room_usage),
        'avg_usage': round(avg, 2),
        'std_dev': round(std_dev, 2),
        'min_usage': min(usages),
        'max_usage': max(usages),
        'distribution': room_usage
    }


# =================
# API ENDPOINTS
# =================

@csrf_exempt
@require_http_methods(["GET"])
def list_datasets(request):
    # Lista los datasets disponibles para generación.
    datasets = []
    
    for filename in ['escuela.xml', 'purdue_clean.xml', 'datos_horarios_pequeno.xml']:
        filepath = get_dataset_path(filename)
        if os.path.exists(filepath):
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
    
    return JsonResponse({
        'success': True,
        'datasets': datasets
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_constraints(request):
    # Obtiene las restricciones por defecto configurables.
    return JsonResponse({
        'success': True,
        'constraints': DEFAULT_CONSTRAINTS,
        'description': {
            'aulas': {
                'max_classes_per_day': 'Máximo de clases por día en aulas normales (null = sin límite)',
                'max_classes_per_week': 'Máximo de clases por semana en aulas normales (null = sin límite)',
                'start_time': 'Hora de inicio de jornada para aulas (formato HH:MM)',
                'end_time': 'Hora de fin de jornada para aulas (formato HH:MM)',
            },
            'laboratorios': {
                'max_classes_per_day': 'Máximo de clases por día en laboratorios (null = sin límite)',
                'max_classes_per_week': 'Máximo de clases por semana en laboratorios (null = sin límite)',
                'start_time': 'Hora de inicio de jornada para labs (formato HH:MM)',
                'end_time': 'Hora de fin de jornada para labs (formato HH:MM)',
            },
            'general': {
                'max_consecutive_blocks': 'Máximo de bloques consecutivos para teoría/práctica',
                'max_consecutive_lab_blocks': 'Máximo de bloques consecutivos para laboratorio',
                'break_duration_minutes': 'Duración del descanso entre bloques en minutos',
                'block_duration_minutes': 'Duración de cada bloque en minutos',
            }
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def generate_schedule(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    
    dataset = data.get('dataset', 'escuela.xml')
    name = data.get('name', 'Horario Generado')
    population_size = int(data.get('population_size', 50))
    generations = int(data.get('generations', 100))
    constraints = data.get('constraints', None)
    
    # Validar parámetros
    population_size = max(20, min(500, population_size))
    generations = max(50, min(500, generations))
    
    xml_path = get_dataset_path(dataset)
    
    if not os.path.exists(xml_path):
        _ensure_datasets_exist()
        if not os.path.exists(xml_path):
            return JsonResponse({
                'success': False,
                'error': f'Dataset no encontrado: {dataset}'
            }, status=404)
    
    try:
        # Generar horario
        result = generate_with_genetic_algorithm(
            xml_path,
            population_size=population_size,
            generations=generations,
            constraints=constraints
        )
        
        result['name'] = name
        result['dataset'] = dataset
        result['population_size'] = population_size
        
        # Guardar en base de datos
        schedule = _save_schedule_to_db(result)
        result['id'] = schedule.id
        
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
    # Genera horario desde archivo subido.
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No se proporcionó archivo'
        }, status=400)
    
    uploaded_file = request.FILES['file']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in ['.xml', '.json']:
        return JsonResponse({
            'success': False,
            'error': 'Solo se aceptan archivos XML o JSON'
        }, status=400)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        if file_ext == '.json':
            xml_path = tmp_path.replace('.json', '.xml')
            json_to_xml(tmp_path, xml_path)
            tmp_path = xml_path
        
        population_size = int(request.POST.get('population_size', 50))
        generations = int(request.POST.get('generations', 100))
        
        # Parsear constraints si se envían
        constraints = None
        constraints_str = request.POST.get('constraints')
        if constraints_str:
            try:
                constraints = json.loads(constraints_str)
            except:
                pass
        
        result = generate_with_genetic_algorithm(
            tmp_path, 
            population_size, 
            generations,
            constraints=constraints
        )
        result['name'] = request.POST.get('name', uploaded_file.name)
        result['dataset'] = uploaded_file.name
        
        # Guardar en BD
        schedule = _save_schedule_to_db(result)
        result['id'] = schedule.id
        
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
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@csrf_exempt
@require_http_methods(["POST"])
def prepare_datasets(request):
    # Prepara/limpia los datasets.
    results = {}
    
    purdue_original = get_dataset_path('pu-fal07-llr.xml')
    purdue_clean_path = get_dataset_path('purdue_clean.xml')
    
    if os.path.exists(purdue_original):
        try:
            clean_purdue_xml(purdue_original, purdue_clean_path)
            results['purdue'] = 'limpiado'
        except Exception as e:
            results['purdue'] = f'error: {str(e)}'
    
    json_path = get_dataset_path('datos_horarios.json')
    escuela_path = get_dataset_path('escuela.xml')
    
    if os.path.exists(json_path) and not os.path.exists(escuela_path):
        try:
            json_to_xml(json_path, escuela_path)
            results['escuela'] = 'convertido'
        except Exception as e:
            results['escuela'] = f'error: {str(e)}'
    
    return JsonResponse({
        'success': True,
        'results': results
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_last_schedule(request):
    # Obtiene el último horario generado desde la BD.
    schedule = Schedule.objects.order_by('-created_at').first()
    
    if not schedule:
        return JsonResponse({
            'success': False,
            'error': 'No hay horarios generados'
        }, status=404)
    
    return JsonResponse({
        'success': True,
        'schedule': schedule.schedule_data
    })


@csrf_exempt
@require_http_methods(["GET"])
def list_saved_schedules(request):
    # Lista horarios guardados en la BD.
    schedules = Schedule.objects.order_by('-created_at')[:20]
    
    result = [{
        'id': s.id,
        'name': s.name,
        'dataset': s.dataset,
        'created_at': s.created_at.isoformat(),
        'fitness_score': s.fitness_score,
        'conflict_count': s.conflict_count,
        'classes_assigned': s.classes_assigned,
        'classes_total': s.classes_total,
        'generation_time_ms': s.generation_time_ms,
        'status': s.status
    } for s in schedules]
    
    return JsonResponse({
        'success': True,
        'schedules': result
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_saved_schedule(request, schedule_id):
    # Obtiene un horario guardado por ID.
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        return JsonResponse({
            'success': True,
            'schedule': schedule.schedule_data
        })
    except Schedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Horario {schedule_id} no encontrado'
        }, status=404)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_schedule(request, schedule_id):
    # Elimina un horario por ID.
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        schedule.delete()
        return JsonResponse({
            'success': True,
            'message': f'Horario {schedule_id} eliminado'
        })
    except Schedule.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Horario {schedule_id} no encontrado'
        }, status=404)
