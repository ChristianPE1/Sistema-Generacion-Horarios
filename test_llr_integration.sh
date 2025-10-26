#!/bin/bash

# Script de prueba para dataset LLR
# Autor: Christian PE
# Fecha: 20 de Octubre 2025

echo "[INFO] Iniciando prueba de integración LLR"
echo "========================================"

# 1. Activar entorno virtual
cd /home/christianpe/Documentos/ti3/proyecto-ti3
source venv/bin/activate

# 2. Aplicar migraciones
echo ""
echo "[INFO] Aplicando migraciones..."
cd backend
python manage.py makemigrations schedule_app
python manage.py migrate

# 3. Crear superusuario (opcional, skip si existe)
echo ""
echo "[INFO] Creando superusuario (skip si ya existe)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123');
    print('[OK] Superusuario creado');
else:
    print('[INFO] Superusuario ya existe');
"

# 4. Iniciar servidor en background
echo ""
echo "[INFO] Iniciando servidor Django..."
python manage.py runserver 8000 > /tmp/django_llr.log 2>&1 &
SERVER_PID=$!
echo "[OK] Servidor iniciado (PID: $SERVER_PID)"
sleep 5

# 5. Importar XML LLR
echo ""
echo "[INFO] Importando dataset LLR (pu-fal07-llr.xml)..."
cd ..
curl -X POST http://localhost:8000/api/import-xml/ \
  -F "file=@pu-fal07-llr.xml" \
  -F "clear_existing=true" \
  -H "Accept: application/json" \
  -s | python3 -m json.tool

# 6. Verificar estadísticas
echo ""
echo "[INFO] Verificando estadísticas..."
curl -s http://localhost:8000/api/dashboard/stats/ | python3 -m json.tool

# 7. Generar horario de prueba (opcional - toma tiempo)
read -p "¿Generar horario con heurísticas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[INFO] Generando horario con población 100, 100 generaciones..."
    cd backend
    python manage.py generate_schedule \
      --name "LLR Test Quick" \
      --population 100 \
      --generations 100 \
      --mutation-rate 0.15
fi

# 8. Cleanup
echo ""
echo "[INFO] Prueba completada. Deteniendo servidor..."
kill $SERVER_PID 2>/dev/null
echo "[OK] Servidor detenido"

echo ""
echo "========================================"
echo "[OK] Prueba de integración LLR completada"
echo "========================================"
echo ""
echo "Resumen:"
echo "  - Dataset: pu-fal07-llr.xml"
echo "  - Clases esperadas: 896"
echo "  - Instructores esperados: 455"
echo "  - Group constraints esperados: 282"
echo ""
echo "Para ejecutar generación completa:"
echo "  cd backend"
echo "  python manage.py generate_schedule \\"
echo "    --name 'LLR Full Test' \\"
echo "    --population 200 \\"
echo "    --generations 300"
