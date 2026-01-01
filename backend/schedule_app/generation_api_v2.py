"""
API Views para generación de horarios.
Sistema Híbrido: Greedy (inicialización) + Algoritmo Genético (refinamiento obligatorio).
"""
import os
import json
import time
import random
import copy
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .schedule_builder import generate_from_xml, load_from_xml
from .xml_cleaner import clean_purdue_xml, json_to_xml

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Archivo para guardar historial de horarios
SCHEDULES_HISTORY_FILE = os.path.join(BASE_DIR, 'schedules_history.json')


def get_dataset_path(name: str) -> str:
    """Obtiene la ruta completa de un dataset."""
    return os.path.join(BASE_DIR, name)


def _load_schedules_history() -> list:
    """Carga el historial de horarios generados."""
    if os.path.exists(SCHEDULES_HISTORY_FILE):
        try:
            with open(SCHEDULES_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def _save_schedule_to_history(schedule: dict) -> int:
    """Guarda un horario en el historial y retorna su ID."""
    history = _load_schedules_history()
    
    # Generar nuevo ID
    new_id = max([s.get('id', 0) for s in history], default=0) + 1
    
    # Agregar metadatos
    schedule_entry = {
        'id': new_id,
        'name': schedule.get('name', f'Horario {new_id}'),
        'dataset': schedule.get('dataset', 'unknown'),
        'created_at': datetime.now().isoformat(),
        'fitness_score': schedule.get('fitness_score', 0),
        'conflict_count': schedule.get('conflict_count', 0),
        'classes_assigned': schedule.get('classes_assigned', 0),
        'classes_total': schedule.get('classes_total', 0),
        'algorithm': schedule.get('algorithm', 'greedy+genetic'),
        'generation_time_ms': schedule.get('generation_time_ms', 0),
        'generations_run': schedule.get('generations_run', 0),
        'population_size': schedule.get('population_size', 0),
        'schedule_data': schedule  # Datos completos
    }
    
    # Agregar al inicio del historial (más recientes primero)
    history.insert(0, schedule_entry)
    
    # Mantener solo los últimos 20 horarios
    history = history[:20]
    
    # Guardar
    with open(SCHEDULES_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return new_id


def _ensure_datasets_exist():
    """Asegura que los datasets necesarios existan."""
    purdue_clean_path = get_dataset_path('purdue_clean.xml')
    purdue_original = get_dataset_path('pu-fal07-llr.xml')
    
    if not os.path.exists(purdue_clean_path) and os.path.exists(purdue_original):
        try:
            clean_purdue_xml(purdue_original, purdue_clean_path)
        except Exception as e:
            print(f"Error limpiando Purdue XML: {e}")


# =============================================================================
# ALGORITMO GENÉTICO - IMPLEMENTACIÓN COMPLETA
# =============================================================================

def generate_with_genetic_algorithm(xml_path: str, population_size: int = 50, 
                                    generations: int = 100) -> dict:
    """
    Sistema Híbrido: Greedy + Algoritmo Genético.
    
    FASE 1 - GREEDY (Inicialización inteligente):
    - Genera una solución inicial válida y de buena calidad
    - Asigna clases a aulas respetando restricciones
    
    FASE 2 - ALGORITMO GENÉTICO (Refinamiento obligatorio):
    - Crea población inicial basada en la solución greedy
    - Aplica operadores genéticos: selección, cruce, mutación
    - Optimiza distribución de aulas para equilibrio de uso
    - Siempre se ejecuta para justificar su uso en el trabajo
    """
    start_time = time.time()
    
    # =========================================================================
    # FASE 1: INICIALIZACIÓN GREEDY
    # =========================================================================
    greedy_result = generate_from_xml(xml_path)
    
    if not greedy_result['assignments']:
        greedy_result['algorithm'] = 'greedy (sin refinamiento - sin asignaciones)'
        return greedy_result
    
    # Cargar datos para el AG
    rooms, instructors, classes, config = load_from_xml(xml_path)
    room_list = [{'id': r.id, 'type': r.room_type, 'capacity': r.capacity} for r in rooms]
    room_map = {r.id: r for r in rooms}
    
    greedy_fitness = _evaluate_fitness(greedy_result['assignments'], room_list, config)
    greedy_time = time.time() - start_time
    
    # =========================================================================
    # FASE 2: ALGORITMO GENÉTICO (SIEMPRE SE EJECUTA)
    # =========================================================================
    ga_start = time.time()
    
    # Crear población inicial basada en mutaciones de la solución greedy
    population = []
    base_assignments = greedy_result['assignments']
    
    # El primer individuo es la solución greedy original
    population.append({
        'assignments': copy.deepcopy(base_assignments),
        'fitness': greedy_fitness
    })
    
    # Generar resto de la población con variaciones
    for i in range(population_size - 1):
        mutated = _create_mutant(base_assignments, room_list, mutation_rate=0.1 + (i * 0.01))
        fitness = _evaluate_fitness(mutated, room_list, config)
        population.append({
            'assignments': mutated,
            'fitness': fitness
        })
    
    # Tracking de evolución
    best_individual = max(population, key=lambda x: x['fitness'])
    best_fitness = best_individual['fitness']
    best_assignments = copy.deepcopy(best_individual['assignments'])
    
    initial_best = best_fitness
    generations_without_improvement = 0
    final_gen = 0
    
    # =========================================================================
    # LOOP EVOLUTIVO PRINCIPAL
    # =========================================================================
    for gen in range(generations):
        final_gen = gen
        
        # Ordenar población por fitness
        population.sort(key=lambda x: -x['fitness'])
        
        # ELITISMO: Mantener los mejores individuos
        elite_count = max(2, population_size // 10)
        new_population = population[:elite_count]
        
        # Generar nuevos individuos
        while len(new_population) < population_size:
            # SELECCIÓN POR TORNEO
            parent1 = _tournament_selection(population, tournament_size=3)
            parent2 = _tournament_selection(population, tournament_size=3)
            
            # CRUCE
            if random.random() < 0.7:  # 70% probabilidad de cruce
                child_assignments = _crossover(
                    parent1['assignments'], 
                    parent2['assignments'],
                    room_list
                )
            else:
                child_assignments = copy.deepcopy(parent1['assignments'])
            
            # MUTACIÓN
            mutation_rate = 0.15 + (0.1 * (generations_without_improvement / 20))
            mutation_rate = min(0.4, mutation_rate)  # Cap at 40%
            
            child_assignments = _mutate(child_assignments, room_list, mutation_rate)
            
            # Evaluar fitness del hijo
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
        
        # Criterio de parada temprana si no hay mejora en 30 generaciones
        if generations_without_improvement >= 30 and gen > generations // 2:
            break
    
    ga_time = time.time() - ga_start
    total_time = time.time() - start_time
    
    # Calcular mejora del AG sobre greedy
    improvement = ((best_fitness - greedy_fitness) / max(greedy_fitness, 1)) * 100
    
    # Calcular estadísticas de distribución de aulas
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
    """Crea una copia mutada de las asignaciones."""
    mutated = copy.deepcopy(assignments)
    
    for assignment in mutated:
        if random.random() < mutation_rate:
            # Encontrar aulas compatibles (mismo tipo o aula genérica)
            current_type = assignment['room'].get('type', 'aula')
            compatible_rooms = [r for r in room_list if r['type'] == current_type or r['type'] == 'aula']
            
            if compatible_rooms:
                new_room = random.choice(compatible_rooms)
                assignment['room'] = {'id': new_room['id'], 'type': new_room['type']}
    
    return mutated


def _tournament_selection(population: list, tournament_size: int = 3) -> dict:
    """Selección por torneo."""
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda x: x['fitness'])


def _crossover(parent1_assignments: list, parent2_assignments: list, room_list: list) -> list:
    """
    Cruce de dos puntos: combina asignaciones de aulas de ambos padres.
    """
    if len(parent1_assignments) <= 2:
        return copy.deepcopy(parent1_assignments)
    
    child = copy.deepcopy(parent1_assignments)
    
    # Determinar puntos de cruce
    size = len(child)
    point1 = random.randint(0, size // 2)
    point2 = random.randint(size // 2, size - 1)
    
    # Tomar asignaciones de aulas del parent2 en el rango [point1, point2]
    for i in range(point1, min(point2 + 1, len(parent2_assignments))):
        if i < len(child):
            # Copiar solo la asignación de aula, mantener el resto
            child[i]['room'] = copy.deepcopy(parent2_assignments[i]['room'])
    
    return child


def _mutate(assignments: list, room_list: list, mutation_rate: float = 0.15) -> list:
    """
    Mutación: cambiar aulas de algunas asignaciones para mejorar equilibrio.
    """
    mutated = copy.deepcopy(assignments)
    
    # Calcular uso actual de aulas
    room_usage = {}
    for a in mutated:
        room_id = a['room']['id']
        room_usage[room_id] = room_usage.get(room_id, 0) + 1
    
    # Identificar aulas sobrecargadas y subutilizadas
    if room_usage:
        avg_usage = sum(room_usage.values()) / len(room_usage)
        overloaded = [r for r, u in room_usage.items() if u > avg_usage * 1.3]
        underused = [r for r in [room['id'] for room in room_list] if room_usage.get(r, 0) < avg_usage * 0.7]
    else:
        overloaded = []
        underused = []
    
    for assignment in mutated:
        current_room = assignment['room']['id']
        
        # Mayor probabilidad de mutar si el aula está sobrecargada
        effective_rate = mutation_rate * 2 if current_room in overloaded else mutation_rate
        
        if random.random() < effective_rate:
            current_type = assignment['room'].get('type', 'aula')
            
            # Preferir aulas subutilizadas del mismo tipo
            compatible_underused = [r for r in room_list 
                                   if r['id'] in underused and 
                                   (r['type'] == current_type or r['type'] == 'aula')]
            
            if compatible_underused and random.random() < 0.7:
                new_room = random.choice(compatible_underused)
            else:
                compatible_rooms = [r for r in room_list 
                                   if r['type'] == current_type or r['type'] == 'aula']
                if compatible_rooms:
                    new_room = random.choice(compatible_rooms)
                else:
                    continue
            
            assignment['room'] = {'id': new_room['id'], 'type': new_room['type']}
    
    return mutated


def _evaluate_fitness(assignments: list, room_list: list, config) -> float:
    """
    Función de fitness que evalúa la calidad de una solución.
    
    Criterios:
    - Equilibrio en uso de aulas (objetivo principal)
    - Penalización por conflictos
    - Bonus por distribución uniforme
    """
    if not assignments:
        return 0.0
    
    fitness = 1000.0
    
    # 1. EQUILIBRIO DE USO DE AULAS (objetivo principal del AG)
    room_usage = {}
    for a in assignments:
        room_id = a['room']['id']
        room_usage[room_id] = room_usage.get(room_id, 0) + len(a.get('schedule', []))
    
    # Todas las aulas disponibles
    all_rooms = [r['id'] for r in room_list]
    for room_id in all_rooms:
        if room_id not in room_usage:
            room_usage[room_id] = 0
    
    if room_usage:
        usages = list(room_usage.values())
        avg_usage = sum(usages) / len(usages)
        
        # Calcular desviación estándar
        variance = sum((u - avg_usage) ** 2 for u in usages) / len(usages)
        std_dev = variance ** 0.5
        
        # Penalizar alta desviación (queremos uso uniforme)
        fitness -= std_dev * 5
        
        # Penalizar aulas vacías
        empty_rooms = sum(1 for u in usages if u == 0)
        fitness -= empty_rooms * 20
        
        # Bonus por buena distribución
        if std_dev < avg_usage * 0.2:
            fitness += 50  # Bonus por distribución muy uniforme
    
    # 2. CONFLICTOS DE AULA (misma aula, mismo slot)
    room_slots = {}
    for a in assignments:
        room_id = a['room']['id']
        for slot in a.get('schedule', []):
            key = (room_id, slot.get('day', ''), slot.get('block', 0))
            if key in room_slots:
                fitness -= 100  # Penalización fuerte por conflicto
            room_slots[key] = True
    
    # 3. BONUS POR CLASES ASIGNADAS
    fitness += len(assignments) * 2
    
    return max(0, fitness)


def _calculate_room_usage(assignments: list) -> dict:
    """Calcula estadísticas de uso de aulas."""
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


# =============================================================================
# API ENDPOINTS
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def list_datasets(request):
    """Lista los datasets disponibles para generación."""
    datasets = []
    
    for filename in ['escuela.xml', 'purdue_clean.xml','datos_horarios_pequeno.xml']:
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
@require_http_methods(["POST"])
def generate_schedule(request):
    """
    Genera un horario usando el Sistema Híbrido: Greedy + Algoritmo Genético.
    
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
    
    # Validar parámetros (mínimos para que el AG funcione)
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
        # Generar horario con sistema híbrido
        result = generate_with_genetic_algorithm(
            xml_path,
            population_size=population_size,
            generations=generations
        )
        
        result['name'] = name
        result['dataset'] = dataset
        result['population_size'] = population_size
        
        # Guardar en historial
        schedule_id = _save_schedule_to_history(result)
        result['id'] = schedule_id
        
        # Guardar como último horario
        output_path = get_dataset_path('ultimo_horario.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
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
    """Genera horario desde archivo subido."""
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
        
        result = generate_with_genetic_algorithm(tmp_path, population_size, generations)
        result['name'] = request.POST.get('name', uploaded_file.name)
        
        schedule_id = _save_schedule_to_history(result)
        result['id'] = schedule_id
        
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
    """Prepara/limpia los datasets."""
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
    """Obtiene el último horario generado."""
    output_path = get_dataset_path('ultimo_horario.json')
    
    if not os.path.exists(output_path):
        return JsonResponse({
            'success': False,
            'error': 'No hay horario generado'
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
    """Lista horarios guardados en el historial."""
    history = _load_schedules_history()
    
    # Retornar solo metadatos, no los datos completos
    schedules = [{
        'id': s['id'],
        'name': s['name'],
        'dataset': s['dataset'],
        'created_at': s['created_at'],
        'fitness_score': s['fitness_score'],
        'conflict_count': s['conflict_count'],
        'classes_assigned': s['classes_assigned'],
        'classes_total': s.get('classes_total', 0),
        'generation_time_ms': s.get('generation_time_ms', 0),
        'status': s.get('status', 'completed')
    } for s in history]
    
    return JsonResponse({
        'success': True,
        'schedules': schedules
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_saved_schedule(request, schedule_id):
    """Obtiene un horario guardado por ID."""
    history = _load_schedules_history()
    
    for s in history:
        if s['id'] == int(schedule_id):
            return JsonResponse({
                'success': True,
                'schedule': s['schedule_data']
            })
    
    return JsonResponse({
        'success': False,
        'error': f'Horario {schedule_id} no encontrado'
    }, status=404)
