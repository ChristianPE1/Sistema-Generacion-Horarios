"""
Script de depuración para analizar el dataset y los conflictos
"""

from schedule_app.models import Class, Room, TimeSlot, ClassInstructor
from collections import defaultdict

print("="*60)
print("ANÁLISIS DEL DATASET")
print("="*60)

# Análisis de clases
classes = Class.objects.all()
print(f"\nTotal de clases: {classes.count()}")

# Análisis de aulas
rooms = Room.objects.all()
print(f"Total de aulas: {rooms.count()}")

# Análisis de capacidades
if rooms.exists():
    avg_capacity = sum(r.capacity for r in rooms) / rooms.count()
    min_capacity = min(r.capacity for r in rooms)
    max_capacity = max(r.capacity for r in rooms)
    print(f"\nCapacidades de aulas:")
    print(f"  - Promedio: {avg_capacity:.0f}")
    print(f"  - Mínima: {min_capacity}")
    print(f"  - Máxima: {max_capacity}")

# Análisis de límites de clase
if classes.exists():
    avg_limit = sum(c.class_limit for c in classes) / classes.count()
    min_limit = min(c.class_limit for c in classes)
    max_limit = max(c.class_limit for c in classes)
    print(f"\nLímites de estudiantes por clase:")
    print(f"  - Promedio: {avg_limit:.0f}")
    print(f"  - Mínimo: {min_limit}")
    print(f"  - Máximo: {max_limit}")

# Análisis de timeslots
timeslots = TimeSlot.objects.all()
print(f"\nTotal de timeslots: {timeslots.count()}")

# Timeslots por clase
slots_per_class = defaultdict(int)
for ts in timeslots:
    slots_per_class[ts.class_obj_id] += 1

if slots_per_class:
    avg_slots = sum(slots_per_class.values()) / len(slots_per_class)
    min_slots = min(slots_per_class.values())
    max_slots = max(slots_per_class.values())
    print(f"\nTimeslots disponibles por clase:")
    print(f"  - Promedio: {avg_slots:.1f}")
    print(f"  - Mínimo: {min_slots}")
    print(f"  - Máximo: {max_slots}")

# Clases sin timeslots
classes_without_slots = classes.count() - len(slots_per_class)
print(f"  - Clases SIN timeslots: {classes_without_slots}")

# Análisis de instructores
instructors_per_class = defaultdict(int)
class_instructors = ClassInstructor.objects.all()
for ci in class_instructors:
    instructors_per_class[ci.class_obj_id] += 1

if instructors_per_class:
    avg_inst = sum(instructors_per_class.values()) / len(instructors_per_class)
    print(f"\nInstructores por clase:")
    print(f"  - Promedio: {avg_inst:.1f}")
    print(f"  - Clases con instructor: {len(instructors_per_class)}")
    print(f"  - Clases sin instructor: {classes.count() - len(instructors_per_class)}")

# Análisis de compatibilidad aula-clase
suitable_rooms_count = []
for class_obj in classes[:100]:  # Muestra de 100 clases
    suitable = sum(1 for r in rooms if r.capacity >= class_obj.class_limit)
    suitable_rooms_count.append(suitable)

if suitable_rooms_count:
    avg_suitable = sum(suitable_rooms_count) / len(suitable_rooms_count)
    print(f"\nAulas compatibles por clase (muestra):")
    print(f"  - Promedio: {avg_suitable:.1f}")
    
# Análisis crítico
print("\n" + "="*60)
print("PROBLEMAS POTENCIALES DETECTADOS:")
print("="*60)

problems = []

if classes_without_slots > 0:
    problems.append(f"⚠️ {classes_without_slots} clases sin timeslots definidos")

if classes.count() / rooms.count() > 20:
    problems.append(f"⚠️ Ratio clases/aulas muy alto: {classes.count() / rooms.count():.1f}")

# Verificar si hay aulas insuficientes para clases grandes
large_classes = classes.filter(class_limit__gt=max_capacity).count() if rooms.exists() else 0
if large_classes > 0:
    problems.append(f"⚠️ {large_classes} clases requieren más capacidad que la máxima aula")

if not problems:
    print("✓ No se detectaron problemas críticos en el dataset")
else:
    for problem in problems:
        print(problem)

print("\n" + "="*60)
