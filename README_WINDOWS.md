# 🚀 Ejecución Rápida en Windows

## Script Automático (Recomendado)

### Opción 1: Usando .bat (CMD)
```cmd
run_clean_windows.bat
```

### Opción 2: Usando PowerShell
```powershell
.\run_clean_windows.ps1
```

## ¿Qué Hace el Script?

1. ✅ Verifica estructura del proyecto
2. 🗑️ Elimina base de datos anterior (`db.sqlite3`)
3. 🔧 Crea nueva base de datos limpia
4. 📥 Carga dataset LLR desde `pu-fal07-llr.xml` (896 clases, 455 instructores, 63 aulas)
5. 🧬 Ejecuta algoritmo genético:
   - Población: 100 individuos
   - Generaciones: 400
   - Tiempo estimado: 10-15 minutos
6. 📊 Guarda horario generado en la base de datos

## Requisitos Previos

### Primera Vez
```powershell
# 1. Crear virtualenv
cd backend
python -m venv venv

# 2. Activar virtualenv
.\venv\Scripts\Activate.ps1  # PowerShell
# O
venv\Scripts\activate.bat    # CMD

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Archivo XML
Asegúrate de que `pu-fal07-llr.xml` esté en la **raíz del proyecto**.

## Ver Resultados

### Iniciar servidor
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### Abrir navegador
http://localhost:8000

### Ver horarios
1. Ve a "Ver Horarios"
2. Selecciona el horario más reciente
3. Explora asignaciones por aula
4. Los conflictos se muestran en **rojo**

## Parámetros Personalizados

Si quieres ajustar los parámetros:

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Eliminar DB anterior
Remove-Item db.sqlite3 -Force

# Crear nueva DB
python manage.py migrate --run-syncdb

# Cargar XML
python manage.py import_xml ..\pu-fal07-llr.xml

# Ejecutar con parámetros personalizados
python manage.py generate_schedule `
  --name "Mi Horario" `
  --description "Test con parámetros ajustados" `
  --population 80 `
  --generations 300 `
  --mutation 0.25
```

### Recomendaciones por Dataset

| Clases | Población | Generaciones | Tiempo |
|--------|-----------|--------------|--------|
| < 100  | 50        | 100          | 1-2 min |
| 100-300| 80        | 200          | 3-5 min |
| 300-600| 100       | 300          | 8-12 min |
| **LLR (896)** | **100** | **400** | **15-20 min** |

## 🆕 Nueva Arquitectura (2 Fases)

### Fase 1: Generación de Horario Base
- ✅ Asigna clases a aulas y horarios
- ✅ Evalúa SOLO:
  - Conflictos de aula
  - Capacidad de aula
  - Group constraints (BTB, DIFF_TIME, SAME_TIME)
- ❌ NO considera:
  - Preferencias de aula/horario (ignoradas)
  - Conflictos de instructor (se resuelven después)

### Fase 2: Asignación de Instructores
- ✅ Asigna instructores a clases ya programadas
- ✅ Considera:
  - Disponibilidad del instructor
  - Preferencias de horario del instructor
  - Distribución equitativa de carga
- ✅ **Permite clases sin instructor** (normal cuando no hay disponibilidad)

## 📚 Documentación Completa

- **Guía Detallada Windows**: `docs/GUIA_WINDOWS.md`
- **Constraints del Sistema**: `docs/CONSTRAINTS_DOCUMENTATION.md`
- **Mejoras de Fitness**: `docs/MEJORAS_FITNESS_V2.md`
- **Changelog**: `docs/CHANGELOG_V2.md`

## ⚠️ Solución de Problemas

### Error: "Python no se reconoce"
Reinstala Python marcando **"Add Python to PATH"**

### Error: "No se puede ejecutar scripts" (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "ModuleNotFoundError: No module named 'django'"
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### El algoritmo se estanca
**Normal** - El sistema aplica **diversity boost** después de 30 generaciones sin mejora:
- Aumenta mutación temporalmente
- Inyecta nuevos individuos
- Repara el mejor individuo

## 🎯 Flujo de Trabajo

```
1. Ejecutar script → 2. Esperar 15 min → 3. Iniciar servidor → 4. Ver en navegador
```

**¡Listo para generar horarios! 🚀**
