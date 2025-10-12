#!/bin/bash
# Cheat Sheet - Comandos Útiles del Sistema de Generación de Horarios

# ============================================================================
# SETUP INICIAL
# ============================================================================

# Instalar dependencias
cd backend && pip install -r requirements.txt

# Crear y aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario (admin)
python manage.py createsuperuser

# ============================================================================
# IMPORTAR DATOS
# ============================================================================

# Importar XML desde el shell de Django
python manage.py shell << 'EOF'
from django.core.files.uploadedfile import SimpleUploadedFile
from schedule_app.xml_parser import import_xml_view
from django.test import RequestFactory

with open('../pu-fal07-cs.xml', 'rb') as f:
    xml_content = f.read()

factory = RequestFactory()
request = factory.post('/api/import-xml/')
request.FILES['file'] = SimpleUploadedFile('pu-fal07-cs.xml', xml_content)
request.POST = {'clear_existing': 'true'}

response = import_xml_view(request)
print(f"Status: {response.status_code}")
EOF

# ============================================================================
# GENERAR HORARIOS
# ============================================================================

# Generación rápida (testing)
python manage.py generate_schedule \
  --name "Test Rápido" \
  --population 50 \
  --generations 100

# Generación estándar
python manage.py generate_schedule \
  --name "Horario Producción" \
  --population 100 \
  --generations 200

# Generación optimizada
python manage.py generate_schedule \
  --name "Horario Optimizado" \
  --population 150 \
  --generations 300 \
  --mutation-rate 0.15

# Generación con todos los parámetros
python manage.py generate_schedule \
  --name "Horario Completo" \
  --population 120 \
  --generations 250 \
  --mutation-rate 0.12 \
  --crossover-rate 0.82 \
  --elitism 6

# ============================================================================
# CONSULTAS A LA BASE DE DATOS
# ============================================================================

# Contar registros
python manage.py shell -c "
from schedule_app.models import *
print(f'Aulas: {Room.objects.count()}')
print(f'Instructores: {Instructor.objects.count()}')
print(f'Cursos: {Course.objects.count()}')
print(f'Clases: {Class.objects.count()}')
print(f'Estudiantes: {Student.objects.count()}')
print(f'Horarios: {Schedule.objects.count()}')
"

# Ver horarios generados
python manage.py shell -c "
from schedule_app.models import Schedule
for s in Schedule.objects.all():
    print(f'ID: {s.id} | {s.name} | Fitness: {s.fitness_score:.2f} | Activo: {s.is_active}')
"

# Ver mejor horario
python manage.py shell -c "
from schedule_app.models import Schedule
best = Schedule.objects.order_by('-fitness_score').first()
if best:
    print(f'Mejor: {best.name}')
    print(f'Fitness: {best.fitness_score:.2f}')
    print(f'Asignaciones: {best.assignments.count()}')
"

# Ver horario activo
python manage.py shell -c "
from schedule_app.models import Schedule
active = Schedule.objects.filter(is_active=True).first()
if active:
    print(f'Activo: {active.name} (Fitness: {active.fitness_score:.2f})')
else:
    print('No hay horario activo')
"

# ============================================================================
# API REST - EJEMPLOS CON CURL
# ============================================================================

# --- IMPORTAR XML ---
curl -X POST http://localhost:8000/api/import-xml/ \
  -F "file=@pu-fal07-cs.xml" \
  -F "clear_existing=true"

# --- GENERAR HORARIO ---
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Horario API",
    "population_size": 100,
    "generations": 200
  }'

# --- LISTAR HORARIOS ---
curl http://localhost:8000/api/schedules/

# --- DETALLE DE HORARIO ---
curl http://localhost:8000/api/schedules/1/

# --- RESUMEN DE HORARIO ---
curl http://localhost:8000/api/schedules/1/summary/

# --- VISTA CALENDARIO ---
curl http://localhost:8000/api/schedules/1/calendar_view/

# --- ACTIVAR HORARIO ---
curl -X POST http://localhost:8000/api/schedules/1/activate/

# --- LISTAR AULAS ---
curl http://localhost:8000/api/rooms/

# --- ESTADÍSTICAS DE AULAS ---
curl http://localhost:8000/api/rooms/statistics/

