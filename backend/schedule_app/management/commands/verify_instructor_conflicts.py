"""
Comando para verificar y reportar conflictos de instructores en un horario generado.
Los instructores ya están asignados desde el XML, este script verifica si hay conflictos.
"""

from django.core.management.base import BaseCommand
from schedule_app.models import Schedule, ScheduleAssignment, ClassInstructor, TimeSlot
from collections import defaultdict


class Command(BaseCommand):
    help = 'Verifica conflictos de instructores en un horario generado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schedule_id',
            type=int,
            required=True,
            help='ID del horario a verificar'
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Exportar conflictos a CSV'
        )

    def handle(self, *args, **options):
        schedule_id = options['schedule_id']
        export = options['export']

        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Horario {schedule_id} no existe'))
            return

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"VERIFICACIÓN DE CONFLICTOS DE INSTRUCTORES")
        self.stdout.write(f"Horario: {schedule.name} (ID: {schedule.id})")
        self.stdout.write(f"{'='*60}\n")

        # Obtener todas las asignaciones
        assignments = ScheduleAssignment.objects.filter(
            schedule=schedule
        ).select_related('class_obj', 'room', 'time_slot')

        # Construir mapa: instructor -> [(class, room, timeslot)]
        instructor_schedules = defaultdict(list)

        for assignment in assignments:
            # Obtener instructores de la clase
            class_instructors = ClassInstructor.objects.filter(
                class_obj=assignment.class_obj
            ).select_related('instructor')

            for ci in class_instructors:
                instructor_schedules[ci.instructor].append({
                    'assignment': assignment,
                    'class': assignment.class_obj,
                    'room': assignment.room,
                    'timeslot': assignment.time_slot
                })

        # Detectar conflictos
        total_conflicts = 0
        conflicts_by_instructor = {}

        for instructor, schedule_list in instructor_schedules.items():
            conflicts = []

            # Comparar cada par de asignaciones
            for i in range(len(schedule_list)):
                for j in range(i + 1, len(schedule_list)):
                    assign1 = schedule_list[i]
                    assign2 = schedule_list[j]

                    ts1 = assign1['timeslot']
                    ts2 = assign2['timeslot']

                    # Verificar solapamiento
                    if self._timeslots_overlap(ts1, ts2):
                        conflicts.append({
                            'class1': assign1['class'],
                            'class2': assign2['class'],
                            'room1': assign1['room'],
                            'room2': assign2['room'],
                            'timeslot1': ts1,
                            'timeslot2': ts2
                        })
                        total_conflicts += 1

            if conflicts:
                conflicts_by_instructor[instructor] = conflicts

        # Reporte
        self.stdout.write(f"\n📊 RESUMEN:")
        self.stdout.write(f"  Total de instructores: {len(instructor_schedules)}")
        self.stdout.write(f"  Instructores con conflictos: {len(conflicts_by_instructor)}")
        self.stdout.write(f"  Total de conflictos: {total_conflicts}")

        if total_conflicts == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ ¡No hay conflictos de instructores!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠️  Se detectaron {total_conflicts} conflictos"))

            # Mostrar detalles de conflictos
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write("DETALLES DE CONFLICTOS")
            self.stdout.write(f"{'='*60}\n")

            for instructor, conflicts in sorted(
                conflicts_by_instructor.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]:  # Mostrar top 10 instructores con más conflictos
                self.stdout.write(f"\n👨‍🏫 Instructor: {instructor.xml_id} - {instructor.name}")
                self.stdout.write(f"   Conflictos: {len(conflicts)}")

                for idx, conflict in enumerate(conflicts[:3], 1):  # Mostrar primeros 3
                    ts1 = conflict['timeslot1']
                    ts2 = conflict['timeslot2']

                    self.stdout.write(f"\n   Conflicto {idx}:")
                    self.stdout.write(f"      Clase 1: {conflict['class1'].xml_id} en {conflict['room1'].xml_id}")
                    self.stdout.write(f"         Días: {ts1.days} | Hora: {self._format_time(ts1.start_time)} | Duración: {ts1.length * 5}min")
                    self.stdout.write(f"      Clase 2: {conflict['class2'].xml_id} en {conflict['room2'].xml_id}")
                    self.stdout.write(f"         Días: {ts2.days} | Hora: {self._format_time(ts2.start_time)} | Duración: {ts2.length * 5}min")

                if len(conflicts) > 3:
                    self.stdout.write(f"   ... y {len(conflicts) - 3} conflictos más")

        # Exportar a CSV si se solicita
        if export:
            self._export_conflicts(schedule_id, conflicts_by_instructor)

        self.stdout.write(f"\n{'='*60}\n")

    def _timeslots_overlap(self, ts1: TimeSlot, ts2: TimeSlot) -> bool:
        """Verifica si dos timeslots se solapan"""
        # Verificar si comparten al menos un día
        share_day = False
        for i in range(min(len(ts1.days), len(ts2.days))):
            if ts1.days[i] == '1' and ts2.days[i] == '1':
                share_day = True
                break

        if not share_day:
            return False

        # Verificar solapamiento de tiempo
        end1 = ts1.start_time + ts1.length
        end2 = ts2.start_time + ts2.length

        return not (end1 <= ts2.start_time or end2 <= ts1.start_time)

    def _format_time(self, start_time: int) -> str:
        """Formatea el tiempo desde slots de 5 minutos"""
        minutes = start_time * 5
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def _export_conflicts(self, schedule_id: int, conflicts_by_instructor: dict):
        """Exporta conflictos a CSV"""
        import csv
        from datetime import datetime

        filename = f"instructor_conflicts_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'instructor_id', 'instructor_name',
                'class1_id', 'class1_room', 'class1_days', 'class1_time',
                'class2_id', 'class2_room', 'class2_days', 'class2_time'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for instructor, conflicts in conflicts_by_instructor.items():
                for conflict in conflicts:
                    writer.writerow({
                        'instructor_id': instructor.xml_id,
                        'instructor_name': instructor.name,
                        'class1_id': conflict['class1'].xml_id,
                        'class1_room': conflict['room1'].xml_id,
                        'class1_days': conflict['timeslot1'].days,
                        'class1_time': self._format_time(conflict['timeslot1'].start_time),
                        'class2_id': conflict['class2'].xml_id,
                        'class2_room': conflict['room2'].xml_id,
                        'class2_days': conflict['timeslot2'].days,
                        'class2_time': self._format_time(conflict['timeslot2'].start_time)
                    })

        self.stdout.write(self.style.SUCCESS(f"\n✅ Conflictos exportados a: {filename}"))
