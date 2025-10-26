from django.db import models


class Room(models.Model):
    """Modelo para las aulas/salones"""
    xml_id = models.IntegerField(unique=True)
    capacity = models.IntegerField()
    location = models.CharField(max_length=100, blank=True)
    is_constraint = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'rooms'
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'
    
    def __str__(self):
        return f"Room {self.xml_id} (Cap: {self.capacity})"


class Instructor(models.Model):
    """Modelo para los profesores/instructores"""
    xml_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True, null=True)
    
    class Meta:
        db_table = 'instructors'
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructores'
    
    def __str__(self):
        return f"Instructor {self.xml_id}" if not self.name else self.name


class Course(models.Model):
    """Modelo para los cursos/ofertas"""
    xml_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
    
    def __str__(self):
        return f"Course {self.xml_id}" if not self.name else f"{self.code} - {self.name}"


class Class(models.Model):
    """Modelo para las clases/secciones"""
    xml_id = models.IntegerField(unique=True)
    offering = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes', null=True)
    config = models.IntegerField(null=True)
    subpart = models.IntegerField(null=True)
    class_limit = models.IntegerField()
    committed = models.BooleanField(default=False)
    scheduler = models.IntegerField(null=True)
    department = models.IntegerField(null=True, blank=True)
    dates = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    class Meta:
        db_table = 'classes'
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
    
    def __str__(self):
        return f"Class {self.xml_id}"


class ClassInstructor(models.Model):
    """Relación entre clases e instructores"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='instructors')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='classes')
    
    class Meta:
        db_table = 'class_instructors'
        unique_together = ('class_obj', 'instructor')
        verbose_name = 'Instructor de Clase'
        verbose_name_plural = 'Instructores de Clases'


class ClassRoom(models.Model):
    """Relación entre clases y aulas con preferencias"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='room_prefs')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='class_prefs')
    preference = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'class_rooms'
        unique_together = ('class_obj', 'room')
        verbose_name = 'Aula de Clase'
        verbose_name_plural = 'Aulas de Clases'


class TimeSlot(models.Model):
    """Modelo para los slots de tiempo"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='time_slots')
    days = models.CharField(max_length=7)  # Formato: "1010000" (L,M,W,J,V,S,D)
    start_time = models.IntegerField()  # Minutos desde medianoche / 5
    length = models.IntegerField()  # Duración en slots de 5 minutos
    break_time = models.IntegerField(default=10)  # Tiempo de descanso en minutos
    preference = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'time_slots'
        verbose_name = 'Slot de Tiempo'
        verbose_name_plural = 'Slots de Tiempo'
    
    def get_day_names(self):
        """Retorna los días de la semana"""
        day_names = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
        return [day_names[i] for i, d in enumerate(self.days) if d == '1']
    
    def get_start_time_formatted(self):
        """Retorna la hora de inicio formateada"""
        minutes = self.start_time * 5
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def get_end_time_formatted(self):
        """Retorna la hora de fin formateada"""
        total_minutes = (self.start_time + self.length) * 5
        hours = total_minutes // 60
        mins = total_minutes % 60
        return f"{hours:02d}:{mins:02d}"


class Student(models.Model):
    """Modelo para los estudiantes"""
    xml_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True, null=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
    
    def __str__(self):
        return f"Student {self.xml_id}" if not self.name else self.name


class StudentClass(models.Model):
    """Relación entre estudiantes y clases"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrolled_classes')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrolled_students')
    offering = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='student_demands')
    weight = models.FloatField(default=1.0)
    
    class Meta:
        db_table = 'student_classes'
        unique_together = ('student', 'class_obj')
        verbose_name = 'Estudiante en Clase'
        verbose_name_plural = 'Estudiantes en Clases'


class Schedule(models.Model):
    """Modelo para horarios generados"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fitness_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'schedules'
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ScheduleAssignment(models.Model):
    """Asignaciones específicas en un horario"""
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='assignments')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'schedule_assignments'
        unique_together = ('schedule', 'class_obj')
        verbose_name = 'Asignación de Horario'
        verbose_name_plural = 'Asignaciones de Horarios'


class GroupConstraint(models.Model):
    """Restricciones de grupo (BTB, DIFF_TIME, etc.)"""
    xml_id = models.IntegerField(unique=True)
    constraint_type = models.CharField(max_length=50)
    preference = models.CharField(max_length=10)
    course_limit = models.IntegerField(null=True, blank=True)
    delta = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'group_constraints'
        verbose_name = 'Restricción de Grupo'
        verbose_name_plural = 'Restricciones de Grupo'
    
    def __str__(self):
        return f"GroupConstraint {self.xml_id} ({self.constraint_type})"


class GroupConstraintClass(models.Model):
    """Relación entre restricciones de grupo y clases"""
    constraint = models.ForeignKey(GroupConstraint, on_delete=models.CASCADE, related_name='classes')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='group_constraints')
    
    class Meta:
        db_table = 'group_constraint_classes'
        unique_together = ('constraint', 'class_obj')
        verbose_name = 'Clase en Restricción de Grupo'
        verbose_name_plural = 'Clases en Restricciones de Grupo'
