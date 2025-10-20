"""
Comando de Django para mostrar reporte de instructores sintéticos.
Uso: python manage.py show_synthetic_instructors
"""

from django.core.management.base import BaseCommand
from schedule_app.models import Instructor, ClassInstructor
from schedule_app.schedule_generator import ScheduleGenerator


class Command(BaseCommand):
    help = 'Muestra un reporte de los instructores sintéticos creados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('  REPORTE DE INSTRUCTORES SINTÉTICOS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')
        
        # Generar reporte
        generator = ScheduleGenerator()
        report = generator.get_synthetic_instructors_report()
        
        if report['total_synthetic'] == 0:
            self.stdout.write(self.style.SUCCESS('[OK] No hay instructores sintéticos en el sistema'))
            self.stdout.write('  Todos los cursos tienen profesores reales asignados.')
            return
        
        self.stdout.write(self.style.WARNING(f'[WARNING]  Total de instructores sintéticos: {report["total_synthetic"]}'))
        self.stdout.write('')
        self.stdout.write('Estos instructores representan cursos que AÚN necesitan')
        self.stdout.write('profesores reales asignados. Use esta información para:')
        self.stdout.write('  1. Identificar qué cursos necesitan profesores')
        self.stdout.write('  2. Calcular cuántos profesores contratar')
        self.stdout.write('  3. Planificar la asignación de carga docente')
        self.stdout.write('')
        self.stdout.write('-'*60)
        
        for idx, inst_data in enumerate(report['instructors'], 1):
            instructor = inst_data['instructor']
            self.stdout.write(f'\n{idx}. {instructor.name}')
            self.stdout.write(f'   Curso: {inst_data["course"]}')
            self.stdout.write(f'   Clases a cargo: {inst_data["class_count"]}')
            self.stdout.write(f'   IDs de clases: {", ".join(map(str, inst_data["classes"]))}')
        
        self.stdout.write('')
        self.stdout.write('-'*60)
        self.stdout.write(self.style.WARNING(f'\n[WARNING]  ACCIÓN REQUERIDA:'))
        self.stdout.write(f'   Asigne {report["total_synthetic"]} profesores reales a estos cursos')
        self.stdout.write('')
        self.stdout.write('Para eliminar instructores sintéticos después de asignar reales:')
        self.stdout.write('  python manage.py shell')
        self.stdout.write('  >>> from schedule_app.models import Instructor')
        self.stdout.write('  >>> Instructor.objects.filter(xml_id__gte=900000).delete()')
        self.stdout.write('')
