from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.db.models import Avg, Max
from .models import (
    Room, Instructor, Course, Class, ClassInstructor,
    ClassRoom, TimeSlot, Student, StudentClass,
    Schedule, ScheduleAssignment
)
from .serializers import (
    RoomSerializer, InstructorSerializer, CourseSerializer,
    ClassSerializer, ClassListSerializer, StudentSerializer,
    StudentClassSerializer, ScheduleSerializer, ScheduleListSerializer,
    TimeSlotSerializer, ClassInstructorSerializer, ClassRoomSerializer
)
from .schedule_generator import ScheduleGenerator
import threading


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para el sistema"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RoomViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar aulas"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Obtener asignaciones de una aula específica para FullCalendar"""
        room = self.get_object()
        
        # Obtener el último horario activo o el especificado
        schedule_id = request.query_params.get('schedule_id')
        if schedule_id:
            try:
                schedule = Schedule.objects.get(id=schedule_id)
            except Schedule.DoesNotExist:
                return Response(
                    {'error': 'Horario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            schedule = Schedule.objects.filter(is_active=True).first()
            if not schedule:
                schedule = Schedule.objects.order_by('-created_at').first()
        
        if not schedule:
            return Response([])
        
        # Obtener todas las asignaciones de esta aula en este horario
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule,
            room=room
        ).select_related(
            'class_obj__offering',
            'time_slot'
        ).prefetch_related('class_obj__instructors__instructor')
        
        # Dos clases en conflicto si: comparten al menos UN día Y horarios se solapan
        conflict_ids = set()
        assignments_list = list(assignments)
        
        def share_days(days1: str, days2: str) -> bool:
            """Verificar si dos cadenas de días comparten al menos un día activo"""
            for i in range(min(len(days1), len(days2))):
                if days1[i] == '1' and days2[i] == '1':
                    return True
            return False
        
        for i, a1 in enumerate(assignments_list):
            for a2 in assignments_list[i+1:]:
                ts1 = a1.time_slot
                ts2 = a2.time_slot
                
                # Verificar si comparten AL MENOS UN día
                if share_days(ts1.days, ts2.days):
                    # Verificar solapamiento temporal:
                    # ts1 empieza antes de que ts2 termine Y ts2 empieza antes de que ts1 termine
                    if (ts1.start_time < ts2.start_time + ts2.length and 
                        ts2.start_time < ts1.start_time + ts1.length):
                        conflict_ids.add(a1.id)
                        conflict_ids.add(a2.id)
        
        # Preparar datos para respuesta
        result = []
        for assignment in assignments_list:
            ts = assignment.time_slot
            has_conflict = assignment.id in conflict_ids
            
            # Obtener instructores
            instructors = [
                ci.instructor.name or f"Instructor {ci.instructor.xml_id}"
                for ci in assignment.class_obj.instructors.all()
            ]
            instructor_name = ', '.join(instructors) if instructors else 'Sin instructor'
            
            # Convertir start_time (slots de 5min) a minutos desde medianoche
            start_minutes = ts.start_time * 5
            length_minutes = ts.length * 5
            
            result.append({
                'id': assignment.id,
                'class_id': assignment.class_obj.xml_id,
                'class_name': assignment.class_obj.offering.name if assignment.class_obj.offering else f'Clase {assignment.class_obj.xml_id}',
                'room_id': room.xml_id,
                'instructor_name': instructor_name,
                'days': ts.days,
                'start_time': start_minutes,  # minutos desde medianoche
                'length': length_minutes,      # duración en minutos
                'student_count': assignment.class_obj.class_limit,
                'has_conflict': has_conflict
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de las aulas"""
        total = self.queryset.count()
        avg_capacity = self.queryset.aggregate(avg=Avg('capacity'))['avg']
        max_capacity = self.queryset.aggregate(max=Max('capacity'))['max']
        
        return Response({
            'total_rooms': total,
            'average_capacity': round(avg_capacity, 2) if avg_capacity else 0,
            'max_capacity': max_capacity or 0
        })


class InstructorViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar instructores"""
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """Obtener las clases de un instructor"""
        instructor = self.get_object()
        class_instructors = ClassInstructor.objects.filter(instructor=instructor)
        classes = [ci.class_obj for ci in class_instructors]
        serializer = ClassListSerializer(classes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de instructores"""
        total = self.queryset.count()
        with_classes = self.queryset.annotate(
            class_count=Count('classes')
        ).filter(class_count__gt=0).count()
        
        return Response({
            'total_instructors': total,
            'instructors_with_classes': with_classes,
            'instructors_without_classes': total - with_classes
        })


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar cursos"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """Obtener las clases de un curso"""
        course = self.get_object()
        classes = course.classes.all()
        serializer = ClassListSerializer(classes, many=True)
        return Response(serializer.data)


class ClassViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar clases"""
    queryset = Class.objects.select_related('offering', 'parent').prefetch_related(
        'instructors__instructor',
        'room_prefs__room',
        'time_slots',
        'enrolled_students'
    ).all()
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClassListSerializer
        return ClassSerializer
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Obtener los estudiantes de una clase"""
        class_obj = self.get_object()
        student_classes = StudentClass.objects.filter(class_obj=class_obj)
        serializer = StudentClassSerializer(student_classes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de clases"""
        total = self.queryset.count()
        committed = self.queryset.filter(committed=True).count()
        with_instructor = ClassInstructor.objects.values('class_obj').distinct().count()
        
        return Response({
            'total_classes': total,
            'committed_classes': committed,
            'classes_with_instructor': with_instructor
        })


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar estudiantes"""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """Obtener las clases de un estudiante"""
        student = self.get_object()
        student_classes = StudentClass.objects.filter(student=student)
        serializer = StudentClassSerializer(student_classes, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar horarios"""
    queryset = Schedule.objects.all()
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ScheduleListSerializer
        return ScheduleSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generar un nuevo horario usando algoritmo genético en segundo plano"""
        try:
            # Obtener parámetros del request
            name = request.data.get('name', f'Horario Generado')
            description = request.data.get('description', '')
            
            # Parámetros del algoritmo genético
            population_size = int(request.data.get('population_size', 100))
            generations = int(request.data.get('generations', 200))
            mutation_rate = float(request.data.get('mutation_rate', 0.1))
            crossover_rate = float(request.data.get('crossover_rate', 0.8))
            elitism_size = int(request.data.get('elitism_size', 5))
            tournament_size = int(request.data.get('tournament_size', 5))
            
            # Validar parámetros
            if not (0 <= mutation_rate <= 1):
                return Response(
                    {'error': 'mutation_rate debe estar entre 0 y 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not (0 <= crossover_rate <= 1):
                return Response(
                    {'error': 'crossover_rate debe estar entre 0 y 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear el objeto Schedule con estado 'generating'
            schedule = Schedule.objects.create(
                name=name,
                description=description,
                status='generating'
            )

            def run_generation(schedule_id):
                try:
                    # Crear generador (heurísticas desactivadas por defecto para mayor velocidad)
                    generator = ScheduleGenerator(
                        population_size=population_size,
                        generations=generations,
                        mutation_rate=mutation_rate,
                        crossover_rate=crossover_rate,
                        elitism_size=elitism_size,
                        tournament_size=tournament_size,
                        use_heuristics=False
                    )
                    
                    # Cargar datos
                    generator.load_data()
                    
                    # Obtener la instancia de schedule
                    current_schedule = Schedule.objects.get(id=schedule_id)
                    
                    # Generar horario pasando la instancia
                    generator.generate(name, description, schedule_instance=current_schedule)
                    
                    # Actualizar estado a completed
                    current_schedule.refresh_from_db()
                    current_schedule.status = 'completed'
                    current_schedule.save()
                    
                except Exception as e:
                    print(f"Error en generación background: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        s = Schedule.objects.get(id=schedule_id)
                        s.status = 'failed'
                        s.description += f"\nError: {str(e)}"
                        s.save()
                    except:
                        pass

            # Iniciar hilo
            thread = threading.Thread(target=run_generation, args=(schedule.id,))
            thread.daemon = True
            thread.start()
            
            # Serializar respuesta inicial
            serializer = ScheduleSerializer(schedule)
            
            return Response({
                'schedule': serializer.data,
                'message': 'Generación de horario iniciada en segundo plano'
            }, status=status.HTTP_202_ACCEPTED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error al iniciar generación: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activar un horario y desactivar los demás"""
        schedule = self.get_object()
        Schedule.objects.all().update(is_active=False)
        schedule.is_active = True
        schedule.save()
        return Response({'status': 'Horario activado'})
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Obtener resumen detallado de un horario"""
        schedule = self.get_object()
        generator = ScheduleGenerator()
        generator.load_data()
        summary = generator.get_schedule_summary(schedule)
        
        return Response({
            'schedule_id': schedule.id,
            'schedule_name': schedule.name,
            'fitness_score': schedule.fitness_score,
            'total_assignments': summary['total_assignments'],
            'unassigned_classes': summary['unassigned_classes'],
            'instructor_schedules': [
                {
                    'instructor_id': item['instructor'].xml_id,
                    'instructor_name': item['instructor'].name,
                    'class_count': len(item['classes'])
                }
                for item in summary['instructor_schedules']
            ],
            'room_schedules': [
                {
                    'room_id': item['room'].xml_id,
                    'room_capacity': item['room'].capacity,
                    'class_count': len(item['classes'])
                }
                for item in summary['room_schedules']
            ]
        })
    
    @action(detail=True, methods=['get'])
    def calendar_view(self, request, pk=None):
        """Obtener vista de calendario para FullCalendar.js"""
        schedule = self.get_object()
        assignments = schedule.assignments.select_related(
            'class_obj__offering',
            'room',
            'time_slot'
        ).prefetch_related('class_obj__instructors__instructor')
        
        # --- Conflict Detection Logic ---
        assignments_list = list(assignments)
        conflict_assignment_ids = set()

        def check_overlap(a1, a2):
            # Check days
            days_overlap = False
            for i in range(7):
                if a1.time_slot.days[i] == '1' and a2.time_slot.days[i] == '1':
                    days_overlap = True
                    break
            if not days_overlap: return False
            
            # Check time
            start1 = a1.time_slot.start_time
            end1 = start1 + a1.time_slot.length
            start2 = a2.time_slot.start_time
            end2 = start2 + a2.time_slot.length
            
            return (start1 < end2 and start2 < end1)

        # 1. Room Conflicts
        by_room = {}
        for a in assignments_list:
            if a.room_id not in by_room: by_room[a.room_id] = []
            by_room[a.room_id].append(a)
        
        for room_id, room_assignments in by_room.items():
            for i, a1 in enumerate(room_assignments):
                for a2 in room_assignments[i+1:]:
                    if check_overlap(a1, a2):
                        conflict_assignment_ids.add(a1.id)
                        conflict_assignment_ids.add(a2.id)

        # 2. Instructor Conflicts
        by_instructor = {}
        for a in assignments_list:
            for class_instructor in a.class_obj.instructors.all():
                inst_id = class_instructor.instructor_id
                if inst_id not in by_instructor: by_instructor[inst_id] = []
                by_instructor[inst_id].append(a)
        
        for inst_id, inst_assignments in by_instructor.items():
             for i, a1 in enumerate(inst_assignments):
                for a2 in inst_assignments[i+1:]:
                    if a1.id == a2.id: continue
                    if check_overlap(a1, a2):
                        conflict_assignment_ids.add(a1.id)
                        conflict_assignment_ids.add(a2.id)
        
        # --- Color Generation Helper ---
        import hashlib
        def get_color(text):
            hash_object = hashlib.md5(text.encode())
            digest = hash_object.digest()
            # Darker colors for white text readability (Range 40-170)
            r = int((digest[0] / 255.0) * 130 + 40)
            g = int((digest[1] / 255.0) * 130 + 40)
            b = int((digest[2] / 255.0) * 130 + 40)
            return f"#{r:02x}{g:02x}{b:02x}"

        events = []
        for assignment in assignments_list:
            time_slot = assignment.time_slot
            class_obj = assignment.class_obj
            
            # Obtener instructores
            instructors = [ci.instructor.name or f"Instructor {ci.instructor.xml_id}" 
                          for ci in class_obj.instructors.all()]
            
            course_name = class_obj.offering.name if class_obj.offering else 'Sin curso'
            color = get_color(course_name)
            is_conflict = assignment.id in conflict_assignment_ids

            # Convertir días binarios a eventos
            day_map = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for i, day_active in enumerate(time_slot.days):
                if day_active == '1':
                    events.append({
                        'id': f"{assignment.id}_{i}",
                        'title': course_name,
                        'daysOfWeek': [i + 1 if i < 6 else 0],  # FullCalendar usa 0=Domingo
                        'startTime': time_slot.get_start_time_formatted(),
                        'endTime': time_slot.get_end_time_formatted(),
                        'backgroundColor': '#ef4444' if is_conflict else color, # Red if conflict
                        'borderColor': '#b91c1c' if is_conflict else color,
                        'textColor': '#ffffff',
                        'extendedProps': {
                            'classId': class_obj.xml_id,
                            'room': f"Room {assignment.room.xml_id}",
                            'roomId': assignment.room.id,
                            'roomXmlId': assignment.room.xml_id,
                            'roomCapacity': assignment.room.capacity,
                            'instructors': instructors,
                            'classLimit': class_obj.class_limit,
                            'conflict': is_conflict
                        }
                    })
        
        return Response(events)
    
    @action(detail=True, methods=['get'], url_path='room/(?P<room_id>[^/.]+)/assignments')
    def room_assignments(self, request, pk=None, room_id=None):
        """Obtener asignaciones de una aula específica en un horario"""
        schedule = self.get_object()
        
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {'error': 'Aula no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener asignaciones de esta aula en este horario
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule,
            room=room
        ).select_related(
            'class_obj__offering',
            'time_slot'
        ).prefetch_related('class_obj__instructors__instructor')
        
        # Detectar conflictos de solapamiento temporal (igual que SQL)
        conflict_ids = set()
        assignments_list = list(assignments)
        
        def share_days(days1: str, days2: str) -> bool:
            """Verificar si dos cadenas de días comparten al menos un día activo"""
            for i in range(min(len(days1), len(days2))):
                if days1[i] == '1' and days2[i] == '1':
                    return True
            return False
        
        for i, a1 in enumerate(assignments_list):
            for a2 in assignments_list[i+1:]:
                ts1 = a1.time_slot
                ts2 = a2.time_slot
                
                # Verificar si comparten AL MENOS UN día
                if share_days(ts1.days, ts2.days):
                    # Verificar solapamiento temporal
                    if (ts1.start_time < ts2.start_time + ts2.length and 
                        ts2.start_time < ts1.start_time + ts1.length):
                        conflict_ids.add(a1.id)
                        conflict_ids.add(a2.id)
        
        result = []
        for assignment in assignments_list:
            ts = assignment.time_slot
            has_conflict = assignment.id in conflict_ids
            
            instructors = [
                ci.instructor.name or f"Instructor {ci.instructor.xml_id}"
                for ci in assignment.class_obj.instructors.all()
            ]
            instructor_name = ', '.join(instructors) if instructors else 'Sin instructor'
            
            # Convertir start_time (slots de 5min) a minutos desde medianoche
            start_minutes = ts.start_time * 5
            length_minutes = ts.length * 5
            
            result.append({
                'id': assignment.id,
                'class_id': assignment.class_obj.xml_id,
                'class_name': assignment.class_obj.offering.name if assignment.class_obj.offering else f'Clase {assignment.class_obj.xml_id}',
                'room_id': room.xml_id,
                'instructor_name': instructor_name,
                'days': ts.days,
                'start_time': start_minutes,  # minutos desde medianoche
                'length': length_minutes,      # duración en minutos
                'student_count': assignment.class_obj.class_limit,
                'has_conflict': has_conflict
            })
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def timetable(self, request, pk=None):
        """Obtener vista completa del horario para el frontend"""
        schedule = self.get_object()
        
        # Obtener asignaciones
        assignments = schedule.assignments.select_related(
            'class_obj__offering',
            'room',
            'time_slot'
        ).prefetch_related('class_obj__instructors__instructor')
        
        # Estructura de respuesta
        days_map = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        grid = {day: {} for day in days_map}
        classes_info = []
        time_slots_set = set()
        classes_by_day = {day: 0 for day in days_map}
        
        for assignment in assignments:
            time_slot = assignment.time_slot
            class_obj = assignment.class_obj
            
            # Formatear hora
            start_time = time_slot.get_start_time_formatted()
            end_time = time_slot.get_end_time_formatted()
            time_str = f"{start_time} - {end_time}"
            time_slots_set.add(time_str)
            
            # Instructores
            instructors = [ci.instructor.name or f"Instructor {ci.instructor.xml_id}" 
                          for ci in class_obj.instructors.all()]
            
            class_info = {
                'id': assignment.id,
                'xml_id': class_obj.xml_id,
                'name': class_obj.offering.name if class_obj.offering else f"Clase {class_obj.xml_id}",
                'code': class_obj.offering.course.code if class_obj.offering and class_obj.offering.course else "",
                'instructors': instructors,
                'room': assignment.room.code if assignment.room else "Sin aula",
                'room_capacity': assignment.room.capacity if assignment.room else 0,
                'limit': class_obj.class_limit,
                'students': class_obj.enrolled_students.count(),
                'start': start_time,
                'end': end_time,
                'duration_min': time_slot.length * 5,
                'time': time_str
            }
            
            classes_info.append(class_info)
            
            # Llenar grid
            for i, day_active in enumerate(time_slot.days):
                if day_active == '1' and i < 7:
                    day_name = days_map[i]
                    classes_by_day[day_name] += 1
                    
                    if time_str not in grid[day_name]:
                        grid[day_name][time_str] = []
                    
                    grid[day_name][time_str].append(class_info)
        
        # Ordenar slots de tiempo
        sorted_time_slots = sorted(list(time_slots_set))
        
        return Response({
            'schedule': {
                'id': schedule.id,
                'name': schedule.name,
                'description': schedule.description,
                'fitness_score': schedule.fitness_score,
                'total_assignments': assignments.count()
            },
            'time_slots': sorted_time_slots,
            'days': days_map,
            'grid': grid,
            'classes': classes_info,
            'stats': {
                'total_classes': assignments.count(),
                'classes_by_day': classes_by_day,
                'max_concurrent_classes': 0, # Simplificado
                'needs_multiple_views': False
            }
        })
    


class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para slots de tiempo"""
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer


class ClassInstructorViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar relaciones clase-instructor"""
    queryset = ClassInstructor.objects.all()
    serializer_class = ClassInstructorSerializer


class ClassRoomViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar relaciones clase-aula"""
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
