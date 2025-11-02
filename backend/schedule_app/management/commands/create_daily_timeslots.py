"""
Comando para crear timeslots individuales por día (Lun-Sab).
Esto permite al algoritmo asignar clases a CUALQUIER día, sin estar limitado
por los patrones multi-día del XML original (MWF, TR, etc).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from schedule_app.models import TimeSlot, Class
from collections import defaultdict


class Command(BaseCommand):
    help = 'Crea timeslots individuales para cada día de la semana (Lun-Sab)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Eliminar todos los timeslots existentes antes de crear nuevos'
        )

    def handle(self, *args, **options):
        clear_existing = options.get('clear_existing', False)

        with transaction.atomic():
            if clear_existing:
                self.stdout.write('Eliminando timeslots existentes...')
                count = TimeSlot.objects.count()
                TimeSlot.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Eliminados {count} timeslots'))

            self._create_daily_timeslots()

        self.stdout.write(self.style.SUCCESS('✓ Timeslots diarios creados exitosamente'))

    def _create_daily_timeslots(self):
        """
        Crea timeslots individuales para cada clase, para cada día Lun-Sab.
        
        Horarios: 7:30am - 10:00pm (cada 30 minutos)
        Duraciones: 12 slots (1h), 18 slots (1.5h), 24 slots (2h), 30 slots (2.5h), 36 slots (3h)
        """
        self.stdout.write('Creando timeslots individuales por día...')
        
        # Patrones de días individuales (Lun-Sab, NO domingo)
        day_patterns = {
            'Lunes': '1000000',
            'Martes': '0100000',
            'Miércoles': '0010000',
            'Jueves': '0001000',
            'Viernes': '0000100',
            'Sábado': '0000010',
        }
        
        # Horarios: 7:30am (90) hasta 10:00pm (264) cada 30 minutos
        start_times = list(range(90, 264, 6))  # 6 slots = 30 minutos
        
        # Duraciones comunes (en slots de 5 minutos)
        durations = [
            12,  # 1 hora
            18,  # 1.5 horas
            24,  # 2 horas
            30,  # 2.5 horas
            36,  # 3 horas
        ]
        
        # Obtener todas las clases
        classes = Class.objects.all()
        total_created = 0
        
        for class_obj in classes:
            for day_name, day_pattern in day_patterns.items():
                for start_time in start_times:
                    for duration in durations:
                        # Verificar que no se pase de las 10pm (264 slots = 10pm)
                        end_time = start_time + duration
                        if end_time <= 264:  # 10:00pm
                            # Crear timeslot si no existe
                            ts, created = TimeSlot.objects.get_or_create(
                                class_obj=class_obj,
                                days=day_pattern,
                                start_time=start_time,
                                length=duration,
                                defaults={
                                    'break_time': 10,
                                    'preference': 0.0  # Sin preferencias
                                }
                            )
                            if created:
                                total_created += 1
            
            if class_obj.id % 100 == 0:
                self.stdout.write(f'  Procesadas {class_obj.id} clases...')
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Creados {total_created} timeslots individuales'
        ))
        
        # Estadísticas
        day_stats = {}
        for day_name, day_pattern in day_patterns.items():
            count = TimeSlot.objects.filter(days=day_pattern).count()
            day_stats[day_name] = count
        
        self.stdout.write('\nDistribución por día:')
        for day, count in sorted(day_stats.items()):
            self.stdout.write(f'  {day}: {count:,} timeslots')
