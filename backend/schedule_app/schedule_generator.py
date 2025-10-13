"""
Metodo de generación de horarios usando algoritmo genético
"""

from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from .models import (
    Class, Room, TimeSlot, Schedule, ScheduleAssignment,
    Instructor, ClassInstructor
)
from .genetic_algorithm import GeneticAlgorithm, Individual
from .constraints import ConstraintValidator


class ScheduleGenerator:
    """
    Metodo principal para generar horarios usando algoritmo genético.
    """
    
    def __init__(self,
                 population_size: int = 100,
                 generations: int = 200,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elitism_size: int = 5,
                 tournament_size: int = 5):
        """
        Inicializa el generador con parámetros del algoritmo genético.
        """
        self.ga = GeneticAlgorithm(
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            elitism_size=elitism_size,
            tournament_size=tournament_size
        )
        
        self.validator = ConstraintValidator(
            hard_constraint_weight=1000.0,
            soft_constraint_weight=1.0
        )
        
        self.classes: List[Class] = []
        self.rooms: List[Room] = []
        self.time_slots_by_class: Dict[int, List[TimeSlot]] = {}
    
    def load_data(self):
        # Cargar todas las clases
        self.classes = list(Class.objects.select_related('offering').all())
        
        # Cargar todas las aulas
        self.rooms = list(Room.objects.all())
        
        # Crear instructores sintéticos para clases sin instructor
        synthetic_instructors_created = self._create_synthetic_instructors()
        
        # Cargar slots de tiempo por clase
        for class_obj in self.classes:
            time_slots = list(TimeSlot.objects.filter(class_obj=class_obj))
            if time_slots:
                self.time_slots_by_class[class_obj.id] = time_slots
            else:
                # Si no hay slots definidos, crear slots por defecto
                # Lunes a Viernes, 8AM-6PM, en bloques de 1 hora
                default_slots = self._create_default_timeslots(class_obj)
                self.time_slots_by_class[class_obj.id] = default_slots
        
        # Cargar datos en el validador
        self.validator.load_data(self.classes, self.rooms)
        
        print(f"Datos cargados: {len(self.classes)} clases, {len(self.rooms)} aulas")
        if synthetic_instructors_created > 0:
            print(f"⚠️ {synthetic_instructors_created} instructores sintéticos creados para clases sin profesor")
    
    def _create_synthetic_instructors(self) -> int:
        """
        Crea instructores sintéticos para clases sin instructor asignado.
        Esto ayuda a:
        1. Generar horarios completos sin bloqueos
        2. Identificar cuántos profesores faltan asignar
        3. Ver qué cursos necesitan más profesores
        
        Returns:
            int: Número de instructores sintéticos creados
        """
        synthetic_count = 0
        
        # Obtener clases sin instructor
        classes_with_instructor = set(
            ClassInstructor.objects.values_list('class_obj_id', flat=True)
        )
        
        classes_without_instructor = [
            c for c in self.classes if c.id not in classes_with_instructor
        ]
        
        if not classes_without_instructor:
            return 0
        
        print(f"\n⚠️ Se encontraron {len(classes_without_instructor)} clases sin instructor asignado")
        print("Creando instructores sintéticos...")
        
        # Agrupar por curso (offering)
        classes_by_course = {}
        for class_obj in classes_without_instructor:
            course_key = class_obj.offering_id if class_obj.offering_id else f"nocourse_{class_obj.id}"
            if course_key not in classes_by_course:
                classes_by_course[course_key] = []
            classes_by_course[course_key].append(class_obj)
        
        # Crear un instructor sintético por curso
        for course_key, course_classes in classes_by_course.items():
            # Obtener nombre del curso
            if isinstance(course_key, int):
                course = course_classes[0].offering
                course_name = course.name if course and course.name else course.code if course and course.code else f"Course_{course_key}"
            else:
                course_name = "Sin_Curso"
            
            # Crear instructor sintético
            # Usar XML ID alto para no conflictuar con IDs reales
            synthetic_xml_id = 900000 + synthetic_count
            
            instructor, created = Instructor.objects.get_or_create(
                xml_id=synthetic_xml_id,
                defaults={
                    'name': f'[SINTÉTICO] Profesor para {course_name}',
                    'email': f'synthetic.instructor.{synthetic_count}@sistema.edu'
                }
            )
            
            if created:
                synthetic_count += 1
            
            # Asignar instructor sintético a todas las clases del curso
            for class_obj in course_classes:
                ClassInstructor.objects.get_or_create(
                    class_obj=class_obj,
                    instructor=instructor
                )
        
        print(f"✓ {synthetic_count} instructores sintéticos creados")
        print(f"✓ {len(classes_without_instructor)} clases ahora tienen instructor asignado\n")
        
        return synthetic_count
    
    def _create_default_timeslots(self, class_obj: Class) -> List[TimeSlot]:
        """Crea slots de tiempo por defecto para una clase"""
        default_slots = []
        
        # Días: Lunes a Viernes (10000 = Lunes, 01000 = Martes, etc.)
        days_patterns = ['1000000', '0100000', '0010000', '0001000', '0000100']
        
        # Horarios: 8AM (96 slots), 9AM (108), 10AM (120), ..., 5PM (204)
        # Cada slot = 5 minutos, entonces 1 hora = 12 slots
        start_times = list(range(96, 216, 12))  # 8AM a 6PM
        
        for days in days_patterns:
            for start in start_times:
                # Crear TimeSlot temporal (no guardado en DB)
                ts = TimeSlot(
                    class_obj=class_obj,
                    days=days,
                    start_time=start,
                    length=12,  # 1 hora por defecto
                    preference=0.0
                )
                default_slots.append(ts)
        
        return default_slots
    
    def generate(self, schedule_name: str = None, 
                description: str = "") -> Schedule:
        """
        Genera un horario optimizado usando el algoritmo genético.
        """

        if not self.classes or not self.rooms:
            raise ValueError("No hay clases o aulas disponibles para generar horarios")
        
        print("Iniciando generación de horario...")
        
        # Inicializar población
        self.ga.initialize_population(
            self.classes,
            self.rooms,
            self.time_slots_by_class
        )
        
        # Ejecutar algoritmo genético
        best_solution = self.ga.evolve(self.validator)
        
        # Obtener estadísticas
        stats = self.ga.get_statistics()
        
        print(f"\nGeneración completada!")
        print(f"Mejor fitness: {stats['best_fitness']:.2f}")
        print(f"Mejora total: {stats['improvement']:.2f}")
        
        # Guardar solución en la base de datos
        schedule = self._save_schedule(
            best_solution,
            schedule_name or f"Horario Generado {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            description,
            stats
        )
        
        return schedule
    
    @transaction.atomic
    def _save_schedule(self, solution: Individual, name: str, description: str, stats: Dict) -> Schedule:
        """
        Guarda la solución en la base de datos como un Schedule.
        """
        # Crear el registro de Schedule
        schedule = Schedule.objects.create(
            name=name,
            description=description,
            fitness_score=solution.fitness,
            is_active=False
        )
        
        # Crear las asignaciones
        for class_id, (room_id, timeslot_id) in solution.genes.items():
            try:
                class_obj = Class.objects.get(id=class_id)
                room = Room.objects.get(id=room_id) if room_id else None
                
                # Obtener o crear el TimeSlot
                if timeslot_id:
                    try:
                        time_slot = TimeSlot.objects.get(id=timeslot_id)
                    except TimeSlot.DoesNotExist:
                        # Si el timeslot no existe en DB (era temporal), crearlo
                        temp_slots = self.time_slots_by_class.get(class_id, [])
                        matching_slot = next((ts for ts in temp_slots 
                                            if hasattr(ts, 'id') and ts.id == timeslot_id), None)
                        
                        if not matching_slot:
                            # Buscar por índice
                            idx = timeslot_id % len(temp_slots) if temp_slots else 0
                            matching_slot = temp_slots[idx] if temp_slots else None
                        
                        if matching_slot and not matching_slot.id:
                            matching_slot.save()
                            time_slot = matching_slot
                        else:
                            continue
                else:
                    continue
                
                # Crear la asignación
                if room and time_slot:
                    ScheduleAssignment.objects.create(
                        schedule=schedule,
                        class_obj=class_obj,
                        room=room,
                        time_slot=time_slot
                    )
            except Exception as e:
                print(f"Error al guardar asignación para clase {class_id}: {e}")
                continue
        
        # Actualizar descripción con estadísticas
        conflicts_report = self.validator.get_conflicts_report(solution)
        
        schedule.description = f"""{description}
            Estadísticas de Generación:
            - Fitness Final: {stats['best_fitness']:.2f}
            - Generaciones: {stats['generations']}
            - Mejora: {stats['improvement']:.2f}

            Conflictos:
            - Instructores: {conflicts_report['hard_constraints']['instructor_conflicts']}
            - Aulas: {conflicts_report['hard_constraints']['room_conflicts']}
            - Estudiantes: {conflicts_report['hard_constraints']['student_conflicts']}
            - Capacidad: {conflicts_report['hard_constraints']['capacity_violations']}
            """
        schedule.save()
        
        print(f"Horario guardado con ID: {schedule.id}")
        print(f"Total de asignaciones: {schedule.assignments.count()}")
        
        return schedule
    
    def get_schedule_summary(self, schedule: Schedule) -> Dict:
        """ Genera un resumen del horario generado """
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule
        ).select_related('class_obj', 'room', 'time_slot')
        
        # Agrupar por instructor
        instructor_schedules = {}
        synthetic_instructors = []
        
        for assignment in assignments:
            class_instructors = ClassInstructor.objects.filter(
                class_obj=assignment.class_obj
            ).select_related('instructor')
            
            for ci in class_instructors:
                instructor = ci.instructor
                if instructor.id not in instructor_schedules:
                    instructor_schedules[instructor.id] = {
                        'instructor': instructor,
                        'classes': [],
                        'is_synthetic': instructor.xml_id >= 900000
                    }
                
                instructor_schedules[instructor.id]['classes'].append({
                    'class': assignment.class_obj,
                    'room': assignment.room,
                    'time_slot': assignment.time_slot
                })
                
                # Identificar instructores sintéticos
                if instructor.xml_id >= 900000:
                    synthetic_instructors.append({
                        'instructor': instructor,
                        'class_count': len(instructor_schedules[instructor.id]['classes'])
                    })
        
        # Agrupar por aula
        room_schedules = {}
        for assignment in assignments:
            room = assignment.room
            if room.id not in room_schedules:
                room_schedules[room.id] = {
                    'room': room,
                    'classes': []
                }
            
            room_schedules[room.id]['classes'].append({
                'class': assignment.class_obj,
                'time_slot': assignment.time_slot
            })
        
        return {
            'schedule': schedule,
            'total_assignments': assignments.count(),
            'instructor_schedules': list(instructor_schedules.values()),
            'room_schedules': list(room_schedules.values()),
            'unassigned_classes': Class.objects.exclude(
                id__in=assignments.values_list('class_obj_id', flat=True)
            ).count(),
            'synthetic_instructors': synthetic_instructors,
            'synthetic_count': len(set(si['instructor'].id for si in synthetic_instructors))
        }
    
    def get_synthetic_instructors_report(self) -> Dict:
        """
        Genera un reporte de instructores sintéticos creados.
        Útil para identificar qué cursos necesitan profesores reales.
        """
        synthetic_instructors = Instructor.objects.filter(xml_id__gte=900000)
        
        report = {
            'total_synthetic': synthetic_instructors.count(),
            'instructors': []
        }
        
        for instructor in synthetic_instructors:
            classes = ClassInstructor.objects.filter(
                instructor=instructor
            ).select_related('class_obj__offering')
            
            course_name = "Sin curso"
            if classes.exists():
                first_class = classes.first().class_obj
                if first_class.offering:
                    course_name = first_class.offering.name or first_class.offering.code or "Sin nombre"
            
            report['instructors'].append({
                'instructor': instructor,
                'name': instructor.name,
                'course': course_name,
                'class_count': classes.count(),
                'classes': list(classes.values_list('class_obj__xml_id', flat=True))
            })
        
        return report
