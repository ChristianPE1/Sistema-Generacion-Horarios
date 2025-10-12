from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
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


class RoomViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar aulas"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
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
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ScheduleListSerializer
        return ScheduleSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generar un nuevo horario usando algoritmo genético"""
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
            
            # Crear generador
            generator = ScheduleGenerator(
                population_size=population_size,
                generations=generations,
                mutation_rate=mutation_rate,
                crossover_rate=crossover_rate,
                elitism_size=elitism_size,
                tournament_size=tournament_size
            )
            
            # Cargar datos
            generator.load_data()
            
            # Generar horario
            schedule = generator.generate(name, description)
            
            # Obtener resumen
            summary = generator.get_schedule_summary(schedule)
            
            # Serializar respuesta
            serializer = ScheduleSerializer(schedule)
            
            return Response({
                'schedule': serializer.data,
                'summary': {
                    'total_assignments': summary['total_assignments'],
                    'unassigned_classes': summary['unassigned_classes'],
                    'instructor_count': len(summary['instructor_schedules']),
                    'room_count': len(summary['room_schedules'])
                },
                'message': 'Horario generado exitosamente'
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error al generar horario: {str(e)}'},
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
        
        events = []
        for assignment in assignments:
            time_slot = assignment.time_slot
            class_obj = assignment.class_obj
            
            # Obtener instructores
            instructors = [ci.instructor.name or f"Instructor {ci.instructor.xml_id}" 
                          for ci in class_obj.instructors.all()]
            
            # Convertir días binarios a eventos
            day_map = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for i, day_active in enumerate(time_slot.days):
                if day_active == '1':
                    events.append({
                        'id': f"{assignment.id}_{i}",
                        'title': f"{class_obj.offering.name if class_obj.offering else 'Sin curso'}",
                        'daysOfWeek': [i + 1 if i < 6 else 0],  # FullCalendar usa 0=Domingo
                        'startTime': time_slot.get_start_time_formatted(),
                        'endTime': time_slot.get_end_time_formatted(),
                        'extendedProps': {
                            'classId': class_obj.xml_id,
                            'room': f"Room {assignment.room.xml_id}",
                            'roomCapacity': assignment.room.capacity,
                            'instructors': instructors,
                            'classLimit': class_obj.class_limit
                        }
                    })
        
        return Response(events)


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
