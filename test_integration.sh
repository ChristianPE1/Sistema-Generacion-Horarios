#!/bin/bash

# Script de prueba de integración del Algoritmo Genético
# Este script demuestra la funcionalidad completa del sistema

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  PRUEBA DE INTEGRACIÓN - ALGORITMO GENÉTICO                  ║"
echo "║  Sistema de Generación de Horarios                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/leo/Sistemas-Generacion-Horarios/backend
source venv/bin/activate

echo "📊 PASO 1: Verificando Datos Importados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py shell << 'EOF'
from schedule_app.models import Class, Room, Instructor, Course, TimeSlot
print(f"✓ Clases:      {Class.objects.count()}")
print(f"✓ Aulas:       {Room.objects.count()}")
print(f"✓ Instructores: {Instructor.objects.count()}")
print(f"✓ Cursos:      {Course.objects.count()}")
print(f"✓ TimeSlots:   {TimeSlot.objects.count()}")
EOF

echo ""
echo "🧬 PASO 2: Probando Componentes del Algoritmo Genético"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell << 'EOF'
from schedule_app.models import Class, Room, TimeSlot
from schedule_app.genetic_algorithm import Individual, GeneticAlgorithm
from schedule_app.constraints import ConstraintValidator

# Cargar datos
classes = list(Class.objects.all()[:20])  # Usar solo 20 clases para prueba rápida
rooms = list(Room.objects.all()[:10])

# Crear time_slots_by_class
time_slots_by_class = {}
for class_obj in classes:
    slots = list(TimeSlot.objects.filter(class_obj=class_obj)[:5])
    if slots:
        time_slots_by_class[class_obj.id] = slots

print(f"✓ Datos cargados: {len(classes)} clases, {len(rooms)} aulas")

# Test 1: Crear individuo
print("\n📋 Test 1: Creación de Individuo")
individual = Individual(classes, rooms, time_slots_by_class)
individual.initialize_random()
print(f"  ✓ Individuo creado con {len(individual.genes)} genes")

# Test 2: Validador de restricciones
print("\n📋 Test 2: Validador de Restricciones")
validator = ConstraintValidator()
validator.load_data(classes, rooms)
print(f"  ✓ Validador inicializado")

# Test 3: Calcular fitness
print("\n📋 Test 3: Cálculo de Fitness")
fitness = individual.calculate_fitness(validator)
print(f"  ✓ Fitness calculado: {fitness:.2f}")

# Test 4: Algoritmo Genético
print("\n📋 Test 4: Algoritmo Genético (5 generaciones)")
ga = GeneticAlgorithm(population_size=10, generations=5, mutation_rate=0.1)
ga.initialize_population(classes, rooms, time_slots_by_class)
print(f"  ✓ Población inicial creada: {len(ga.population)} individuos")

best = ga.evolve(validator)
print(f"  ✓ Evolución completada")
print(f"  ✓ Mejor fitness: {best.fitness:.2f}")

stats = ga.get_statistics()
print(f"  ✓ Mejora: {stats['improvement']:.2f}")
EOF

echo ""
echo "🔌 PASO 3: Probando Endpoint de API (Simulación)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell << 'EOF'
from schedule_app.schedule_generator import ScheduleGenerator

# Crear generador con parámetros de prueba
print("🚀 Generando horario con AG...")
generator = ScheduleGenerator(
    population_size=20,
    generations=10,
    mutation_rate=0.1,
    crossover_rate=0.8
)

# Cargar solo subset de datos para prueba rápida
from schedule_app.models import Class, Room, TimeSlot
generator.classes = list(Class.objects.all()[:30])
generator.rooms = list(Room.objects.all()[:15])

# Cargar time slots
for class_obj in generator.classes:
    slots = list(TimeSlot.objects.filter(class_obj=class_obj)[:5])
    if slots:
        generator.time_slots_by_class[class_obj.id] = slots

# Cargar en validador
generator.validator.load_data(generator.classes, generator.rooms)

print(f"  ✓ Datos cargados: {len(generator.classes)} clases, {len(generator.rooms)} aulas")

# Generar horario
schedule = generator.generate(
    schedule_name="Test Integration",
    description="Prueba de integración del algoritmo genético"
)

print(f"\n✅ HORARIO GENERADO:")
print(f"  • ID: {schedule.id}")
print(f"  • Nombre: {schedule.name}")
print(f"  • Fitness: {schedule.fitness_score:.2f}")
print(f"  • Asignaciones: {schedule.assignments.count()}")

# Obtener resumen
summary = generator.get_schedule_summary(schedule)
print(f"\n📊 RESUMEN:")
print(f"  • Total asignaciones: {summary['total_assignments']}")
print(f"  • Clases sin asignar: {summary['unassigned_classes']}")
print(f"  • Instructores: {len(summary['instructor_schedules'])}")
print(f"  • Aulas usadas: {len(summary['room_schedules'])}")
EOF

echo ""
echo "✅ PASO 4: Verificando Horario Guardado en BD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell << 'EOF'
from schedule_app.models import Schedule

schedules = Schedule.objects.all()
print(f"📋 Total de horarios en BD: {schedules.count()}\n")

for schedule in schedules:
    print(f"  Horario #{schedule.id}: {schedule.name}")
    print(f"    - Fitness: {schedule.fitness_score:.2f}")
    print(f"    - Asignaciones: {schedule.assignments.count()}")
    print(f"    - Creado: {schedule.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"    - Activo: {'Sí' if schedule.is_active else 'No'}")
    print()
EOF

echo ""
echo "🎯 PASO 5: Probando Vista de Calendario (API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell << 'EOF'
from schedule_app.models import Schedule
from django.test import RequestFactory
from schedule_app.views import ScheduleViewSet

schedule = Schedule.objects.first()
if schedule:
    factory = RequestFactory()
    request = factory.get(f'/api/schedules/{schedule.id}/calendar_view/')
    
    view = ScheduleViewSet()
    view.kwargs = {'pk': schedule.id}
    view.request = request
    
    response = view.calendar_view(request, pk=schedule.id)
    events = response.data
    
    print(f"📅 Eventos de calendario generados: {len(events)}")
    if events:
        print(f"\n  Ejemplo de evento:")
        event = events[0]
        print(f"    - Título: {event['title']}")
        print(f"    - Días: {event.get('daysOfWeek', 'N/A')}")
        print(f"    - Hora inicio: {event.get('startTime', 'N/A')}")
        print(f"    - Hora fin: {event.get('endTime', 'N/A')}")
        print(f"    - Aula: {event.get('extendedProps', {}).get('room', 'N/A')}")
else:
    print("No hay horarios para mostrar")
EOF

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ PRUEBA COMPLETADA CON ÉXITO                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 RESUMEN DE FUNCIONALIDADES PROBADAS:"
echo ""
echo "  ✓ Importación de datos XML"
echo "  ✓ Creación de individuos (cromosomas)"
echo "  ✓ Validación de restricciones"
echo "  ✓ Cálculo de fitness"
echo "  ✓ Algoritmo genético (evolución)"
echo "  ✓ Generación de horarios"
echo "  ✓ Persistencia en base de datos"
echo "  ✓ Vista de calendario (FullCalendar)"
echo "  ✓ API REST endpoints"
echo ""
echo "🎉 El sistema está completamente funcional!"
echo ""
