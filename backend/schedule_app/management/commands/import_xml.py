from django.core.management.base import BaseCommand
import xml.etree.ElementTree as ET
from schedule_app.models import (
    Room, Instructor, Course, Class, Student, 
    GroupConstraint, GroupConstraintClass,
    ClassInstructor, ClassRoom, TimeSlot
)
from django.db import transaction


class Command(BaseCommand):
    help = 'Importa datos desde archivo XML del formato UniTime'

    def add_arguments(self, parser):
        parser.add_argument(
            'xml_file',
            type=str,
            help='Ruta al archivo XML a importar'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar la base de datos antes de importar'
        )

    def handle(self, *args, **options):
        xml_file = options['xml_file']
        clear_db = options.get('clear', False)

        if clear_db:
            self.stdout.write('Limpiando base de datos...')
            Room.objects.all().delete()
            Instructor.objects.all().delete()
            Course.objects.all().delete()
            Class.objects.all().delete()
            Student.objects.all().delete()
            GroupConstraint.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Base de datos limpiada'))

        self.stdout.write(f'Importando desde {xml_file}...')

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            stats = {
                'rooms': 0,
                'instructors': 0,
                'courses': 0,
                'classes': 0,
                'students': 0,
                'constraints': 0,
                'timeslots': 0,
                'class_rooms': 0
            }

            with transaction.atomic():
                # Importar rooms
                self.stdout.write('Importando aulas...')
                rooms_element = root.find('rooms')
                if rooms_element is not None:
                    for room_elem in rooms_element.findall('room'):
                        room_id = room_elem.get('id')
                        capacity = int(room_elem.get('capacity', 0))
                        location = room_elem.get('location', '')
                        is_constraint = room_elem.get('constraint', 'true') == 'true'
                        
                        Room.objects.create(
                            xml_id=int(room_id),
                            capacity=capacity,
                            location=location,
                            is_constraint=is_constraint
                        )
                        stats['rooms'] += 1

                self.stdout.write(self.style.SUCCESS(f'✓ {stats["rooms"]} aulas importadas'))

                # Importar classes (incluye instructors y courses)
                self.stdout.write('Importando clases, instructores y cursos...')
                classes_element = root.find('classes')
                if classes_element is not None:
                    instructors_dict = {}
                    courses_dict = {}
                    
                    for class_elem in classes_element.findall('class'):
                        class_id = class_elem.get('id')
                        offering_id = class_elem.get('offering', '')
                        subpart_id = class_elem.get('subpart', '')
                        class_limit = int(class_elem.get('classLimit', 0))
                        committed = class_elem.get('committed', 'false') == 'true'
                        
                        # Crear curso si no existe
                        if offering_id and offering_id not in courses_dict:
                            course = Course.objects.create(
                                xml_id=int(offering_id),
                                name=f"Course {offering_id}",
                                code=f"C{offering_id}"
                            )
                            courses_dict[offering_id] = course
                            stats['courses'] += 1
                        
                        course = courses_dict.get(offering_id)
                        
                        # Procesar instructores (buscar TODOS, no solo los de solución)
                        instructor = None
                        for instructor_elem in class_elem.findall('instructor'):
                            instructor_id = instructor_elem.get('id')
                            if instructor_id not in instructors_dict:
                                instructor = Instructor.objects.create(
                                    xml_id=int(instructor_id),
                                    name=f"Instructor {instructor_id}"
                                )
                                instructors_dict[instructor_id] = instructor
                                stats['instructors'] += 1
                            else:
                                instructor = instructors_dict[instructor_id]
                            
                            # Tomar el primero como el principal
                            break
                        
                        # Procesar tiempos y aulas de solución
                        time_elem = class_elem.find('time[@solution="true"]')
                        room_elem = class_elem.find('room[@solution="true"]')
                        
                        days = None
                        start_time = None
                        length = None
                        room = None
                        
                        if time_elem is not None:
                            days = time_elem.get('days', '0000000')
                            start_time = int(time_elem.get('start', 0))
                            length = int(time_elem.get('length', 0))
                        
                        if room_elem is not None:
                            room_id_str = room_elem.get('id')
                            try:
                                room = Room.objects.get(xml_id=int(room_id_str))
                            except Room.DoesNotExist:
                                pass
                        
                        # Crear clase
                        class_obj = Class.objects.create(
                            xml_id=int(class_id),
                            offering=course,
                            config=int(class_elem.get('config', 0)) if class_elem.get('config') else None,
                            subpart=int(subpart_id) if subpart_id else None,
                            class_limit=class_limit,
                            committed=committed,
                            scheduler=int(class_elem.get('scheduler', 0)) if class_elem.get('scheduler') else None,
                            department=int(class_elem.get('department', 0)) if class_elem.get('department') else None,
                            dates=class_elem.get('dates', '')
                        )
                        
                        # Asociar instructor
                        if instructor:
                            ClassInstructor.objects.create(
                                class_obj=class_obj,
                                instructor=instructor
                            )
                        
                        # Asociar TODAS las aulas disponibles (no solo la de solución)
                        for room_elem in class_elem.findall('room'):
                            room_id_str = room_elem.get('id')
                            try:
                                room_obj = Room.objects.get(xml_id=int(room_id_str))
                                pref = float(room_elem.get('pref', 0.0))
                                ClassRoom.objects.get_or_create(
                                    class_obj=class_obj,
                                    room=room_obj,
                                    defaults={'preference': pref}
                                )
                                stats['class_rooms'] += 1
                            except Room.DoesNotExist:
                                pass
                        
                        # Asociar TODOS los timeslots disponibles (no solo la solución)
                        for time_elem in class_elem.findall('time'):
                            days = time_elem.get('days', '0000000')
                            start = int(time_elem.get('start', 0))
                            length = int(time_elem.get('length', 0))
                            break_time = int(time_elem.get('breakTime', 10))
                            pref = float(time_elem.get('pref', 0.0))
                            
                            TimeSlot.objects.create(
                                class_obj=class_obj,
                                days=days,
                                start_time=start,
                                length=length,
                                break_time=break_time,
                                preference=pref
                            )
                            stats['timeslots'] += 1
                        
                        stats['classes'] += 1
                        
                        if stats['classes'] % 100 == 0:
                            self.stdout.write(f'  {stats["classes"]} clases procesadas...')

                self.stdout.write(self.style.SUCCESS(
                    f'✓ {stats["classes"]} clases, {stats["instructors"]} instructores, '
                    f'{stats["courses"]} cursos importados'
                ))

                # Importar group constraints
                self.stdout.write('Importando restricciones de grupo...')
                constraints_element = root.find('groupConstraints')
                if constraints_element is not None:
                    for constraint_elem in constraints_element.findall('constraint'):
                        constraint_id = constraint_elem.get('id')
                        constraint_type = constraint_elem.get('type', '')
                        pref = constraint_elem.get('pref', 'R')
                        
                        constraint, created = GroupConstraint.objects.get_or_create(
                            xml_id=int(constraint_id),
                            defaults={
                                'constraint_type': constraint_type,
                                'preference': pref
                            }
                        )
                        
                        # Asociar clases a la restricción
                        for class_elem in constraint_elem.findall('class'):
                            class_id = class_elem.get('id')
                            try:
                                class_obj = Class.objects.get(xml_id=int(class_id))
                                GroupConstraintClass.objects.get_or_create(
                                    constraint=constraint,
                                    class_obj=class_obj
                                )
                            except Class.DoesNotExist:
                                pass
                        
                        stats['constraints'] += 1
                        
                        if stats['constraints'] % 50 == 0:
                            self.stdout.write(f'  {stats["constraints"]} restricciones procesadas...')

                self.stdout.write(self.style.SUCCESS(
                    f'✓ {stats["constraints"]} restricciones importadas'
                ))

            # Resumen final
            self.stdout.write(self.style.SUCCESS('\n=== IMPORTACIÓN COMPLETADA ==='))
            self.stdout.write(f'Aulas: {stats["rooms"]}')
            self.stdout.write(f'Instructores: {stats["instructors"]}')
            self.stdout.write(f'Cursos: {stats["courses"]}')
            self.stdout.write(f'Clases: {stats["classes"]}')
            self.stdout.write(f'Restricciones: {stats["constraints"]}')
            self.stdout.write(f'Timeslots: {stats["timeslots"]}')
            self.stdout.write(f'Opciones de aulas: {stats["class_rooms"]}')

        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f'Error al parsear XML: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
