"""
Script de prueba rápida del algoritmo genético optimizado.
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_system.settings')
django.setup()

from schedule_app.schedule_generator import ScheduleGenerator
from schedule_app.models import Class, Room, TimeSlot

print("="*60)
print("PRUEBA DE VELOCIDAD - ALGORITMO GENÉTICO OPTIMIZADO")
print("="*60)

# Contadores
num_classes = Class.objects.count()
num_rooms = Room.objects.count()
num_timeslots = TimeSlot.objects.count()

print(f"\nDataset:")
print(f"  - Clases: {num_classes}")
print(f"  - Aulas: {num_rooms}")
print(f"  - Slots de tiempo: {num_timeslots}")

if num_classes == 0:
    print("\n[ERROR] No hay datos en la base de datos.")
    print("Primero importa un archivo XML desde el frontend o ejecuta:")
    print("  python manage.py loaddata <fixture>")
    sys.exit(1)

# Prueba con POCAS generaciones para medir velocidad
print("\n" + "-"*60)
print("PRUEBA 1: 10 generaciones (población 30)")
print("-"*60)

generator = ScheduleGenerator(
    population_size=30,
    generations=10,
    mutation_rate=0.15,
    crossover_rate=0.70,
    elitism_size=3,
    tournament_size=3
)

start_time = time.time()

try:
    # Cargar datos primero
    generator.load_data()
    
    # Generar horario
    result = generator.generate(
        schedule_name=f"Test Genético {time.strftime('%Y%m%d_%H%M%S')}",
        description="Prueba de velocidad del algoritmo genético"
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n✓ Horario generado exitosamente")
    print(f"\nResultados:")
    print(f"  - Tiempo total: {elapsed:.2f} segundos")
    print(f"  - Fitness final: {result.fitness_score:.2f}")
    print(f"  - Conflictos: {result.conflict_count}")
    print(f"  - Tiempo por generación: {elapsed/10:.2f}s")
    
    # Segunda prueba con más generaciones si la primera fue rápida
    if elapsed < 60:
        print("\n" + "-"*60)
        print("PRUEBA 2: 30 generaciones (población 50)")
        print("-"*60)
        
        generator2 = ScheduleGenerator(
            population_size=50,
            generations=30,
            mutation_rate=0.15,
            crossover_rate=0.70,
            elitism_size=5,
            tournament_size=3
        )
        
        generator2.load_data()
        
        start_time2 = time.time()
        result2 = generator2.generate(
            schedule_name=f"Test Genético 2 {time.strftime('%Y%m%d_%H%M%S')}",
            description="Segunda prueba de velocidad"
        )
        end_time2 = time.time()
        elapsed2 = end_time2 - start_time2
        
        print(f"\n✓ Horario generado exitosamente")
        print(f"\nResultados:")
        print(f"  - Tiempo total: {elapsed2:.2f} segundos")
        print(f"  - Fitness final: {result2.fitness_score:.2f}")
        print(f"  - Conflictos: {result2.conflict_count}")
        print(f"  - Tiempo por generación: {elapsed2/30:.2f}s")
        print(f"\nMejora respecto a prueba 1: {result.conflict_count - result2.conflict_count} conflictos menos")

except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("RESUMEN:")
print("="*60)
print("El algoritmo genético optimizado usa:")
print("  ✓ Inicialización greedy (rápida)")
print("  ✓ Operadores simples (sin heurísticas complejas)")
print("  ✓ Reparación mínima (solo capacidad)")
print("  ✓ Población reducida (50 individuos)")
print("  ✓ Menos generaciones (100 por defecto)")
print("\nPara producción se recomienda:")
print("  - 50-100 generaciones para datasets pequeños")
print("  - 100-200 generaciones para datasets grandes")
print("="*60)
