"""
API Views optimizadas para generación rápida de horarios.
Incluye endpoints para generación directa desde archivos sin cargar a BD.
"""

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import json
import tempfile
import uuid
from typing import Dict, Any
from .direct_generator import (
    DirectScheduleGenerator,
    generate_from_json_file,
    generate_from_xml_file
)
from .json_to_xml_converter import convert_json_to_xml


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def generate_from_file(request):
    """
    Genera horario directamente desde archivo JSON/XML sin cargar a BD.
    Optimizado para velocidad máxima.
    
    POST /api/schedules/generate-from-file/
    
    Form data:
        - file: Archivo JSON o XML
        - use_genetic: bool (opcional, default=False) - Usar algoritmo genético
        - save_to_db: bool (opcional, default=False) - Guardar resultado en BD
        
    Returns:
        JSON con asignaciones y estadísticas
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No se proporcionó archivo'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    use_genetic = request.POST.get('use_genetic', 'false').lower() == 'true'
    save_to_db = request.POST.get('save_to_db', 'false').lower() == 'true'
    
    # Validar extensión
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in ['.json', '.xml']:
        return Response(
            {'error': 'Solo se aceptan archivos .json o .xml'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext, delete=False) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # Generar horario
        if file_ext == '.json':
            asignaciones, stats = generate_from_json_file(temp_path)
        else:
            asignaciones, stats = generate_from_xml_file(temp_path)
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        # Convertir asignaciones a formato JSON serializable
        dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        generator = DirectScheduleGenerator()
        if file_ext == '.json':
            generator.load_from_json(temp_path if os.path.exists(temp_path) else uploaded_file)
        
        result_asignaciones = []
        for asig in asignaciones:
            dias = [dias_nombre[i] for i, d in enumerate(asig.time_slot.dias) if d == '1']
            
            # Calcular hora fin
            inicio_slot = asig.time_slot.hora_inicio
            fin_slot = inicio_slot + asig.time_slot.duracion
            
            result_asignaciones.append({
                'curso_codigo': asig.curso_codigo,
                'sala_id': asig.sala_id,
                'profesor_id': asig.profesor_id,
                'dias': dias,
                'hora_inicio': _slot_to_time(inicio_slot),
                'hora_fin': _slot_to_time(fin_slot),
                'duracion_minutos': asig.time_slot.duracion * 5,
                'num_bloques': asig.time_slot.num_bloques,
                'duracion_bloque_min': asig.time_slot.duracion_bloque_min
            })
        
        response_data = {
            'success': True,
            'asignaciones': result_asignaciones,
            'estadisticas': stats,
            'mensaje': f"Horario generado exitosamente en {stats['tiempo_ms']}ms"
        }
        
        # Si se solicita guardar en BD, hacerlo aquí
        if save_to_db:
            # TODO: Implementar guardado en BD si es necesario
            response_data['guardado_bd'] = False
            response_data['mensaje'] += ' (no guardado en BD)'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Limpiar archivo temporal si existe
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return Response(
            {'error': f'Error al generar horario: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([JSONParser])
def generate_from_json_data(request):
    """
    Genera horario directamente desde datos JSON en el body (sin archivo).
    Útil para datos que vienen de un bucket o API externa.
    
    POST /api/schedules/generate-from-data/
    
    Body (JSON):
        {
            "cursos": [...],
            "profesores": [...],
            "salas": [...],
            "configuracion_general": {...}
        }
        
    Returns:
        JSON con asignaciones y estadísticas
    """
    try:
        data = request.data
        
        # Validar que tenga los campos necesarios
        if 'cursos' not in data or 'salas' not in data:
            return Response(
                {'error': 'Faltan campos requeridos: cursos, salas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear archivo temporal con los datos
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(data, temp_file)
            temp_path = temp_file.name
        
        # Generar horario
        asignaciones, stats = generate_from_json_file(temp_path)
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        # Convertir a formato serializable
        dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        result_asignaciones = []
        for asig in asignaciones:
            dias = [dias_nombre[i] for i, d in enumerate(asig.time_slot.dias) if d == '1']
            
            result_asignaciones.append({
                'curso_codigo': asig.curso_codigo,
                'sala_id': asig.sala_id,
                'profesor_id': asig.profesor_id,
                'dias': dias,
                'hora_inicio': _slot_to_time(asig.time_slot.hora_inicio),
                'hora_fin': _slot_to_time(asig.time_slot.hora_inicio + asig.time_slot.duracion),
                'duracion_minutos': asig.time_slot.duracion * 5,
                'num_bloques': asig.time_slot.num_bloques,
                'duracion_bloque_min': asig.time_slot.duracion_bloque_min
            })
        
        return Response({
            'success': True,
            'asignaciones': result_asignaciones,
            'estadisticas': stats,
            'mensaje': f"Horario generado en {stats['tiempo_ms']}ms"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Limpiar temporal si existe
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return Response(
            {'error': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def convert_json_to_xml_endpoint(request):
    """
    Convierte archivo JSON a XML formato Purdue.
    
    POST /api/schedules/convert-json-to-xml/
    
    Form data:
        - file: Archivo JSON
        
    Returns:
        Archivo XML descargable
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No se proporcionó archivo'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    
    try:
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as temp_json:
            for chunk in uploaded_file.chunks():
                temp_json.write(chunk)
            temp_json_path = temp_json.name
        
        # Convertir
        temp_xml_path = temp_json_path.replace('.json', '.xml')
        xml_content = convert_json_to_xml(temp_json_path, temp_xml_path)
        
        # Leer XML generado
        with open(temp_xml_path, 'r', encoding='utf-8') as f:
            xml_data = f.read()
        
        # Limpiar archivos temporales
        os.unlink(temp_json_path)
        os.unlink(temp_xml_path)
        
        # Retornar XML como respuesta
        from django.http import HttpResponse
        response = HttpResponse(xml_data, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{uploaded_file.name.replace(".json", ".xml")}"'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return Response(
            {'error': f'Error en conversión: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def check_generation_status(request, task_id):
    """
    Verifica el estado de una generación en progreso.
    
    GET /api/schedules/generation-status/<task_id>/
    
    Returns:
        JSON con estado y progreso
    """
    # Buscar en cache
    status_data = cache.get(f'generation_status_{task_id}')
    
    if not status_data:
        return Response(
            {'error': 'Tarea no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response(status_data, status=status.HTTP_200_OK)


def _slot_to_time(slot: int, inicio_jornada: str = '07:00') -> str:
    """Helper para convertir slot a HH:MM"""
    from datetime import datetime, timedelta
    inicio = datetime.strptime(inicio_jornada, '%H:%M')
    tiempo = inicio + timedelta(minutes=slot * 5)
    return tiempo.strftime('%H:%M')
