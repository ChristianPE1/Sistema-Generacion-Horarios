import xml.etree.ElementTree as ET
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count, Avg
from .models import (
    Room, Instructor, Course, Class, ClassInstructor,
    ClassRoom, TimeSlot, Student, StudentClass
)


@csrf_exempt
@transaction.atomic
def import_xml_view(request):
    """
    Vista para importar datos desde archivo XML
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo se permiten peticiones POST'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No se encontró el archivo'}, status=400)
    
    xml_file = request.FILES['file']
    
    try:
        # Parsear el XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        stats = {
            'rooms': 0,
            'instructors': 0,
            'courses': 0,
            'classes': 0,
            'time_slots': 0,
            'students': 0,
            'enrollments': 0
        }
        
        # Limpiar datos existentes si se solicita
        if request.POST.get('clear_existing') == 'true':
            Room.objects.all().delete()
            Instructor.objects.all().delete()
            Course.objects.all().delete()
            Class.objects.all().delete()
            Student.objects.all().delete()
        
        # 1. Importar Rooms
        rooms_elem = root.find('rooms')
        if rooms_elem is not None:
            for room_elem in rooms_elem.findall('room'):
                room, created = Room.objects.get_or_create(
                    xml_id=int(room_elem.get('id')),
                    defaults={
                        'capacity': int(room_elem.get('capacity', 0)),
                        'location': room_elem.get('location', ''),
                        'is_constraint': room_elem.get('constraint', 'false').lower() == 'true'
                    }
                )
                if created:
                    stats['rooms'] += 1
        
        # 2. Importar Instructors (extraer de las clases)
        instructor_ids = set()
        classes_elem = root.find('classes')
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                for instructor_elem in class_elem.findall('instructor'):
                    instructor_ids.add(int(instructor_elem.get('id')))
        
        for instructor_id in instructor_ids:
            instructor, created = Instructor.objects.get_or_create(
                xml_id=instructor_id,
                defaults={'name': f'Instructor {instructor_id}'}
            )
            if created:
                stats['instructors'] += 1
        
        # 3. Importar Courses (offerings)
        offering_ids = set()
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                offering_id = class_elem.get('offering')
                if offering_id:
                    offering_ids.add(int(offering_id))
        
        for offering_id in offering_ids:
            course, created = Course.objects.get_or_create(
                xml_id=offering_id,
                defaults={
                    'name': f'Course {offering_id}',
                    'code': f'COURSE-{offering_id}'
                }
            )
            if created:
                stats['courses'] += 1
        
        # 4. Importar Classes (primera pasada - sin parents)
        class_map = {}
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                class_id = int(class_elem.get('id'))
                offering_id = class_elem.get('offering')
                
                class_obj, created = Class.objects.get_or_create(
                    xml_id=class_id,
                    defaults={
                        'offering_id': Course.objects.filter(xml_id=int(offering_id)).first().id if offering_id else None,
                        'config': int(class_elem.get('config')) if class_elem.get('config') else None,
                        'subpart': int(class_elem.get('subpart')) if class_elem.get('subpart') else None,
                        'class_limit': int(class_elem.get('classLimit', 0)),
                        'committed': class_elem.get('committed', 'false').lower() == 'true',
                        'scheduler': int(class_elem.get('scheduler')) if class_elem.get('scheduler') else None,
                        'dates': class_elem.get('dates', '')
                    }
                )
                class_map[class_id] = class_obj
                
                if created:
                    stats['classes'] += 1
                    
                    # Importar instructores de la clase
                    for instructor_elem in class_elem.findall('instructor'):
                        instructor_id = int(instructor_elem.get('id'))
                        instructor = Instructor.objects.filter(xml_id=instructor_id).first()
                        if instructor:
                            ClassInstructor.objects.get_or_create(
                                class_obj=class_obj,
                                instructor=instructor
                            )
                    
                    # Importar rooms de la clase
                    for room_elem in class_elem.findall('room'):
                        room_id = int(room_elem.get('id'))
                        room = Room.objects.filter(xml_id=room_id).first()
                        if room:
                            ClassRoom.objects.get_or_create(
                                class_obj=class_obj,
                                room=room,
                                defaults={'preference': float(room_elem.get('pref', 0))}
                            )
                    
                    # Importar time slots
                    for time_elem in class_elem.findall('time'):
                        TimeSlot.objects.create(
                            class_obj=class_obj,
                            days=time_elem.get('days', '0000000'),
                            start_time=int(time_elem.get('start', 0)),
                            length=int(time_elem.get('length', 0)),
                            preference=float(time_elem.get('pref', 0))
                        )
                        stats['time_slots'] += 1
        
        # 5. Actualizar parents (segunda pasada)
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                class_id = int(class_elem.get('id'))
                parent_id = class_elem.get('parent')
                
                if parent_id and class_id in class_map:
                    parent_id = int(parent_id)
                    if parent_id in class_map:
                        class_obj = class_map[class_id]
                        class_obj.parent = class_map[parent_id]
                        class_obj.save()
        
        # 6. Importar Students
        students_elem = root.find('students')
        if students_elem is not None:
            for student_elem in students_elem.findall('student'):
                student_id = int(student_elem.get('id'))
                student, created = Student.objects.get_or_create(
                    xml_id=student_id,
                    defaults={'name': f'Student {student_id}'}
                )
                if created:
                    stats['students'] += 1
                
                # Importar enrollments
                for class_elem in student_elem.findall('class'):
                    class_id = int(class_elem.get('id'))
                    if class_id in class_map:
                        StudentClass.objects.get_or_create(
                            student=student,
                            class_obj=class_map[class_id]
                        )
                        stats['enrollments'] += 1
        
        return JsonResponse({
            'success': True,
            'message': 'XML importado exitosamente',
            'stats': stats
        })
        
    except ET.ParseError as e:
        return JsonResponse({
            'error': f'Error al parsear XML: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error al importar XML: {str(e)}'
        }, status=500)


def dashboard_stats(request):
    """
    Vista para obtener estadísticas del dashboard
    """
    try:
        # Estadísticas de aulas
        rooms_stats = {
            'total': Room.objects.count(),
            'avg_capacity': Room.objects.aggregate(avg=Avg('capacity'))['avg'] or 0,
            'with_constraints': Room.objects.filter(is_constraint=True).count()
        }
        
        # Estadísticas de instructores
        instructors_stats = {
            'total': Instructor.objects.count(),
            'with_classes': Instructor.objects.annotate(
                class_count=Count('classes')
            ).filter(class_count__gt=0).count()
        }
        
        # Estadísticas de cursos
        courses_stats = {
            'total': Course.objects.count(),
            'with_classes': Course.objects.annotate(
                class_count=Count('classes')
            ).filter(class_count__gt=0).count()
        }
        
        # Estadísticas de clases
        classes_stats = {
            'total': Class.objects.count(),
            'committed': Class.objects.filter(committed=True).count(),
            'with_instructor': ClassInstructor.objects.values('class_obj').distinct().count(),
            'avg_limit': Class.objects.aggregate(avg=Avg('class_limit'))['avg'] or 0
        }
        
        # Estadísticas de estudiantes
        students_stats = {
            'total': Student.objects.count(),
            'enrolled': Student.objects.annotate(
                class_count=Count('enrolled_classes')
            ).filter(class_count__gt=0).count()
        }
        
        # Estadísticas de slots de tiempo
        timeslots_stats = {
            'total': TimeSlot.objects.count()
        }
        
        return JsonResponse({
            'rooms': rooms_stats,
            'instructors': instructors_stats,
            'courses': courses_stats,
            'classes': classes_stats,
            'students': students_stats,
            'timeslots': timeslots_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al obtener estadísticas: {str(e)}'
        }, status=500)
