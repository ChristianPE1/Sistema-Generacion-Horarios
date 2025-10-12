#!/bin/bash

# Script para probar el algoritmo genético de generación de horarios

echo "================================================"
echo "   Sistema de Generación de Horarios - Test"
echo "   Algoritmo Genético"
echo "================================================"
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -d "backend" ]; then
    echo -e "${RED}Error: Ejecuta este script desde el directorio raíz del proyecto${NC}"
    exit 1
fi

cd backend

# Activar entorno virtual
if [ -d "venv" ]; then
    echo -e "${BLUE}Activando entorno virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: No se encontró el entorno virtual. Ejecuta setup.sh primero${NC}"
    exit 1
fi

# Verificar que hay datos
echo -e "${BLUE}Verificando datos en la base de datos...${NC}"
CLASSES_COUNT=$(python manage.py shell -c "from schedule_app.models import Class; print(Class.objects.count())" 2>/dev/null)

if [ "$CLASSES_COUNT" = "0" ] || [ -z "$CLASSES_COUNT" ]; then
    echo -e "${RED}No hay clases en la base de datos.${NC}"
    echo -e "${BLUE}¿Deseas importar el archivo XML de prueba? (s/n)${NC}"
    read -r IMPORT
    
    if [ "$IMPORT" = "s" ] || [ "$IMPORT" = "S" ]; then
        if [ -f "../pu-fal07-cs.xml" ]; then
            echo -e "${BLUE}Importando datos desde pu-fal07-cs.xml...${NC}"
            python manage.py shell << EOF
from django.core.files.uploadedfile import SimpleUploadedFile
from schedule_app.xml_parser import import_xml_view
from django.test import RequestFactory
import os

# Leer el archivo XML
with open('../pu-fal07-cs.xml', 'rb') as f:
    xml_content = f.read()

# Crear un request simulado
factory = RequestFactory()
request = factory.post('/api/import-xml/')
request.FILES['file'] = SimpleUploadedFile('pu-fal07-cs.xml', xml_content)
request.POST = {'clear_existing': 'true'}

# Ejecutar la importación
response = import_xml_view(request)
print(f"Importación completada con código: {response.status_code}")
EOF
            echo -e "${GREEN}Importación completada${NC}"
        else
            echo -e "${RED}No se encontró el archivo pu-fal07-cs.xml${NC}"
            exit 1
        fi
    else
        echo -e "${RED}No se puede continuar sin datos${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Datos encontrados en la base de datos${NC}"
echo ""

# Menú de opciones
echo -e "${BLUE}Selecciona una opción:${NC}"
echo "1) Generar horario con parámetros por defecto (rápido)"
echo "2) Generar horario optimizado (más generaciones)"
echo "3) Generar horario con parámetros personalizados"
echo "4) Ver horarios existentes"
echo "5) Ver resumen de un horario"
echo ""
read -p "Opción: " OPTION

case $OPTION in
    1)
        echo -e "${BLUE}Generando horario con parámetros por defecto...${NC}"
        python manage.py generate_schedule --name "Horario Test Rápido" --population 50 --generations 100
        ;;
    2)
        echo -e "${BLUE}Generando horario optimizado (esto puede tomar varios minutos)...${NC}"
        python manage.py generate_schedule --name "Horario Optimizado" --population 150 --generations 300 --mutation-rate 0.15
        ;;
    3)
        echo -e "${BLUE}Parámetros personalizados:${NC}"
        read -p "Nombre del horario: " NAME
        read -p "Tamaño población (50-200): " POP
        read -p "Número de generaciones (100-500): " GEN
        read -p "Tasa de mutación (0.05-0.20): " MUT
        read -p "Tasa de cruce (0.7-0.95): " CROSS
        
        python manage.py generate_schedule \
            --name "$NAME" \
            --population "$POP" \
            --generations "$GEN" \
            --mutation-rate "$MUT" \
            --crossover-rate "$CROSS"
        ;;
    4)
        echo -e "${BLUE}Horarios existentes:${NC}"
        python manage.py shell -c "
from schedule_app.models import Schedule
schedules = Schedule.objects.all().order_by('-created_at')
if schedules:
    for s in schedules:
        print(f'ID: {s.id} | {s.name} | Fitness: {s.fitness_score:.2f} | Activo: {s.is_active}')
else:
    print('No hay horarios generados')
"
        ;;
    5)
        read -p "ID del horario: " SCHEDULE_ID
        echo -e "${BLUE}Resumen del horario ${SCHEDULE_ID}:${NC}"
        python manage.py shell << EOF
from schedule_app.models import Schedule
from schedule_app.schedule_generator import ScheduleGenerator

try:
    schedule = Schedule.objects.get(id=${SCHEDULE_ID})
    generator = ScheduleGenerator()
    generator.load_data()
    summary = generator.get_schedule_summary(schedule)
    
    print(f"\nHorario: {schedule.name}")
    print(f"Fitness: {schedule.fitness_score:.2f}")
    print(f"Asignaciones totales: {summary['total_assignments']}")
    print(f"Clases sin asignar: {summary['unassigned_classes']}")
    print(f"Instructores: {len(summary['instructor_schedules'])}")
    print(f"Aulas utilizadas: {len(summary['room_schedules'])}")
except Schedule.DoesNotExist:
    print("Horario no encontrado")
EOF
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Proceso completado${NC}"
echo ""
echo -e "${BLUE}Para ver los horarios generados en la API:${NC}"
echo "curl http://localhost:8000/api/schedules/"
echo ""
echo -e "${BLUE}Para obtener vista de calendario:${NC}"
echo "curl http://localhost:8000/api/schedules/1/calendar_view/"