# --- LISTAR INSTRUCTORES ---
curl http://localhost:8000/api/instructors/

# --- CLASES DE UN INSTRUCTOR ---
curl http://localhost:8000/api/instructors/1/classes/

# --- LISTAR CURSOS ---
curl http://localhost:8000/api/courses/

# --- LISTAR CLASES ---
curl http://localhost:8000/api/classes/

# ============================================================================
# ANÁLISIS Y DEBUGGING
# ============================================================================

# Ver descripción detallada de un horario
python manage.py shell -c "
from schedule_app.models import Schedule
s = Schedule.objects.get(id=1)
print(s.description)
"

# Analizar conflictos de un horario
python manage.py shell << 'EOF'
from schedule_app.models import Schedule
from schedule_app.schedule_generator import ScheduleGenerator
from schedule_app.constraints import ConstraintValidator

schedule = Schedule.objects.get(id=1)
generator = ScheduleGenerator()
generator.load_data()

# Recrear el individuo del horario
from schedule_app.genetic_algorithm import Individual
individual = Individual(generator.classes, generator.rooms, generator.time_slots_by_class)

# Cargar genes desde BD
for assignment in schedule.assignments.all():
    individual.genes[assignment.class_obj.id] = (assignment.room.id, assignment.time_slot.id)

# Evaluar
report = generator.validator.get_conflicts_report(individual)
print("Conflictos Duros:")
for k, v in report['hard_constraints'].items():
    print(f"  {k}: {v}")
print("\nConflictos Blandos:")
for k, v in report['soft_constraints'].items():
    print(f"  {k}: {v}")
EOF

# Ver clases sin asignar en un horario
python manage.py shell -c "
from schedule_app.models import Schedule, Class
schedule = Schedule.objects.get(id=1)
assigned_ids = schedule.assignments.values_list('class_obj_id', flat=True)
unassigned = Class.objects.exclude(id__in=assigned_ids)
print(f'Clases sin asignar: {unassigned.count()}')
for c in unassigned[:5]:
    print(f'  - Clase {c.xml_id}')
"

# ============================================================================
# LIMPIEZA Y MANTENIMIENTO
# ============================================================================

# Eliminar todos los horarios
python manage.py shell -c "
from schedule_app.models import Schedule
count = Schedule.objects.count()
Schedule.objects.all().delete()
print(f'{count} horarios eliminados')
"

# Eliminar horarios con fitness bajo
python manage.py shell -c "
from schedule_app.models import Schedule
deleted = Schedule.objects.filter(fitness_score__lt=90000).delete()
print(f'Eliminados: {deleted[0]} horarios con fitness < 90000')
"

# Resetear base de datos completa
python manage.py flush --no-input

# Recrear migraciones
rm -rf schedule_app/migrations/0*.py
python manage.py makemigrations
python manage.py migrate

# ============================================================================
# EXPORTACIÓN DE DATOS
# ============================================================================

# Exportar horario a JSON
curl http://localhost:8000/api/schedules/1/calendar_view/ | jq '.' > horario_1.json

# Exportar resumen a JSON
curl http://localhost:8000/api/schedules/1/summary/ | jq '.' > resumen_1.json

# Exportar lista de horarios
curl http://localhost:8000/api/schedules/ | jq '.' > horarios.json

# ============================================================================
# TESTING Y BENCHMARKING
# ============================================================================

# Generar múltiples horarios y comparar
for i in {1..5}; do
  echo "Generando horario $i..."
  python manage.py generate_schedule \
    --name "Benchmark $i" \
    --population 100 \
    --generations 200
done

# Ver estadísticas de todos
python manage.py shell -c "
from schedule_app.models import Schedule
import statistics

scores = list(Schedule.objects.values_list('fitness_score', flat=True))
if scores:
    print(f'Total horarios: {len(scores)}')
    print(f'Mejor: {max(scores):.2f}')
    print(f'Peor: {min(scores):.2f}')
    print(f'Promedio: {statistics.mean(scores):.2f}')
    print(f'Desv. Est: {statistics.stdev(scores):.2f}')
"

# Benchmark de tiempo
time python manage.py generate_schedule \
  --name "Benchmark Time" \
  --population 100 \
  --generations 200

