# Guía de Ejecución en Windows

Esta guía te ayudará a ejecutar el sistema de generación de horarios desde cero en Windows.

## 📋 Requisitos Previos

### 1. Software Necesario

- **Python 3.8 o superior**
  - Descargar desde: https://www.python.org/downloads/
  - ⚠️ **IMPORTANTE**: Durante la instalación, marca la opción **"Add Python to PATH"**

- **Git** (opcional, para clonar el repositorio)
  - Descargar desde: https://git-scm.com/download/win

### 2. Verificar Instalación de Python

Abre **PowerShell** o **CMD** y ejecuta:

```powershell
python --version
```

Deberías ver algo como: `Python 3.10.x` o superior.

---

## 🚀 Configuración Inicial (Solo la Primera Vez)

### Paso 1: Clonar o Descargar el Proyecto

**Opción A: Con Git**
```powershell
git clone https://github.com/ChristianPE1/Sistema-Generacion-Horarios.git
cd Sistema-Generacion-Horarios
```

**Opción B: Sin Git**
1. Descarga el ZIP desde GitHub
2. Extrae en una carpeta (ej: `C:\Users\TuNombre\proyecto-ti3`)
3. Abre PowerShell en esa carpeta (Shift + Clic derecho > "Abrir ventana de PowerShell aquí")

### Paso 2: Crear el Virtual Environment

```powershell
cd backend
python -m venv venv
```

### Paso 3: Activar el Virtual Environment

**En PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**En CMD:**
```cmd
venv\Scripts\activate.bat
```

**⚠️ Nota para PowerShell:** Si recibes un error de "ejecución de scripts deshabilitada", ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 4: Instalar Dependencias

```powershell
pip install -r requirements.txt
```

Esto instalará Django, Django REST Framework y otras librerías necesarias.

### Paso 5: Verificar el Archivo XML

Asegúrate de que el archivo `pu-fal07-llr.xml` esté en la **raíz del proyecto** (no en la carpeta `backend`).

```
proyecto-ti3/
├── backend/
│   ├── venv/
│   ├── manage.py
│   └── ...
├── pu-fal07-llr.xml  ← Aquí debe estar
├── run_clean_windows.bat
└── run_clean_windows.ps1
```

---

## 🔄 Ejecución Limpia (Cada Vez que Quieras Probar)

Cada vez que quieras hacer una prueba limpia desde cero (limpiar DB, recargar XML, ejecutar algoritmo), usa uno de estos métodos:

### Método 1: Script Automático (.bat)

**Doble clic** en el archivo `run_clean_windows.bat` en la raíz del proyecto.

**O desde CMD:**
```cmd
run_clean_windows.bat
```

### Método 2: Script Automático (.ps1)

**Clic derecho** en `run_clean_windows.ps1` > **"Ejecutar con PowerShell"**

**O desde PowerShell:**
```powershell
.\run_clean_windows.ps1
```

### Método 3: Paso a Paso Manual

Si prefieres ejecutar cada comando manualmente:

```powershell
# 1. Activar venv
cd backend
.\venv\Scripts\Activate.ps1

# 2. Eliminar DB anterior
Remove-Item db.sqlite3 -Force

# 3. Crear nueva DB
python manage.py migrate --run-syncdb

# 4. Cargar XML
python manage.py import_xml ..\pu-fal07-llr.xml

# 5. Ejecutar algoritmo genético
python manage.py generate_schedule --name "LLR Test" --description "Prueba" --population 100 --generations 400
```

---

## 📊 Verificar Resultados

### 1. Iniciar el Servidor de Desarrollo

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. Abrir el Frontend

Abre tu navegador y ve a: **http://localhost:8000**

### 3. Ver el Horario Generado

1. En la interfaz web, ve a **"Ver Horarios"**
2. Selecciona el horario más reciente de la lista
3. Explora las asignaciones por aula
4. Verifica los conflictos detectados (marcados en rojo)

---

## 🛠️ Solución de Problemas Comunes

### Error: "Python no se reconoce como comando"

**Causa:** Python no está en el PATH.

**Solución:**
1. Reinstala Python marcando **"Add Python to PATH"**
2. O agrega manualmente Python al PATH:
   - Busca la carpeta de instalación (ej: `C:\Users\TuNombre\AppData\Local\Programs\Python\Python310`)
   - Agrégala a las variables de entorno del sistema

### Error: "No se puede ejecutar scripts en este sistema" (PowerShell)

**Causa:** PowerShell tiene restricciones de ejecución de scripts.

**Solución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "ModuleNotFoundError: No module named 'django'"

**Causa:** El virtualenv no está activado o las dependencias no están instaladas.

**Solución:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "File not found: pu-fal07-llr.xml"

**Causa:** El archivo XML no está en la ubicación correcta.

**Solución:**
Mueve el archivo `pu-fal07-llr.xml` a la **raíz del proyecto**, al mismo nivel que `run_clean_windows.bat`.

