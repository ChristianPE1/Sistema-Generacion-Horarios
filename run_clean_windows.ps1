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
# Uso: 
#      .\run_clean_windows.ps1                    # Con heurísticas (más lento pero mejor)
#      .\run_clean_windows.ps1 -NoHeuristics     # Sin heurísticas (más rápido)
# ========================================

param(
    [switch]$NoHeuristics = $true
)

Write-Host ""
Write-Host "========================================"
Write-Host " LIMPIEZA Y GENERACION DE HORARIOS" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

# Cambiar al directorio del script
Set-Location $PSScriptRoot

Write-Host "[1/8] Verificando estructura del proyecto..." -ForegroundColor Yellow

if (!(Test-Path "env")) {
    Write-Host "ERROR: No se encontro el virtualenv en env" -ForegroundColor Red
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

Write-Host "[2/8] Activando virtualenv..." -ForegroundColor Yellow
& "env\Scripts\Activate.ps1"
Write-Host "[OK] Virtualenv activado" -ForegroundColor Green
Write-Host ""

Write-Host "[3/8] Eliminando base de datos anterior..." -ForegroundColor Yellow
Set-Location backend
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "[OK] Base de datos eliminada" -ForegroundColor Green
} else {
    Write-Host "[INFO] No habia base de datos anterior" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[4/8] Creando nueva base de datos..." -ForegroundColor Yellow
python manage.py migrate --run-syncdb
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la migracion de la base de datos" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Base de datos creada" -ForegroundColor Green
Write-Host ""

Write-Host "[5/8] Cargando dataset LLR (esto puede tomar 2-3 minutos)..." -ForegroundColor Yellow
python manage.py import_xml ..\pu-fal07-llr.xml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la carga del XML" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Dataset cargado" -ForegroundColor Green
Write-Host ""

Write-Host "[6/8] Creando timeslots individuales por dia (Lun-Sab)..." -ForegroundColor Yellow
Write-Host "[INFO] Esto puede tomar 3-5 minutos..." -ForegroundColor Gray
python manage.py create_daily_timeslots --clear-existing
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la creacion de timeslots diarios" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Timeslots diarios creados" -ForegroundColor Green
Write-Host ""

Write-Host "[7/8] Expandiendo disponibilidad de aulas..." -ForegroundColor Yellow
python manage.py expand_availability --expand-rooms
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la expansion de aulas" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Disponibilidad de aulas expandida" -ForegroundColor Green
Write-Host ""

Write-Host "[8/8] Ejecutando algoritmo genetico..." -ForegroundColor Yellow
Write-Host ""
Write-Host "PARAMETROS:" -ForegroundColor Cyan
Write-Host "- Poblacion: 100 individuos"
Write-Host "- Generaciones: 400"
Write-Host "- Mutacion: 20%"
Write-Host "- Dataset: LLR (896 clases, 455 instructores, 63 aulas)"

if ($NoHeuristics) {
    Write-Host "- Heuristicas: DESACTIVADAS (inicializacion rapida)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tiempo estimado: 5-8 minutos" -ForegroundColor Yellow
    Write-Host ""
    python manage.py generate_schedule --name "LLR Clean Run" --population 200 --generations 1000 --no-heuristics
} else {
    Write-Host "- Heuristicas: ACTIVADAS (mejor calidad inicial)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tiempo estimado: 15-20 minutos" -ForegroundColor Yellow
    Write-Host ""
    python manage.py generate_schedule --name "LLR Clean Run" --population 100 --generations 400
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la generacion del horario" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
