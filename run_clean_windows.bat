@echo off
REM ========================================
REM Script para Windows: Limpieza y Carga
REM ========================================
REM Este script limpia la base de datos, carga el dataset LLR y ejecuta el algoritmo genetico
REM 
REM Requisitos:
REM - Python 3.8+ instalado
REM - Virtualenv creado en backend\venv
REM - Archivo pu-fal07-llr.xml en la raiz del proyecto
REM
REM Uso: Doble clic o ejecutar desde cmd:
REM      run_clean_windows.bat
REM ========================================

echo.
echo ========================================
echo  LIMPIEZA Y GENERACION DE HORARIOS
echo ========================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo [1/6] Verificando estructura del proyecto...
if not exist "backend\venv" (
    echo ERROR: No se encontro el virtualenv en backend\venv
    echo.
    echo Por favor ejecuta primero:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "pu-fal07-llr.xml" (
    echo ERROR: No se encontro el archivo pu-fal07-llr.xml
    echo.
    echo Por favor coloca el archivo XML en la raiz del proyecto
    echo.
    pause
    exit /b 1
)

echo [OK] Estructura verificada
echo.

echo [2/6] Activando virtualenv...
call backend\venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el virtualenv
    pause
    exit /b 1
)
echo [OK] Virtualenv activado
echo.

echo [3/6] Eliminando base de datos anterior...
cd backend
if exist db.sqlite3 (
    del /f db.sqlite3
    echo [OK] Base de datos eliminada
) else (
    echo [INFO] No habia base de datos anterior
)
echo.

echo [4/6] Creando nueva base de datos...
python manage.py migrate --run-syncdb
if errorlevel 1 (
    echo ERROR: Fallo la migracion de la base de datos
    pause
    exit /b 1
)
echo [OK] Base de datos creada
echo.

echo [5/6] Cargando dataset LLR (esto puede tomar 2-3 minutos)...
python manage.py import_xml ..\pu-fal07-llr.xml
if errorlevel 1 (
    echo ERROR: Fallo la carga del XML
    pause
    exit /b 1
)
echo [OK] Dataset cargado
echo.

echo [6/6] Ejecutando algoritmo genetico...
echo.
echo PARAMETROS:
echo - Poblacion: 100 individuos
echo - Generaciones: 400
echo - Mutacion: 20%%
echo - Dataset: LLR (896 clases, 455 instructores, 63 aulas)
echo.
echo Tiempo estimado: 10-15 minutos
echo.
python manage.py generate_schedule --name "LLR Clean Run" --description "Generacion limpia desde Windows" --population 100 --generations 400
if errorlevel 1 (
    echo ERROR: Fallo la generacion del horario
    pause
    exit /b 1
)

echo.
echo ========================================
echo  PROCESO COMPLETADO
echo ========================================
echo.
echo El horario fue generado exitosamente
echo.
echo Para ver los resultados:
echo 1. Inicia el servidor: python manage.py runserver
echo 2. Abre el navegador en: http://localhost:8000
echo 3. Ve a la seccion "Ver Horarios"
echo.
pause