# ============================================================================
# DESARROLLO Y DEBUG
# ============================================================================

# Activar modo verbose en el algoritmo (editar genetic_algorithm.py)
# Cambiar línea 143 de:
#   if (generation + 1) % 10 == 0:
# A:
#   if (generation + 1) % 1 == 0:

# Ver logs del servidor Django
python manage.py runserver --verbosity 3

# Ejecutar shell interactivo
python manage.py shell

# Ejecutar shell con IPython (si está instalado)
python manage.py shell -i ipython

# Crear datos de prueba
python manage.py shell << 'EOF'
from schedule_app.models import Room, Instructor, Course

# Crear 5 aulas de prueba
for i in range(1, 6):
    Room.objects.create(xml_id=1000+i, capacity=30+i*5)

# Crear 3 instructores de prueba
for i in range(1, 4):
    Instructor.objects.create(xml_id=2000+i, name=f"Test Instructor {i}")

print("Datos de prueba creados")
EOF

# ============================================================================
# SCRIPTS ÚTILES
# ============================================================================

# Script para encontrar el mejor horario de múltiples ejecuciones
cat > find_best.sh << 'SCRIPT'
#!/bin/bash
BEST_FITNESS=0
BEST_ID=0

for i in {1..10}; do
  echo "Generación $i/10..."
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/schedules/generate/ \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Auto $i\", \"population_size\": 150, \"generations\": 300}")
  
  ID=$(echo $RESPONSE | jq -r '.schedule.id')
  FITNESS=$(echo $RESPONSE | jq -r '.schedule.fitness_score')
  
  echo "  ID: $ID, Fitness: $FITNESS"
  
  if (( $(echo "$FITNESS > $BEST_FITNESS" | bc -l) )); then
    BEST_FITNESS=$FITNESS
    BEST_ID=$ID
  fi
done

echo ""
echo "MEJOR HORARIO: ID=$BEST_ID, Fitness=$BEST_FITNESS"
curl -s -X POST http://localhost:8000/api/schedules/$BEST_ID/activate/
echo "Horario $BEST_ID activado"
SCRIPT

chmod +x find_best.sh

# ============================================================================
# MONITOREO
# ============================================================================

# Ver uso de base de datos
python manage.py dbshell << 'SQL'
.tables
.schema schedule_assignments
SELECT COUNT(*) FROM schedules;
SELECT COUNT(*) FROM schedule_assignments;
.quit
SQL

# Ver tamaño de BD
du -h backend/db.sqlite3

# Ver últimas creaciones
python manage.py shell -c "
from schedule_app.models import Schedule
recent = Schedule.objects.order_by('-created_at')[:5]
print('Últimos 5 horarios:')
for s in recent:
    print(f'  {s.created_at.strftime(\"%Y-%m-%d %H:%M\")} - {s.name}')
"

# ============================================================================
# AYUDA Y DOCUMENTACIÓN
# ============================================================================

# Ver ayuda del comando generate_schedule
python manage.py generate_schedule --help

# Ver todos los comandos disponibles
python manage.py help

# Listar URLs disponibles
python manage.py show_urls  # (requiere django-extensions)

# O manualmente
python manage.py shell -c "
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(pattern)
"

# ============================================================================
# SHORTCUTS
# ============================================================================

# Alias útiles (agregar a ~/.bashrc o ~/.zshrc)
alias dj='python manage.py'
alias djrun='python manage.py runserver'
alias djshell='python manage.py shell'
alias djmig='python manage.py makemigrations && python manage.py migrate'
alias genhorario='python manage.py generate_schedule'

# Función para generar y ver resultado
gentest() {
    python manage.py generate_schedule --name "Test $(date +%H%M)" --population 50 --generations 100
    python manage.py shell -c "from schedule_app.models import Schedule; s = Schedule.objects.latest('created_at'); print(f'Fitness: {s.fitness_score:.2f}')"
}

# ============================================================================
# FIN DEL CHEAT SHEET
# ============================================================================

echo "💡 Tip: Puedes ejecutar cualquiera de estos comandos directamente"
echo "📚 Documentación completa en: GENETIC_ALGORITHM.md"
echo "🚀 Script interactivo: ./test_genetic.sh"
