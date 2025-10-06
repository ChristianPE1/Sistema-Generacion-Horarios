#!/bin/bash

# Script de instalación para el Sistema de Generación de Horarios
# Este script configura el entorno completo del proyecto

set -e  # Detener en caso de error

echo "=========================================="
echo "🚀 Instalación del Sistema de Horarios"
echo "=========================================="

# Colores para la salida
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si estamos en el directorio correcto
if [ ! -f "pu-fal07-cs.xml" ]; then
    echo "❌ Error: No se encontró el archivo pu-fal07-cs.xml"
    echo "Por favor ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# ==========================================
# 1. BACKEND - Configuración de Python
# ==========================================
echo -e "\n${YELLOW}📦 Paso 1: Configurando Backend (Django)${NC}"

cd backend

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual de Python..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
else
    echo "El entorno virtual ya existe"
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "Instalando dependencias de Django..."
pip install -r requirements.txt

echo -e "${GREEN}✓${NC} Dependencias de Python instaladas"

# Crear base de datos
echo "Configurando base de datos..."
python manage.py makemigrations
python manage.py migrate

echo -e "${GREEN}✓${NC} Base de datos creada"

# Crear superusuario (opcional)
echo ""
read -p "¿Deseas crear un superusuario para el admin de Django? (s/n): " create_superuser
if [ "$create_superuser" == "s" ]; then
    python manage.py createsuperuser
fi

cd ..

# ==========================================
# 2. FRONTEND - Configuración de Node.js
# ==========================================
echo -e "\n${YELLOW}📦 Paso 2: Configurando Frontend (React + Vite)${NC}"

cd frontend

# Verificar que Node.js esté instalado
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js no está instalado"
    echo "Por favor instala Node.js desde https://nodejs.org/"
    exit 1
fi

echo "Node.js versión: $(node --version)"
echo "npm versión: $(npm --version)"

# Instalar dependencias
echo "Instalando dependencias de npm..."
npm install

echo -e "${GREEN}✓${NC} Dependencias de npm instaladas"

cd ..

# ==========================================
# 3. Resumen y siguientes pasos
# ==========================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Instalación Completada${NC}"
echo "=========================================="
echo ""
echo "Para ejecutar el sistema:"
echo ""
echo "1. Backend (Django):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "2. Frontend (React) - En otra terminal:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Accede a la aplicación:"
echo "   - Frontend: http://localhost:3000"
echo "   - API Backend: http://localhost:8000/api/"
echo "   - Admin Django: http://localhost:8000/admin/"
echo ""
echo "4. Importar datos XML:"
echo "   Ve a http://localhost:3000/import-xml"
echo "   Y sube el archivo pu-fal07-cs.xml"
echo ""
echo "=========================================="
