# Script de prueba para generación de horarios - Windows PowerShell
# Uso: .\test_schedule.ps1

$BACKEND_DIR = "d:\Documentos\UNSA CICLO 10\INTERDISCIPLINAR 3\Sistema-Generacion-Horarios\backend"
$PYTHON_EXE = "..\env\Scripts\python.exe"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Sistema de Generación de Horarios" -ForegroundColor Cyan
Write-Host " Algoritmo Genético - Test Rápido" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio backend
Set-Location $BACKEND_DIR

# Verificar datos
Write-Host "Verificando datos en la base de datos..." -ForegroundColor Yellow
& $PYTHON_EXE manage.py shell -c "from schedule_app.models import Class; print(f'Clases en BD: {Class.objects.count()}')"

Write-Host ""
Write-Host "Selecciona el modo de prueba:" -ForegroundColor Yellow
Write-Host "1) Rápido (50 población, 100 generaciones) - ~1 min" -ForegroundColor Green
Write-Host "2) Normal (100 población, 200 generaciones) - ~3 min" -ForegroundColor Green
Write-Host "3) Optimizado (150 población, 300 generaciones) - ~7 min" -ForegroundColor Green
Write-Host "4) Intensivo (200 población, 500 generaciones) - ~15 min" -ForegroundColor Green
Write-Host ""

$opcion = Read-Host "Opción"

switch ($opcion) {
    "1" {
        Write-Host "Ejecutando prueba rápida..." -ForegroundColor Cyan
        & $PYTHON_EXE manage.py generate_schedule --name "Test Rápido" --population 50 --generations 100
    }
    "2" {
        Write-Host "Ejecutando prueba normal..." -ForegroundColor Cyan
        & $PYTHON_EXE manage.py generate_schedule --name "Test Normal" --population 100 --generations 200
    }
    "3" {
        Write-Host "Ejecutando prueba optimizada..." -ForegroundColor Cyan
        & $PYTHON_EXE manage.py generate_schedule --name "Test Optimizado" --population 150 --generations 300
    }
    "4" {
        Write-Host "Ejecutando prueba intensiva..." -ForegroundColor Cyan
        & $PYTHON_EXE manage.py generate_schedule --name "Test Intensivo" --population 200 --generations 500
    }
    default {
        Write-Host "Opción inválida" -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host " Horarios Generados" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
& $PYTHON_EXE manage.py shell -c "
from schedule_app.models import Schedule
schedules = Schedule.objects.all().order_by('-created_at')
if schedules:
    for s in schedules:
        print(f'ID: {s.id} | {s.name} | Fitness: {s.fitness_score:.2f}')
else:
    print('No hay horarios generados')
"

Write-Host ""
Write-Host "Para ver detalles del último horario:" -ForegroundColor Yellow
Write-Host "  .\env\Scripts\python.exe manage.py shell -c 'from schedule_app.models import Schedule; s = Schedule.objects.latest(\"created_at\"); print(f\"Fitness: {s.fitness_score:.2f}\")'" -ForegroundColor Gray
