"""
Comando de Django para generar horarios usando el algoritmo genético.
Uso: python manage.py generate_schedule [opciones]
"""

from django.core.management.base import BaseCommand
from schedule_app.schedule_generator import ScheduleGenerator


class Command(BaseCommand):
    help = 'Genera un horario usando algoritmo genético'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Horario Generado',
            help='Nombre del horario a generar'
        )
        parser.add_argument(
            '--population',
            type=int,
            default=100,
            help='Tamaño de la población (default: 100)'
        )
        parser.add_argument(
            '--generations',
            type=int,
            default=200,
            help='Número de generaciones (default: 200)'
        )
        parser.add_argument(
            '--mutation-rate',
            type=float,
            default=0.1,
            help='Tasa de mutación 0-1 (default: 0.1)'
        )
        parser.add_argument(
            '--crossover-rate',
            type=float,
            default=0.8,
            help='Tasa de cruce 0-1 (default: 0.8)'
        )
        parser.add_argument(
            '--elitism',
            type=int,
            default=5,
            help='Tamaño del elitismo (default: 5)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Generador de Horarios - Algoritmo Genético ===\n'))
        
        # Crear generador
        generator = ScheduleGenerator(
            population_size=options['population'],
            generations=options['generations'],
            mutation_rate=options['mutation_rate'],
            crossover_rate=options['crossover_rate'],
            elitism_size=options['elitism']
        )
        
        self.stdout.write('Cargando datos...')
        try:
            generator.load_data()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al cargar datos: {e}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Datos cargados exitosamente\n'))
        
        # Generar horario
        self.stdout.write('Iniciando generación de horario...\n')
        try:
            schedule = generator.generate(
                schedule_name=options['name'],
                description=f"Generado desde línea de comandos con parámetros: "
                           f"population={options['population']}, "
                           f"generations={options['generations']}, "
                           f"mutation_rate={options['mutation_rate']}, "
                           f"crossover_rate={options['crossover_rate']}"
            )
            
            self.stdout.write(self.style.SUCCESS(f'\n[OK] Horario generado exitosamente!'))
            self.stdout.write(f'  ID: {schedule.id}')
            self.stdout.write(f'  Nombre: {schedule.name}')
            self.stdout.write(f'  Fitness: {schedule.fitness_score:.2f}')
            self.stdout.write(f'  Asignaciones: {schedule.assignments.count()}')
            
            # Obtener resumen
            summary = generator.get_schedule_summary(schedule)
            self.stdout.write(f'\nResumen:')
            self.stdout.write(f'  - Clases asignadas: {summary["total_assignments"]}')
            self.stdout.write(f'  - Clases sin asignar: {summary["unassigned_classes"]}')
            self.stdout.write(f'  - Instructores con clases: {len(summary["instructor_schedules"])}')
            self.stdout.write(f'  - Aulas utilizadas: {len(summary["room_schedules"])}')
            
            # Mostrar reporte de instructores sintéticos
            if summary.get('synthetic_count', 0) > 0:
                self.stdout.write(self.style.WARNING(f'\n[WARNING] ATENCIÓN: Instructores Sintéticos'))
                self.stdout.write(self.style.WARNING(f'  - Total: {summary["synthetic_count"]} instructores sintéticos'))
                self.stdout.write(self.style.WARNING(f'  - Estos representan cursos que AÚN necesitan profesores reales'))
                self.stdout.write(f'\n  Para ver el reporte completo de instructores sintéticos:')
                self.stdout.write(f'  python manage.py shell -c "from schedule_app.schedule_generator import ScheduleGenerator; g = ScheduleGenerator(); print(g.get_synthetic_instructors_report())"')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError al generar horario: {e}'))
            import traceback
            traceback.print_exc()
