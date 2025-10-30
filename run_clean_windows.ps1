# ========================================
# Script PowerShell: Limpieza y Carga
# ========================================
# Este script limpia la base de datos, carga el dataset LLR y ejecuta el algoritmo genetico
# 
# Requisitos:
# - Python 3.8+ instalado
# - Virtualenv creado en backend\venv
# - Archivo pu-fal07-llr.xml en la raiz del proyecto
#
# Uso: Clic derecho > "Ejecutar con PowerShell" o desde PowerShell:
#      .\run_clean_windows.ps1
# ========================================

Write-Host ""
Write-Host "========================================"
Write-Host " LIMPIEZA Y GENERACION DE HORARIOS" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

# Cambiar al directorio del script
Set-Location $PSScriptRoot

Write-Host "[1/6] Verificando estructura del proyecto..." -ForegroundColor Yellow

if (!(Test-Path "backend\venv")) {
    Write-Host "ERROR: No se encontro el virtualenv en backend\venv" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor ejecuta primero:"
    Write-Host "  cd backend"
    Write-Host "  python -m venv venv"
    Write-Host "  venv\Scripts\activate"
    Write-Host "  pip install -r requirements.txt"
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

if (!(Test-Path "pu-fal07-llr.xml")) {
    Write-Host "ERROR: No se encontro el archivo pu-fal07-llr.xml" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor coloca el archivo XML en la raiz del proyecto"
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "[OK] Estructura verificada" -ForegroundColor Green
Write-Host ""

Write-Host "[2/6] Activando virtualenv..." -ForegroundColor Yellow
& "backend\venv\Scripts\Activate.ps1"
Write-Host "[OK] Virtualenv activado" -ForegroundColor Green
Write-Host ""

Write-Host "[3/6] Eliminando base de datos anterior..." -ForegroundColor Yellow
Set-Location backend
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "[OK] Base de datos eliminada" -ForegroundColor Green
} else {
    Write-Host "[INFO] No habia base de datos anterior" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[4/6] Creando nueva base de datos..." -ForegroundColor Yellow
python manage.py migrate --run-syncdb
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la migracion de la base de datos" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Base de datos creada" -ForegroundColor Green
Write-Host ""

Write-Host "[5/6] Cargando dataset LLR (esto puede tomar 2-3 minutos)..." -ForegroundColor Yellow
python manage.py import_xml ..\pu-fal07-llr.xml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la carga del XML" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Dataset cargado" -ForegroundColor Green
Write-Host ""

Write-Host "[6/6] Ejecutando algoritmo genetico..." -ForegroundColor Yellow
Write-Host ""
Write-Host "PARAMETROS:" -ForegroundColor Cyan
Write-Host "- Poblacion: 100 individuos"
Write-Host "- Generaciones: 400"
Write-Host "- Mutacion: 20%"
Write-Host "- Dataset: LLR (896 clases, 455 instructores, 63 aulas)"
Write-Host ""
Write-Host "Tiempo estimado: 10-15 minutos" -ForegroundColor Yellow
Write-Host ""

python manage.py generate_schedule --name "LLR Clean Run" --description "Generacion limpia desde Windows" --population 100 --generations 400
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la generacion del horario" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " PROCESO COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "El horario fue generado exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "Para ver los resultados:"
Write-Host "1. Inicia el servidor: python manage.py runserver"
Write-Host "2. Abre el navegador en: http://localhost:8000"
Write-Host "3. Ve a la seccion 'Ver Horarios'"
Write-Host ""
Read-Host "Presiona Enter para salir"
