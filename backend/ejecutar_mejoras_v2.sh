#!/bin/bash

# 🚀 Script de Ejecución - Mejoras Fitness v2.0
# Ejecuta generación optimizada con restricciones mejoradas

set -e  # Salir si hay error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     GENERACIÓN DE HORARIO CON MEJORAS v2.0                ║"
echo "║     Objetivo: Alcanzar 70%+ fitness (313,600+)            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Debes ejecutar este script desde el directorio backend/"
    echo "   cd /home/christianpe/Documentos/ti3/proyecto-ti3/backend"
    exit 1
fi

# Activar entorno virtual
echo "📦 Activando entorno virtual..."
source venv/bin/activate

# Verificar Django
echo "🔍 Verificando instalación de Django..."
python manage.py check
if [ $? -ne 0 ]; then
    echo "❌ Error: Django no está configurado correctamente"
    exit 1
fi
echo "✅ Django OK"
echo ""

# Mostrar configuración
echo "⚙️  CONFIGURACIÓN:"
echo "   • Población: 200"
echo "   • Generaciones: 200"
echo "   • Tiempo estimado: 15-20 minutos"
echo "   • Fitness esperado: 310,000-340,000 (69-76%)"
echo ""

# Preguntar confirmación
read -p "¿Deseas continuar? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Cancelado por el usuario"
    exit 0
fi

echo ""
echo "🧬 Iniciando algoritmo genético..."
echo "   (Esto tomará aproximadamente 15-20 minutos)"
echo ""

# Ejecutar generación
START_TIME=$(date +%s)

python manage.py generate_schedule \
    --name "LLR Mejorado v2.0 - $(date '+%Y%m%d_%H%M')" \
    --population 200 \
    --generations 200

EXIT_CODE=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    RESULTADOS                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Generación completada exitosamente"
    echo "⏱️  Tiempo total: ${MINUTES}m ${SECONDS}s"
    echo ""
    
    # Extraer ID del último horario generado
    SCHEDULE_ID=$(sqlite3 db.sqlite3 "SELECT id FROM schedule_schedules ORDER BY id DESC LIMIT 1;" 2>/dev/null)
    
    if [ ! -z "$SCHEDULE_ID" ]; then
        echo "📋 ID del horario: $SCHEDULE_ID"
        echo ""
        
        # Calcular fitness porcentual
        FITNESS=$(sqlite3 db.sqlite3 "SELECT fitness FROM schedule_schedules WHERE id = $SCHEDULE_ID;" 2>/dev/null)
        if [ ! -z "$FITNESS" ]; then
            PERCENTAGE=$(python3 -c "print(f'{($FITNESS / 448000.0 * 100):.1f}')" 2>/dev/null)
            echo "📊 Fitness obtenido: $FITNESS ($PERCENTAGE%)"
            
            # Evaluar resultado
            if (( $(echo "$PERCENTAGE >= 70.0" | bc -l) )); then
                echo "🎉 ¡ÉXITO! Objetivo de 70% alcanzado"
            elif (( $(echo "$PERCENTAGE >= 65.0" | bc -l) )); then
                echo "⚠️  Cerca del objetivo (65-70%)"
                echo "   Intenta con más generaciones: --generations 300"
            else
                echo "⚠️  Por debajo del objetivo (<65%)"
                echo "   Recomendación: Aumentar población a 250"
            fi
            echo ""
        fi
        
        # Contar conflictos de aula
        echo "🔍 Analizando conflictos..."
        ROOM_CONFLICTS=$(sqlite3 db.sqlite3 "
            SELECT COUNT(*) 
            FROM schedule_assignments sa1 
            JOIN schedule_assignments sa2 
              ON sa1.schedule_id = sa2.schedule_id 
              AND sa1.room_id = sa2.room_id 
              AND sa1.id < sa2.id 
            JOIN time_slots ts1 ON sa1.time_slot_id = ts1.id 
            JOIN time_slots ts2 ON sa2.time_slot_id = ts2.id 
            WHERE sa1.schedule_id = $SCHEDULE_ID 
              AND ts1.days = ts2.days 
              AND ts1.start_time < ts2.start_time + ts2.length 
              AND ts2.start_time < ts1.start_time + ts1.length;
        " 2>/dev/null)
        
        if [ ! -z "$ROOM_CONFLICTS" ]; then
            echo "   Conflictos de aula: $ROOM_CONFLICTS"
            if [ "$ROOM_CONFLICTS" -lt 50 ]; then
                echo "   ✅ Conflictos aceptables (<50)"
            else
                echo "   ⚠️  Conflictos altos (objetivo: <50)"
            fi
        fi
        
        # Contar violaciones de capacidad
        CAPACITY_VIOLATIONS=$(sqlite3 db.sqlite3 "
            SELECT COUNT(*) 
            FROM schedule_assignments sa 
            JOIN classes c ON sa.class_obj_id = c.id 
            JOIN rooms r ON sa.room_id = r.id 
            WHERE sa.schedule_id = $SCHEDULE_ID 
              AND r.capacity < c.class_limit;
        " 2>/dev/null)
        
        if [ ! -z "$CAPACITY_VIOLATIONS" ]; then
            echo "   Violaciones capacidad: $CAPACITY_VIOLATIONS"
            if [ "$CAPACITY_VIOLATIONS" -lt 20 ]; then
                echo "   ✅ Violaciones aceptables (<20)"
            else
                echo "   ⚠️  Violaciones altas (objetivo: <20)"
            fi
        fi
        
        echo ""
        echo "📋 SIGUIENTES PASOS:"
        echo ""
        echo "1️⃣  Verificar conflictos de instructor:"
        echo "   python manage.py verify_instructor_conflicts --schedule_id $SCHEDULE_ID"
        echo ""
        echo "2️⃣  Ver en frontend:"
        echo "   http://localhost:3000/schedules/$SCHEDULE_ID"
        echo ""
        echo "3️⃣  Exportar conflictos (si los hay):"
        echo "   python manage.py verify_instructor_conflicts --schedule_id $SCHEDULE_ID --export"
        echo ""
    fi
else
    echo "❌ Error durante la generación (código: $EXIT_CODE)"
    echo "   Revisa los logs arriba para más detalles"
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            Documentación disponible en:                   ║"
echo "║   • MEJORAS_FITNESS_V2.md (guía completa)                 ║"
echo "║   • RESUMEN_MEJORAS.md (resumen ejecutivo)                ║"
echo "║   • CHANGELOG_V2.md (cambios técnicos)                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
