# Script de Prueba Completo del Sistema Limpio
# Ejecutar: .\test_final.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SISTEMA GENERACION - VERSION 3.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activar entorno
if (Test-Path "env\Scripts\Activate.ps1") {
    & "env\Scripts\Activate.ps1"
    Write-Host "* Entorno virtual activado" -ForegroundColor Green
} else {
    Write-Host "* No se encuentra el entorno virtual" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Ejecutar prueba
Write-Host "[Ejecutando prueba completa...]" -ForegroundColor Yellow
python test_sistema_limpio.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  * SISTEMA VALIDADO" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Archivos generados:" -ForegroundColor Cyan
    if (Test-Path "pu-fal07-llr_clean.xml") {
        $size = (Get-Item "pu-fal07-llr_clean.xml").Length / 1KB
        $sizeStr = "{0:N2}" -f $size
        Write-Host "  * pu-fal07-llr_clean.xml ($sizeStr KB)" -ForegroundColor Green
    }
    if (Test-Path "horario_final.json") {
        $size = (Get-Item "horario_final.json").Length / 1KB
        $sizeStr = "{0:N2}" -f $size
        Write-Host "  * horario_final.json ($sizeStr KB)" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Siguiente paso:" -ForegroundColor Yellow
    Write-Host "  Actualizar frontend para usar:" -ForegroundColor White
    Write-Host "  POST /api/schedules/generate-from-file/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ver GUIA_TECNICA.md para más detalles" -ForegroundColor White
    
} else {
    Write-Host ""
    Write-Host "* Prueba fallo" -ForegroundColor Red
    exit 1
}
