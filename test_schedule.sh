#!/bin/bash

# Script de prueba del algoritmo genético para generación de horarios
# Autor: Sistema de Horarios TI3
# Fecha: Octubre 2025

echo "=========================================="
echo "   PRUEBA DE ALGORITMO GENÉTICO"
echo "   Sistema de Generación de Horarios"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="/home/christianpe/Documentos/ti3/proyecto-ti3/backend"

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    echo -e "${RED}Error: No se encontró manage.py en $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

# Verificar/crear entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo -e "${GREEN}Entorno virtual activado${NC}"
echo ""

# Menú de opciones
echo "Selecciona el modo de prueba:"
echo ""
echo "1. Rápido   - 50 población, 100 generaciones (~30 seg)"
echo "2. Normal   - 100 población, 150 generaciones (~1 min)"
echo "3. Optimizado - 150 población, 250 generaciones (~2 min)"
echo "4. Intensivo - 200 población, 400 generaciones (~5 min)"
echo "5. Personalizado"
echo "6. Solo analizar horario existente"
echo ""
read -p "Opción [1-6]: " option

case $option in
    1)
        POPULATION=50
        GENERATIONS=100
        NAME="Test Rápido"
        ;;
    2)
        POPULATION=100
        GENERATIONS=150
        NAME="Test Normal"
        ;;
    3)
        POPULATION=150
        GENERATIONS=250
        NAME="Test Optimizado"
        ;;
    4)
        POPULATION=200
        GENERATIONS=400
        NAME="Test Intensivo"
        ;;
    5)
        read -p "Tamaño de población: " POPULATION
        read -p "Número de generaciones: " GENERATIONS
        read -p "Nombre del horario: " NAME
        ;;
    6)
        echo ""
        echo -e "${YELLOW}Analizando horarios existentes...${NC}"
        python manage.py shell << EOF
from schedule_app.models import Schedule
from schedule_app.constraints import ConstraintValidator

schedules = Schedule.objects.all().order_by('-created_at')[:5]
print("\n" + "="*60)
print("HORARIOS RECIENTES:")
print("="*60)

for i, schedule in enumerate(schedules, 1):
    print(f"\n{i}. {schedule.name}")
    print(f"   Fitness: {schedule.fitness_score:.2f}")
    print(f"   Creado: {schedule.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Asignaciones: {schedule.assignments.count()}")
EOF
        exit 0
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Configuración:${NC}"
echo "  - Población: $POPULATION"
echo "  - Generaciones: $GENERATIONS"
echo "  - Nombre: $NAME"
echo ""
echo -e "${YELLOW}Iniciando generación de horario...${NC}"
echo ""

# Ejecutar generación
python manage.py generate_schedule \
    --name "$NAME" \
    --population "$POPULATION" \
    --generations "$GENERATIONS"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "   GENERACIÓN COMPLETADA"
    echo "==========================================${NC}"
    echo ""
    echo -e "${YELLOW}Analizando resultado...${NC}"
    
    # Mostrar estadísticas del último horario
    python manage.py shell << EOF
from schedule_app.models import Schedule

latest = Schedule.objects.latest('created_at')
print("\n" + "="*60)
print("ESTADÍSTICAS DEL HORARIO GENERADO")
print("="*60)
print(f"\nNombre: {latest.name}")
print(f"Fitness: {latest.fitness_score:.2f}")
print(f"Asignaciones: {latest.assignments.count()}")

# Interpretación del fitness
fitness = latest.fitness_score
base = 100000.0

if fitness >= 95000:
    status = "EXCELENTE ✓✓✓"
elif fitness >= 80000:
    status = "BUENO ✓✓"
elif fitness >= 50000:
    status = "ACEPTABLE ✓"
else:
    status = "POBRE ✗"

percentage = (fitness / base) * 100
print(f"\nEstado: {status}")
print(f"Calidad: {percentage:.1f}%")

# Calcular violaciones aproximadas
if fitness < base:
    penalty = base - fitness
    hard_violations_approx = int(penalty / 1000)
    soft_violations_approx = int((penalty % 1000))
    
    print(f"\nViolaciones aproximadas:")
    print(f"  - Duras: ~{hard_violations_approx}")
    print(f"  - Blandas: ~{soft_violations_approx}")

print("\n" + "="*60)
EOF

    echo ""
    echo -e "${GREEN}Para ver el horario en la interfaz web:${NC}"
    echo "  1. Inicia el backend: cd backend && source venv/bin/activate && python manage.py runserver"
    echo "  2. Inicia el frontend: cd frontend && npm run dev"
    echo "  3. Abre: http://localhost:3000/schedules"
    echo ""
else
    echo ""
    echo -e "${RED}Error en la generación del horario${NC}"
    exit 1
fi
