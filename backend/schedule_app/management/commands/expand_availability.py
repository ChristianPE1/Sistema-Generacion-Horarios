from django.core.management.base import BaseCommand
from django.db import transaction
from schedule_app.models import Room, Class, ClassRoom, TimeSlot
from collections import defaultdict


class Command(BaseCommand):
    help = 'Expande la disponibilidad de aulas y horarios para mejorar la flexibilidad del algoritmo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-friday-saturday',
            action='store_true',
            help='Agregar timeslots de viernes y sábado'
        )
        parser.add_argument(
            '--expand-rooms',
            action='store_true',
            help='Expandir disponibilidad de aulas (todas las aulas para todas las clases compatibles)'
        )

    def handle(self, *args, **options):
        add_friday_saturday = options.get('add_friday_saturday', False)
        expand_rooms = options.get('expand_rooms', False)

        with transaction.atomic():
            if add_friday_saturday:
                self._add_friday_saturday_timeslots()
            
            if expand_rooms:
                self._expand_room_availability()

        self.stdout.write(self.style.SUCCESS('✓ Expansión de disponibilidad completada'))

    def _add_friday_saturday_timeslots(self):
        """
        Crea timeslots de viernes y sábado para cada clase basados en sus patrones existentes.
        """
        self.stdout.write('Expandiendo timeslots a viernes y sábado...')
        
        friday_pattern = '0000100'  # Viernes
        saturday_pattern = '0000010'  # Sábado
        
        friday_count = 0
        saturday_count = 0
        
        # Procesar cada clase
        classes = Class.objects.all()
        total_classes = classes.count()
        
        for idx, class_obj in enumerate(classes, 1):
            if idx % 100 == 0:
                self.stdout.write(f'  Procesadas {idx}/{total_classes} clases...')
            
            # Obtener timeslots existentes de esta clase
            existing_timeslots = TimeSlot.objects.filter(class_obj=class_obj)
            
            # Agrupar por (start_time, length) para evitar duplicados
            unique_patterns = {}
            for ts in existing_timeslots:
                key = (ts.start_time, ts.length, ts.break_time, ts.preference)
                if key not in unique_patterns:
                    unique_patterns[key] = ts
            
            # Crear timeslots de viernes y sábado
            for (start, length, break_time, pref), template_ts in unique_patterns.items():
                # Crear timeslot de viernes si no existe
                if not TimeSlot.objects.filter(
                    class_obj=class_obj,
                    days=friday_pattern,
                    start_time=start,
                    length=length
                ).exists():
                    TimeSlot.objects.create(
                        class_obj=class_obj,
                        days=friday_pattern,
                        start_time=start,
                        length=length,
                        break_time=break_time,
                        preference=pref
                    )
                    friday_count += 1
                
                # Crear timeslot de sábado si no existe
                if not TimeSlot.objects.filter(
                    class_obj=class_obj,
                    days=saturday_pattern,
                    start_time=start,
                    length=length
                ).exists():
                    TimeSlot.objects.create(
                        class_obj=class_obj,
                        days=saturday_pattern,
                        start_time=start,
                        length=length,
                        break_time=break_time,
                        preference=pref
                    )
                    saturday_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Agregados {friday_count} timeslots de viernes y {saturday_count} de sábado'
        ))

    def _expand_room_availability(self):
        """
        Expande la disponibilidad de aulas: todas las aulas disponibles para todas las clases
        que cumplan con restricciones de capacidad.
        """
        self.stdout.write('Expandiendo disponibilidad de aulas...')
        
        rooms = Room.objects.all()
        classes = Class.objects.all()
        
        added_count = 0
        skipped_count = 0
        
        for class_obj in classes:
            class_limit = class_obj.class_limit or 0
            
            for room in rooms:
                # Solo agregar si la capacidad del aula es suficiente
                if room.capacity >= class_limit:
                    # Verificar si ya existe la relación
                    if not ClassRoom.objects.filter(class_obj=class_obj, room=room).exists():
                        ClassRoom.objects.create(
                            class_obj=class_obj,
                            room=room,
                            preference=0.0  # Neutral
                        )
                        added_count += 1
                else:
                    skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Agregadas {added_count} nuevas relaciones aula-clase'
        ))
        self.stdout.write(f'  (Omitidas {skipped_count} por capacidad insuficiente)')
        
        # Estadísticas finales
        total_classes = classes.count()
        total_rooms = rooms.count()
        avg_rooms_per_class = ClassRoom.objects.values('class_obj').distinct().count()
        
        self.stdout.write(f'\nEstadísticas:')
        self.stdout.write(f'  Total clases: {total_classes}')
        self.stdout.write(f'  Total aulas: {total_rooms}')
        self.stdout.write(f'  Relaciones aula-clase: {ClassRoom.objects.count()}')
