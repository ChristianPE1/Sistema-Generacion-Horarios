from rest_framework import serializers
from .models import (
    Room, Instructor, Course, Class, ClassInstructor,
    ClassRoom, TimeSlot, Student, StudentClass,
    Schedule, ScheduleAssignment
)


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class InstructorSerializer(serializers.ModelSerializer):
    class_count = serializers.SerializerMethodField()
    
    def get_class_count(self, obj):
        return obj.classes.count()
    
    class Meta:
        model = Instructor
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    class_count = serializers.SerializerMethodField()
    
    def get_class_count(self, obj):
        return obj.classes.count()
    
    class Meta:
        model = Course
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):
    day_names = serializers.SerializerMethodField()
    start_time_formatted = serializers.SerializerMethodField()
    end_time_formatted = serializers.SerializerMethodField()
    
    def get_day_names(self, obj):
        return obj.get_day_names()
    
    def get_start_time_formatted(self, obj):
        return obj.get_start_time_formatted()
    
    def get_end_time_formatted(self, obj):
        return obj.get_end_time_formatted()
    
    class Meta:
        model = TimeSlot
        fields = '__all__'


class ClassInstructorSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.name', read_only=True)
    
    class Meta:
        model = ClassInstructor
        fields = '__all__'


class ClassRoomSerializer(serializers.ModelSerializer):
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)
    
    class Meta:
        model = ClassRoom
        fields = '__all__'


class ClassSerializer(serializers.ModelSerializer):
    instructors = ClassInstructorSerializer(many=True, read_only=True)
    room_prefs = ClassRoomSerializer(many=True, read_only=True)
    time_slots = TimeSlotSerializer(many=True, read_only=True)
    offering_name = serializers.CharField(source='offering.name', read_only=True)
    student_count = serializers.SerializerMethodField()
    
    def get_student_count(self, obj):
        return obj.enrolled_students.count()
    
    class Meta:
        model = Class
        fields = '__all__'


class ClassListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    offering_name = serializers.CharField(source='offering.name', read_only=True)
    instructor_names = serializers.SerializerMethodField()
    
    def get_instructor_names(self, obj):
        return [ci.instructor.name for ci in obj.instructors.all()]
    
    class Meta:
        model = Class
        fields = ['id', 'xml_id', 'class_limit', 'offering_name', 'instructor_names']


class StudentSerializer(serializers.ModelSerializer):
    enrolled_classes_count = serializers.SerializerMethodField()
    
    def get_enrolled_classes_count(self, obj):
        return obj.enrolled_classes.count()
    
    class Meta:
        model = Student
        fields = '__all__'


class StudentClassSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    class_info = serializers.CharField(source='class_obj.__str__', read_only=True)
    
    class Meta:
        model = StudentClass
        fields = '__all__'


class ScheduleAssignmentSerializer(serializers.ModelSerializer):
    class_info = ClassListSerializer(source='class_obj', read_only=True)
    room_info = RoomSerializer(source='room', read_only=True)
    time_slot_info = TimeSlotSerializer(source='time_slot', read_only=True)
    
    class Meta:
        model = ScheduleAssignment
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    assignments = ScheduleAssignmentSerializer(many=True, read_only=True)
    assignment_count = serializers.SerializerMethodField()
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de horarios"""
    assignment_count = serializers.SerializerMethodField()
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    
    class Meta:
        model = Schedule
        fields = ['id', 'name', 'description', 'fitness_score', 'is_active', 
                  'created_at', 'updated_at', 'assignment_count']
