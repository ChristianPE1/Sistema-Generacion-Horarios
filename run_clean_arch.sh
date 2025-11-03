#!/bin/bash

# ========================================
# Script Bash: Limpieza y Carga (Arch Linux)
# ========================================
# Este script limpia la base de datos, carga el dataset LLR y ejecuta el algoritmo genetico
#
# Requisitos:
# - Python 3.8+ instalado
# - Virtualenv creado en backend/env
# - Archivo pu-fal07-llr.xml en la raiz del proyecto
#
# Uso:
#      ./run_clean_arch.sh                    # Con heurísticas (más lento pero mejor)
#      ./run_clean_arch.sh --no-heuristics    # Sin heurísticas (más rápido)
# ========================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_step() {
    echo -e "${YELLOW}[$1/$2]${NC} $3"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_info() {
    echo -e "${CYAN}INFO:${NC} $1"
}

# Parsear argumentos
NO_HEURISTICS=false
if [[ "$1" == "--no-heuristics" ]]; then
    NO_HEURISTICS=true
fi

echo ""
echo "========================================"
echo -e " ${CYAN}LIMPIEZA Y GENERACION DE HORARIOS${NC}"
echo "========================================"
echo ""

# Cambiar al directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_step "1" "8" "Verificando estructura del proyecto..."

if [[ ! -d "env" ]]; then
    print_error "No se encontró el virtualenv en 'env'"
    echo ""
    echo "Por favor ejecuta primero:"
    echo "  cd backend"
    echo "  python -m venv env"
    echo "  source env/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

if [[ ! -f "pu-fal07-llr.xml" ]]; then
    print_error "No se encontró el archivo pu-fal07-llr.xml"
    echo ""
    echo "Por favor coloca el archivo XML en la raíz del proyecto"
    echo ""
    exit 1
fi

print_success "Estructura verificada"
echo ""

print_step "2" "8" "Activando virtualenv..."
source env/bin/activate
print_success "Virtualenv activado"
echo ""

print_step "3" "8" "Eliminando base de datos anterior..."
cd backend
if [[ -f "db.sqlite3" ]]; then
    rm -f "db.sqlite3"
    print_success "Base de datos eliminada"
else
    print_info "No había base de datos anterior"
fi
echo ""

print_step "4" "8" "Creando nueva base de datos..."
python manage.py migrate --run-syncdb
print_success "Base de datos creada"
echo ""

print_step "5" "8" "Cargando dataset LLR (esto puede tomar 2-3 minutos)..."
python manage.py import_xml ../pu-fal07-llr.xml
print_success "Dataset cargado"
echo ""

print_step "6" "8" "Creando timeslots individuales por día (Lun-Sab)..."
echo "INFO: Esto puede tomar 3-5 minutos..."
python manage.py create_daily_timeslots --clear-existing
print_success "Timeslots diarios creados"
echo ""

print_step "7" "8" "Expandiendo disponibilidad de aulas..."
python manage.py expand_availability --expand-rooms
print_success "Disponibilidad de aulas expandida"
echo ""

print_step "8" "8" "Ejecutando algoritmo genético..."
echo ""
echo -e "${CYAN}PARÁMETROS:${NC}"
echo "- Población: 100 individuos"
echo "- Generaciones: 400"
echo "- Mutación: 20%"
echo "- Dataset: LLR (896 clases, 455 instructores, 63 aulas)"

if [[ "$NO_HEURISTICS" == true ]]; then
    echo -e "- Heurísticas: ${YELLOW}DESACTIVADAS${NC} (inicialización rápida)"
    echo ""
    echo -e "${YELLOW}Tiempo estimado: 5-8 minutos${NC}"
    echo ""
    python manage.py generate_schedule --name "LLR Clean Run" --population 200 --generations 1000 --no-heuristics
else
    echo -e "- Heurísticas: ${GREEN}ACTIVADAS${NC} (mejor calidad inicial)"
    echo ""
    echo -e "${YELLOW}Tiempo estimado: 15-20 minutos${NC}"
    echo ""
    python manage.py generate_schedule --name "LLR Clean Run" --population 100 --generations 400
fi

echo ""
echo -e "${GREEN}========================================"
echo -e " PROCESO COMPLETADO"
echo -e "=======================================${NC}"
echo ""
echo -e "${GREEN}El horario fue generado exitosamente${NC}"
echo ""
echo "Para ver los resultados:"
echo "1. Inicia el servidor: python manage.py runserver"
echo "2. Abre el navegador en: http://localhost:8000"
echo "3. Ve a la sección 'Ver Horarios'"
echo ""

# Desactivar virtualenv
deactivate
