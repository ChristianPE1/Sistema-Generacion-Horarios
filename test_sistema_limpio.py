#!/usr/bin/env python
"""
Script para generar XML limpio desde JSON y probar el sistema completo
"""

import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from schedule_app.simple_xml_converter import convert_json_to_clean_xml
from schedule_app.simple_xml_parser import SimpleXMLParser
from schedule_app.direct_generator import generate_from_json_file


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("="*60)
    print("SISTEMA DE GENERACIÓN - VERSIÓN LIMPIA")
    print("="*60)
    
    # 1. Generar XML limpio
    print("\n[1] Generando XML limpio...")
    json_path = os.path.join(base_dir, 'datos_horarios.json')
    xml_clean_path = os.path.join(base_dir, 'pu-fal07-llr_clean.xml')
    
    try:
        convert_json_to_clean_xml(json_path, xml_clean_path)
        print(f"    ✅ XML limpio generado: {xml_clean_path}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return 1
    
    # 2. Verificar XML
    print("\n[2] Verificando XML...")
    parser = SimpleXMLParser(xml_clean_path)
    parser.parse()
    summary = parser.get_summary()
    
    print(f"    ✅ Salas: {summary['rooms']}")
    print(f"    ✅ Instructores: {summary['instructors']}")
    print(f"    ✅ Clases: {summary['classes']}")
    print(f"    ✅ Time slots: {summary['total_timeslots']}")
    
    # 3. Generar horario
    print("\n[3] Generando horario con reglas...")
    print("    - No cruces")
    print("    - Máx 3 sesiones consecutivas")
    print("    - 10 min break entre cursos")
    print("    - Labs no cuentan como consecutivos")
    
    output_path = os.path.join(base_dir, 'horario_final.json')
    asignaciones, stats = generate_from_json_file(json_path, output_path)
    
    print(f"\n[4] ✅ Generación completada!")
    print(f"    Tiempo: {stats['tiempo_ms']} ms")
    print(f"    Cursos asignados: {stats['cursos_asignados']}/{stats['cursos_totales']}")
    print(f"    Resultado: {output_path}")
    
    # 4. Verificar reglas
    print("\n[5] Verificando cumplimiento de reglas...")
    
    # Verificar máx 3 bloques
    max_bloques = 0
    for asig in asignaciones:
        if asig.time_slot.num_bloques > max_bloques:
            max_bloques = asig.time_slot.num_bloques
    
    if max_bloques <= 3:
        print(f"    ✅ Máximo bloques consecutivos: {max_bloques} (≤ 3)")
    else:
        print(f"    ❌ Excede máximo: {max_bloques} bloques")
    
    # Verificar bloques de 50 min
    todos_50 = all(asig.time_slot.duracion_bloque_min == 50 for asig in asignaciones)
    if todos_50:
        print(f"    ✅ Todos los bloques son de 50 min")
    else:
        print(f"    ❌ Algunos bloques no son de 50 min")
    
    print("\n" + "="*60)
    print("✅ PRUEBA COMPLETADA")
    print("="*60)
    print(f"\nArchivos generados:")
    print(f"  - {xml_clean_path}")
    print(f"  - {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
