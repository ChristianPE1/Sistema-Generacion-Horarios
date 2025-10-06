#!/bin/bash

# Script para ejecutar el sistema completo
# Inicia tanto el backend como el frontend

set -e

echo "=========================================="
echo "🚀 Iniciando Sistema de Horarios"
echo "=========================================="

# Verificar que las instalaciones estén completas
if [ ! -d "backend/venv" ]; then
    echo "❌ Error: El entorno virtual no existe"
    echo "Por favor ejecuta primero: ./setup.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Error: Las dependencias de npm no están instaladas"
    echo "Por favor ejecuta primero: ./setup.sh"
    exit 1
fi

# Función para manejar Ctrl+C
cleanup() {
    echo ""
    echo "Deteniendo servidores..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar Backend
echo "Iniciando Backend (Django)..."
cd backend
source venv/bin/activate
python manage.py runserver > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Esperar a que Django inicie
sleep 3

# Iniciar Frontend
echo "Iniciando Frontend (React + Vite)..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Esperar a que Vite inicie
sleep 3

echo ""
echo "=========================================="
echo "✅ Sistema iniciado correctamente"
echo "=========================================="
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000/api/"
echo "👨‍💼 Admin Django: http://localhost:8000/admin/"
echo ""
echo "Logs disponibles en:"
echo "  - backend/logs/backend.log"
echo "  - frontend/logs/frontend.log"
echo ""
echo "Presiona Ctrl+C para detener los servidores"
echo ""

# Mantener el script en ejecución
wait
