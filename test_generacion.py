"""Test de generación con datasets."""
import os
import sys

# Añadir path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.schedule_app.schedule_builder import generate_from_xml

print("=" * 60)
print("PRUEBA DE GENERACIÓN DE HORARIOS")
print("=" * 60)

# Probar con escuela
escuela_path = "escuela.xml"
if os.path.exists(escuela_path):
    print(f"\n[1] Dataset: escuela.xml")
    result = generate_from_xml(escuela_path)
    print(f"    Clases asignadas: {result['classes_assigned']}/{result['classes_total']}")
    print(f"    Sin asignar: {result['conflict_count']}")
    print(f"    Fitness: {result['fitness_score']}")
    print(f"    Tiempo: {result['generation_time_ms']} ms")

# Probar con Purdue
purdue_path = "purdue_clean.xml"
if os.path.exists(purdue_path):
    print(f"\n[2] Dataset: purdue_clean.xml")
    result = generate_from_xml(purdue_path)
    print(f"    Clases asignadas: {result['classes_assigned']}/{result['classes_total']}")
    print(f"    Sin asignar: {result['conflict_count']}")
    print(f"    Fitness: {result['fitness_score']}")
    print(f"    Tiempo: {result['generation_time_ms']} ms")

print("\n" + "=" * 60)
print("COMPLETADO")
print("=" * 60)
