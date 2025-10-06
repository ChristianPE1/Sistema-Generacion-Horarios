from django.contrib import admin
from .models import (
    Room, Instructor, Course, Class, ClassInstructor, 
    ClassRoom, TimeSlot, Student, StudentClass, 
    Schedule, ScheduleAssignment
)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('xml_id', 'capacity', 'location', 'is_constraint')
    list_filter = ('is_constraint',)
    search_fields = ('xml_id', 'location')


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('xml_id', 'name', 'email')
    search_fields = ('xml_id', 'name', 'email')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('xml_id', 'code', 'name')
    search_fields = ('xml_id', 'code', 'name')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('xml_id', 'offering', 'class_limit', 'committed', 'parent')
    list_filter = ('committed',)
    search_fields = ('xml_id',)


@admin.register(ClassInstructor)
class ClassInstructorAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'instructor')
    search_fields = ('class_obj__xml_id', 'instructor__name')


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'room', 'preference')
    search_fields = ('class_obj__xml_id', 'room__xml_id')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'days', 'start_time', 'length', 'preference')
    search_fields = ('class_obj__xml_id',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('xml_id', 'name', 'email')
    search_fields = ('xml_id', 'name', 'email')


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj')
    search_fields = ('student__xml_id', 'class_obj__xml_id')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'fitness_score', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(ScheduleAssignment)
class ScheduleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'class_obj', 'room', 'time_slot')
    search_fields = ('schedule__name', 'class_obj__xml_id')
