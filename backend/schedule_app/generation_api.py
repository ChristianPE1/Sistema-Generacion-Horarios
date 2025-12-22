"""
API Views para generación de horarios con Algoritmo Constructivo/Genético.

Endpoints:
- POST /api/generate/from-xml/ - Genera horario desde archivo XML
- POST /api/generate/from-json/ - Genera horario desde archivo JSON  
- GET /api/datasets/ - Lista datasets disponibles (escuela.xml, purdue_clean.xml)
"""
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .schedule_builder import generate_from_xml, load_from_xml
from .xml_cleaner import clean_purdue_xml, json_to_xml

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        # Generar horario
        result = generate_from_xml(
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
