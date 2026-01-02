from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Avg, Max

from .models import (
    Room, Instructor, Course, Class, ClassInstructor,
    ClassRoom, TimeSlot, Student, StudentClass
)
from .serializers import (
    RoomSerializer, InstructorSerializer, CourseSerializer,
    ClassSerializer, ClassListSerializer, StudentSerializer,
    StudentClassSerializer, TimeSlotSerializer, 
    ClassInstructorSerializer, ClassRoomSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    # Paginación estándar para el sistema
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RoomViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar aulas
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        # Obtener estadísticas de las aulas
        total = self.queryset.count()
        avg_capacity = self.queryset.aggregate(avg=Avg('capacity'))['avg']
        max_capacity = self.queryset.aggregate(max=Max('capacity'))['max']
        
        return Response({
            'total_rooms': total,
            'average_capacity': round(avg_capacity, 2) if avg_capacity else 0,
            'max_capacity': max_capacity or 0
        })


class InstructorViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar instructores
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
        # Obtener estadísticas de instructores
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
    # ViewSet para gestionar cursos
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
    # ViewSet para gestionar clases
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
        # Obtener los estudiantes de una clase
        class_obj = self.get_object()
        student_classes = StudentClass.objects.filter(class_obj=class_obj)
        serializer = StudentClassSerializer(student_classes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        # Obtener estadísticas de clases
        total = self.queryset.count()
        committed = self.queryset.filter(committed=True).count()
        with_instructor = ClassInstructor.objects.values('class_obj').distinct().count()
        
        return Response({
            'total_classes': total,
            'committed_classes': committed,
            'classes_with_instructor': with_instructor
        })


class StudentViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar estudiantes
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        # Obtener las clases de un estudiante
        student = self.get_object()
        student_classes = StudentClass.objects.filter(student=student)
        serializer = StudentClassSerializer(student_classes, many=True)
        return Response(serializer.data)


class TimeSlotViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar slots de tiempo
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    pagination_class = StandardResultsSetPagination


class ClassInstructorViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar relación clase-instructor
    queryset = ClassInstructor.objects.all()
    serializer_class = ClassInstructorSerializer
    pagination_class = StandardResultsSetPagination


class ClassRoomViewSet(viewsets.ModelViewSet):
    # ViewSet para gestionar relación clase-aula
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    pagination_class = StandardResultsSetPagination
