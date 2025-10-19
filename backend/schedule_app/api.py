"""
API REST para el frontend.
Endpoints para visualización de horarios y análisis.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .models import Schedule, ScheduleAssignment, Instructor, Room, Class
from .analysis import WorkloadAnalyzer, ConflictAnalyzer, RoomUtilizationAnalyzer
from collections import defaultdict


@api_view(['GET'])
def get_schedules_list(request):
    """
    Lista todos los horarios generados.
    
    GET /api/schedules/
    """
    schedules = Schedule.objects.all().order_by('-id')
    
    data = []
    for schedule in schedules:
        data.append({
            'id': schedule.id,
            'name': schedule.name,
            'description': schedule.description,
            'fitness_score': schedule.fitness_score,
            'is_active': schedule.is_active,
            'created_at': schedule.created_at.isoformat() if hasattr(schedule, 'created_at') else None,
            'total_assignments': schedule.assignments.count()
        })
    
    return Response(data)


@api_view(['GET'])
def get_schedule_calendar(request, schedule_id):
    """
    Retorna horario en formato FullCalendar.
    
    GET /api/schedules/<id>/calendar/
    
    Query params:
        - instructor_id: Filtrar por instructor
        - room_id: Filtrar por aula
        - offering_id: Filtrar por curso
    """
    schedule = get_object_or_404(Schedule, id=schedule_id)
    assignments = ScheduleAssignment.objects.filter(
        schedule=schedule
    ).select_related('class_obj__offering', 'room', 'time_slot')
    
    # Aplicar filtros
    instructor_id = request.GET.get('instructor_id')
    room_id = request.GET.get('room_id')
    offering_id = request.GET.get('offering_id')
    
    if instructor_id:
        assignments = assignments.filter(class_obj__instructors__id=instructor_id)
    if room_id:
        assignments = assignments.filter(room_id=room_id)
    if offering_id:
        assignments = assignments.filter(class_obj__offering_id=offering_id)
    
    events = []
    
    for assignment in assignments:
        if not assignment.time_slot:
            continue
        
        # Convertir timeslot a formato datetime
        event_data = _convert_assignment_to_event(assignment)
        if event_data:
            events.append(event_data)
    
    return Response({
        'schedule_id': schedule.id,
        'schedule_name': schedule.name,
        'fitness_score': schedule.fitness_score,
        'total_events': len(events),
        'events': events
    })


def _convert_assignment_to_event(assignment):
    """Convierte una asignación a formato FullCalendar"""
    ts = assignment.time_slot
    if not ts:
        return None
    
    # Decodificar días (bit string de 7 dígitos)
    days = ts.days
    active_days = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, bit in enumerate(days[:7]):
        if bit == '1':
            active_days.append(i)
    
    # Convertir slot a tiempo
    # slot * 5 minutos = tiempo desde medianoche
    start_minutes = ts.start_time * 5
    duration_minutes = ts.length * 5
    
    start_hour = start_minutes // 60
    start_minute = start_minutes % 60
    end_minutes = start_minutes + duration_minutes
    end_hour = end_minutes // 60
    end_minute = end_minutes % 60
    
    # Obtener información del instructor
    instructors = assignment.class_obj.instructors.all()
    instructor_names = [inst.name for inst in instructors]
    
    # Determinar color basado en conflictos
    background_color = '#28a745'  # Verde por defecto
    
    # Si tiene problemas de capacidad
    if assignment.room and assignment.room.capacity < assignment.class_obj.class_limit:
        background_color = '#ffc107'  # Amarillo
    
    # Obtener nombre del curso
    course_name = "Sin nombre"
    if assignment.class_obj.offering:
        course_name = assignment.class_obj.offering.name or assignment.class_obj.offering.code or f"Curso {assignment.class_obj.offering.id}"
    
    # Crear eventos para cada día
    events = []
    
    # Usar una fecha base (lunes de esta semana)
    base_date = datetime.now().date()
    base_date -= timedelta(days=base_date.weekday())  # Ir al lunes
    
    for day_index in active_days:
        event_date = base_date + timedelta(days=day_index)
        
        events.append({
            'id': f"{assignment.id}_{day_index}",
            'assignment_id': assignment.id,
            'title': f"{course_name}",
            'start': f"{event_date}T{start_hour:02d}:{start_minute:02d}:00",
            'end': f"{event_date}T{end_hour:02d}:{end_minute:02d}:00",
            'backgroundColor': background_color,
            'borderColor': background_color,
            'extendedProps': {
                'class_id': assignment.class_obj.id,
                'class_limit': assignment.class_obj.class_limit,
                'offering_id': assignment.class_obj.offering_id,
                'room_id': assignment.room.id if assignment.room else None,
                'room_name': f"Aula {assignment.room.id}" if assignment.room else "Sin aula",
                'room_capacity': assignment.room.capacity if assignment.room else 0,
                'instructors': instructor_names,
                'time_slot_id': ts.id,
                'days': days,
                'has_capacity_issue': assignment.room.capacity < assignment.class_obj.class_limit if assignment.room else False
            }
        })
    
    return events if len(events) == 1 else events


@api_view(['GET'])
def get_workload_analysis(request):
    """
    Análisis de carga de trabajo de instructores.
    
    GET /api/analysis/workload/
    """
    analyzer = WorkloadAnalyzer()
    data = analyzer.analyze_instructor_workload()
    
    return Response(data)


@api_view(['GET'])
def get_instructor_schedule(request, instructor_id):
    """
    Horario específico de un instructor.
    
    GET /api/instructors/<id>/schedule/
    
    Query params:
        - schedule_id: ID del horario (opcional)
    """
    schedule_id = request.GET.get('schedule_id')
    
    analyzer = WorkloadAnalyzer()
    data = analyzer.get_instructor_schedule(
        instructor_id=instructor_id,
        schedule_id=int(schedule_id) if schedule_id else None
    )
    
    return Response(data)


@api_view(['GET'])
def get_conflict_analysis(request, schedule_id):
    """
    Análisis de conflictos en un horario.
    
    GET /api/schedules/<id>/conflicts/
    """
    analyzer = ConflictAnalyzer()
    data = analyzer.analyze_schedule_conflicts(schedule_id)
    
    return Response(data)


@api_view(['GET'])
def get_room_utilization(request, schedule_id):
    """
    Análisis de utilización de aulas.
    
    GET /api/schedules/<id>/rooms/
    """
    analyzer = RoomUtilizationAnalyzer()
    data = analyzer.analyze_room_utilization(schedule_id)
    
    return Response(data)


@api_view(['GET'])
def get_instructors_list(request):
    """
    Lista todos los instructores.
    
    GET /api/instructors/
    """
    instructors = Instructor.objects.all().order_by('name')
    
    data = []
    for instructor in instructors:
        class_count = instructor.classes.count()
        
        data.append({
            'id': instructor.id,
            'name': instructor.name,
            'email': instructor.email,
            'xml_id': instructor.xml_id,
            'is_synthetic': instructor.xml_id >= 900000,
            'class_count': class_count
        })
    
    return Response(data)


@api_view(['GET'])
def get_rooms_list(request):
    """
    Lista todas las aulas.
    
    GET /api/rooms/
    """
    rooms = Room.objects.all().order_by('id')
    
    data = []
    for room in rooms:
        data.append({
            'id': room.id,
            'capacity': room.capacity,
            'location': room.location if hasattr(room, 'location') else None
        })
    
    return Response(data)


@api_view(['GET'])
def get_dashboard_stats(request):
    """
    Estadísticas generales para el dashboard.
    
    GET /api/dashboard/stats/
    """
    latest_schedule = Schedule.objects.order_by('-id').first()
    
    if not latest_schedule:
        return Response({'error': 'No hay horarios generados'}, status=status.HTTP_404_NOT_FOUND)
    
    # Análisis de carga
    workload_analyzer = WorkloadAnalyzer()
    workload_data = workload_analyzer.analyze_instructor_workload()
    
    # Análisis de conflictos
    conflict_analyzer = ConflictAnalyzer()
    conflict_data = conflict_analyzer.analyze_schedule_conflicts(latest_schedule.id)
    
    # Análisis de aulas
    room_analyzer = RoomUtilizationAnalyzer()
    room_data = room_analyzer.analyze_room_utilization(latest_schedule.id)
    
    return Response({
        'schedule': {
            'id': latest_schedule.id,
            'name': latest_schedule.name,
            'fitness_score': latest_schedule.fitness_score,
            'total_assignments': latest_schedule.assignments.count()
        },
        'instructors': {
            'total': workload_data['total_instructors'],
            'avg_load': round(workload_data['avg_load'], 1),
            'overloaded': len(workload_data['overloaded']),
            'synthetic': len(workload_data['synthetic'])
        },
        'conflicts': {
            'total': conflict_data['total_conflicts'],
            'room_conflicts': len(conflict_data['room_conflicts']),
            'capacity_issues': len(conflict_data['capacity_issues'])
        },
        'rooms': {
            'total': room_data['total_rooms'],
            'used': room_data['used_rooms'],
            'unused': room_data['unused_rooms'],
            'avg_utilization': round(room_data['avg_utilization'], 1)
        }
    })


@api_view(['GET'])
def get_schedule_timetable(request, schedule_id):
    """
    Retorna horario en formato TABLA (como horario escolar tradicional).
    
    GET /api/schedules/<id>/timetable/
    
    Formato de respuesta:
    {
        "schedule": {...},
        "timetable": {
            "Lunes": {
                "08:00-09:00": [
                    {
                        "class_name": "Matemáticas I",
                        "room": "A-101",
                        "instructor": "Dr. Smith",
                        "students": 45
                    }
                ]
            }
        },
        "time_range": ["07:00", "08:00", "09:00", ...],
        "days": ["Lunes", "Martes", ...]
    }
    """
    schedule = get_object_or_404(Schedule, id=schedule_id)
    assignments = ScheduleAssignment.objects.filter(
        schedule=schedule
    ).select_related(
        'class_obj__offering',
        'room',
        'time_slot'
    ).prefetch_related(
        'class_obj__instructors'
    )
    
    # Nombres de días
    day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    # Estructura: {dia: {hora: [clases]}}
    timetable = {day: {} for day in day_names}
    all_hours = set()
    
    for assignment in assignments:
        if not assignment.time_slot:
            continue
            
        ts = assignment.time_slot
        class_obj = assignment.class_obj
        room = assignment.room
        
        # Decodificar días (bit string: "0101000" = Mar/Jue)
        days_bits = ts.days[:7] if len(ts.days) >= 7 else ts.days.ljust(7, '0')
        
        # Calcular hora de inicio y fin
        start_minutes = ts.start_time * 5  # slots de 5 minutos
        duration_minutes = ts.length * 5
        
        start_hour = start_minutes // 60
        start_min = start_minutes % 60
        start_time = f"{start_hour:02d}:{start_min:02d}"
        
        end_minutes = start_minutes + duration_minutes
        end_hour = end_minutes // 60
        end_min = end_minutes % 60
        end_time = f"{end_hour:02d}:{end_min:02d}"
        
        time_label = f"{start_time}-{end_time}"
        all_hours.add(start_time)
        
        # Obtener instructores (a través de ClassInstructor - relación many-to-many)
        class_instructors = class_obj.instructors.all()  # Devuelve ClassInstructor objects
        instructor_names = [ci.instructor.name for ci in class_instructors] if class_instructors else ["Sin instructor"]
        
        # Información de la clase
        class_info = {
            'id': class_obj.id,
            'xml_id': class_obj.xml_id,
            'name': class_obj.offering.name if class_obj.offering else f"Clase {class_obj.xml_id}",
            'code': class_obj.offering.code if class_obj.offering else "N/A",
            'instructors': instructor_names,
            'room': room.location if room else "Sin aula",
            'room_capacity': room.capacity if room else 0,
            'students': class_obj.enrolled_students.count(),
            'limit': class_obj.class_limit,
            'time': time_label,
            'start': start_time,
            'end': end_time,
            'duration_min': duration_minutes
        }
        
        # Agregar a cada día activo
        for day_idx, bit in enumerate(days_bits):
            if bit == '1' and day_idx < 7:
                day_name = day_names[day_idx]
                
                if time_label not in timetable[day_name]:
                    timetable[day_name][time_label] = []
                    
                timetable[day_name][time_label].append(class_info)
    
    # Ordenar horas
    sorted_hours = sorted(list(all_hours))
    
    # Generar rangos de hora completos
    time_ranges = []
    for hour_str in sorted_hours:
        hour = int(hour_str.split(':')[0])
        for slot in range(0, 60, 30):  # Intervalos de 30 min
            time_ranges.append(f"{hour:02d}:{slot:02d}")
    
    # Estadísticas
    total_slots = sum(len(times) for day_times in timetable.values() for times in day_times.values())
    max_concurrent = max(
        (len(classes) for day in timetable.values() for classes in day.values()),
        default=0
    )
    
    # Calcular clases por día para stats
    classes_by_day = {}
    for day in day_names:
        classes_by_day[day] = sum(len(classes) for classes in timetable[day].values())
    
    return Response({
        'schedule': {
            'id': schedule.id,
            'name': schedule.name,
            'description': schedule.description or '',
            'fitness_score': schedule.fitness_score,
            'total_assignments': assignments.count()
        },
        'grid': timetable,
        'days': day_names,
        'time_slots': sorted_hours,
        'classes': [],  # Lista plana si se necesita
        'stats': {
            'total_classes': assignments.count(),
            'classes_by_day': classes_by_day,
            'max_concurrent_classes': max_concurrent,
            'needs_multiple_views': max_concurrent > 10
        }
    })