### El Algoritmo Tarda Mucho (>20 minutos)

**Causa:** Dataset LLR es grande (896 clases).

**Solución:**
- **Normal:** 10-15 minutos con población 100
- Si quieres más rápido (pero menor calidad): Reduce generaciones:
  ```powershell
  python manage.py generate_schedule --name "Test Rapido" --population 50 --generations 200
  ```

### El Fitness se Estanca

**Comportamiento esperado:** El algoritmo puede estancarse temporalmente.

**Qué hace el sistema:**
- Después de 30 generaciones sin mejora, aplica **diversity boost**
- Aumenta mutación temporalmente
- Inyecta nuevos individuos
- Repara el mejor individuo

**Si se estanca persistentemente:**
- Verifica que no haya demasiados constraints imposibles de cumplir
- Revisa el log de la consola para ver qué constraints se violan más

---

## 📈 Parámetros del Algoritmo Genético

Puedes ajustar los parámetros según tus necesidades:

```powershell
python manage.py generate_schedule `
  --name "Nombre del Horario" `
  --description "Descripción" `
  --population 100 `
  --generations 400 `
  --mutation 0.2 `
  --crossover 0.8
```

### Recomendaciones por Tamaño de Dataset

| Clases | Población | Generaciones | Tiempo Estimado |
|--------|-----------|--------------|-----------------|
| < 100  | 50        | 100          | 1-2 min         |
| 100-300| 80        | 200          | 3-5 min         |
| 300-600| 100       | 300          | 8-12 min        |
| 600+   | 100       | 400          | 15-20 min       |

**Dataset LLR:** 896 clases → Usar población 100, generaciones 400

---

## 🔍 Comandos Útiles

### Ver Estadísticas de la Base de Datos

```powershell
python manage.py shell
```

Luego en el shell de Django:
```python
from schedule_app.models import Class, Room, Instructor, Schedule
print(f"Clases: {Class.objects.count()}")
print(f"Aulas: {Room.objects.count()}")
print(f"Instructores: {Instructor.objects.count()}")
print(f"Horarios generados: {Schedule.objects.count()}")
exit()
```

### Listar Horarios Generados

```powershell
python manage.py shell
```

```python
from schedule_app.models import Schedule
for s in Schedule.objects.all():
    print(f"{s.id}: {s.name} - Fitness: {s.fitness_score:.2f}")
exit()
```

### Eliminar un Horario Específico

```powershell
python manage.py shell
```

```python
from schedule_app.models import Schedule
Schedule.objects.filter(id=24).delete()  # Cambia 24 por el ID que quieras eliminar
exit()
```

---

## 📝 Notas Importantes

### Sobre las Preferencias

**CAMBIO RECIENTE:** El sistema ahora **ignora** las preferencias de aula y horario del XML durante la fase de asignación.

**Solo evalúa:**
- ✅ Conflictos de instructor (no puede estar en 2 lugares al mismo tiempo)
- ✅ Conflictos de aula (no pueden haber 2 clases en la misma aula al mismo tiempo)
- ✅ Capacidad de aula (debe ser >= al límite de estudiantes)
- ✅ Gaps de instructor (minimizar ventanas horarias)
- ✅ Group constraints (BTB, DIFF_TIME, SAME_TIME)

**Eliminado:**
- ❌ Preferencias de aula (`preference` en `ClassRoom`)
- ❌ Preferencias de horario (`preference` en `TimeSlot`)

**Razón:** Enfocarse en constraints estructurales mejora la convergencia del algoritmo.

### Sobre los Instructores

**NUEVO:** Los instructores se asignan **después** de que las clases tienen aula y horario.

- No afecta la validez del horario si una clase queda sin instructor
- Esto es normal cuando no hay suficientes instructores disponibles
- Puedes revisar qué clases quedaron sin instructor y asignarlos manualmente

---

## 🎯 Flujo de Trabajo Recomendado

1. **Limpieza:** Ejecuta `run_clean_windows.bat` para empezar desde cero
2. **Espera:** Deja que el algoritmo termine (10-15 min para LLR)
3. **Verifica:** Inicia el servidor y revisa el horario en el navegador
4. **Ajusta:** Si el fitness es bajo (<250k para LLR), prueba con más generaciones
5. **Itera:** Repite el proceso ajustando parámetros según sea necesario

---

## 📚 Documentación Adicional

- **Constraints del Sistema:** Ver `docs/CONSTRAINTS_DOCUMENTATION.md`
- **Mejoras de Fitness:** Ver `docs/MEJORAS_FITNESS_V2.md`
- **Changelog:** Ver `docs/CHANGELOG_V2.md`

---

## 🆘 Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa los logs de la consola durante la ejecución
2. Verifica que todos los requisitos estén instalados
3. Asegúrate de estar usando la rama correcta (`main` o `christiam`)
4. Consulta la documentación técnica en `docs/`

**¡Listo para generar horarios en Windows! 🚀**
