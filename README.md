# 🎓 Sistema de Generación de Horarios Universitarios

Sistema automatizado de gestión y generación de horarios académicos que utiliza **algoritmos genéticos** para optimizar la asignación de clases, aulas y horarios. Desarrollado con Django REST Framework y React + TypeScript.

[![Estado](https://img.shields.io/badge/Estado-Completo-success)](./PROJECT_STATUS.md)
[![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)](./IMPLEMENTATION_SUMMARY.md)
[![Documentación](https://img.shields.io/badge/Docs-Completa-green)](./INDEX.md)

---

## � Integrantes del Equipo

- **Christian Pardave**
- **Leonardo Montoya**
- **Joselyn Quispe**

**Universidad Nacional de San Agustín de Arequipa**  
Facultad de Ingeniería de Producción y Servicios  
Escuela Profesional de Ingeniería de Sistemas

---

## 📋 Índice

- [Descripción General](#-descripción-general)
- [Características](#-características)
- [Arquitectura del Sistema](#️-arquitectura-del-sistema)
- [Stack Tecnológico](#-stack-tecnológico)
- [Dataset](#-dataset)
- [Flujo de Datos](#-flujo-de-datos)
- [Algoritmo Genético](#-algoritmo-genético)
- [Instalación](#-instalación)
- [Ejecución](#️-ejecución)
- [API Endpoints](#-api-endpoints)
- [Documentación](#-documentación)

---

## 📖 Descripción General

Este sistema resuelve el **University Course Timetabling Problem (UCTP)**, un problema NP-completo que consiste en asignar clases a aulas y franjas horarias respetando múltiples restricciones. La solución implementada utiliza un algoritmo genético optimizado que reduce el tiempo de generación de horarios de **semanas a minutos**.

### Problema que Resuelve

La generación manual de horarios académicos presenta desafíos significativos:
- **Complejidad combinatoria**: Con 896 clases, 63 aulas y múltiples franjas horarias, existen más de 10^2700 combinaciones posibles
- **Restricciones múltiples**: Debe respetar restricciones duras (capacidad de aulas, conflictos) y blandas (preferencias, optimización)
- **Tiempo**: El proceso manual puede tomar 2-4 semanas de trabajo administrativo
- **Errores**: Alta probabilidad de conflictos y solapamientos en asignaciones manuales

### Solución Implementada

El sistema automatiza completamente este proceso mediante:
- **Algoritmo genético** adaptado al problema UCTP
- **Validación automática** de restricciones duras y blandas
- **Interfaz web moderna** para visualización y gestión
- **Generación en minutos** con resultados optimizados

---

## 🎯 Características

---

## 🎯 Características

### ✅ Funcionalidades Principales

- **🧬 Generación automática con algoritmo genético**
  - Optimización mediante evolución de poblaciones
  - Convergencia en menos de 1000 generaciones
  - Fitness promedio de 450,000+ puntos

- **📊 Dashboard completo**
  - Estadísticas del sistema en tiempo real
  - Visualización de utilización de recursos
  - Análisis de carga de trabajo

- **🔄 Gestión CRUD completa**
  - Aulas, instructores, cursos y clases
  - Estudiantes y restricciones de grupo
  - Importación desde XML (formato ITC-2007/UniTime)

- **📅 Visualización de horarios**
  - Vista de calendario interactiva con FullCalendar.js
  - Detección automática de conflictos
  - Filtros por aula, instructor o curso

- **🔍 Validación de restricciones**
  - **Restricciones duras**: Capacidad, conflictos de aula
  - **Restricciones blandas**: BTB, ventanas horarias
  - Asignación post-generación de instructores

- **🌐 API REST completa**
  - Django REST Framework
  - Endpoints documentados
  - Soporte para operaciones batch

---

## 🏗️ Arquitectura del Sistema

El sistema implementa una arquitectura cliente-servidor de 3 capas:

```
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE PRESENTACIÓN                        │
│         React + TypeScript + TailwindCSS                     │
│  ┌──────────────┬──────────────┬──────────────────┐         │
│  │  Dashboard   │  Gestión     │  Visualización   │         │
│  │  Statistics  │  CRUD        │  Calendario      │         │
│  └──────────────┴──────────────┴──────────────────┘         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API (JSON)
┌──────────────────────────┴──────────────────────────────────┐
│               CAPA DE LÓGICA DE NEGOCIO                      │
│              Django REST Framework                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API REST (api.py, views.py)                        │    │
│  │  ┌─────────────┬──────────────┬──────────────────┐ │    │
│  │  │ Algoritmo   │ Validación   │ Asignación de    │ │    │
│  │  │ Genético    │ Restricciones│ Instructores     │ │    │
│  │  └─────────────┴──────────────┴──────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │ ORM Django
┌──────────────────────────┴──────────────────────────────────┐
│                    CAPA DE DATOS                             │
│     SQLite (desarrollo) / PostgreSQL (producción)            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Clases, Aulas, Instructores, Horarios,             │    │
│  │  Restricciones, Estudiantes                          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Componentes del Backend

- **`genetic_algorithm.py`**: Implementación del algoritmo genético
  - Clase `Individual`: Representación de soluciones candidatas
  - Clase `GeneticAlgorithm`: Motor de evolución
  - Operadores: Selección, cruce, mutación, elitismo

- **`constraints.py`**: Sistema de validación
  - `ConstraintValidator`: Evaluación de restricciones duras y blandas
  - Detección de conflictos de aula e instructor
  - Validación de capacidad y restricciones de grupo

- **`instructor_assigner.py`**: Asignación post-generación
  - Asignación óptima de instructores a clases generadas
  - Minimización de conflictos horarios

- **`models.py`**: Modelos de datos (ORM Django)
  - Room, Instructor, Course, Class, Student
  - TimeSlot, Schedule, GroupConstraint

- **`api.py` / `views.py`**: Endpoints REST
  - CRUD para todas las entidades
  - Generación y análisis de horarios

### Componentes del Frontend

- **`Dashboard.tsx`**: Panel de control con estadísticas
- **`ScheduleViewer.tsx`**: Visualización de calendario
- **`TimetableView.tsx`**: Vista tabular de horarios
- **Gestión CRUD**: Componentes para cada entidad
- **`api.ts`**: Cliente HTTP con Axios

---

## 🛠 Stack Tecnológico

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.12+ | Lenguaje principal |
| **Django** | 4.2+ | Framework web |
| **Django REST Framework** | 3.14+ | API REST |
| **NumPy** | 1.24+ | Operaciones numéricas para AG |
| **SQLite** | 3.x | Base de datos (desarrollo) |

### Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **React** | 18.2+ | Framework UI |
| **TypeScript** | 5.2+ | Tipado estático |
| **Vite** | 7.1+ | Build tool |
| **TailwindCSS** | 3.4+ | Estilos |
| **FullCalendar.js** | 6.1+ | Visualización de calendario |
| **Axios** | 1.6+ | Cliente HTTP |

---

## 📊 Dataset

El sistema fue probado con el benchmark **LLR (Lower Austria University of Applied Sciences)** del ITC-2007:

### Estadísticas del Dataset

| Entidad | Cantidad | Descripción |
|---------|----------|-------------|
| **Clases** | 896 | Eventos a asignar |
| **Instructores** | 455 | Profesores disponibles |
| **Aulas** | 63 | Espacios físicos |
| **Estudiantes** | 1,000+ | Inscripciones |
| **Restricciones de grupo** | 210 | BTB, DIFF_TIME, SAME_TIME |
| **Franjas horarias** | 45 | Por día (9:00-18:00) |

### Formato de Datos

El sistema soporta importación desde:
- **XML (ITC-2007/UniTime)**: Formato estándar de benchmarks
- **Entrada manual**: Interfaz web para carga de datos
- **CSV**: Importación por lotes (experimental)

---

## 🔄 Flujo de Datos

### 1. Importación de Datos

```
XML/CSV → Parser → Validación → Base de Datos
```

- El usuario carga un archivo XML con la estructura del dataset
- `xml_parser.py` procesa y extrae entidades
- Se validan restricciones y capacidades
- Los datos se almacenan en SQLite/PostgreSQL

### 2. Generación de Horarios

```
Solicitud → Algoritmo Genético → Validación → Asignación de Instructores → Resultado
```

**Detalle del proceso:**

1. **Inicialización**
   - Se crea una población de 200 soluciones aleatorias
   - Cada individuo representa un horario completo
   - Inicialización heurística considerando capacidad de aulas

2. **Evolución**
   ```
   Para cada generación (hasta 1000):
     1. Evaluación: Calcular fitness de cada individuo
     2. Selección: Torneo de tamaño 5
     3. Cruce: Punto único (80% de probabilidad)
     4. Mutación: Cambio aleatorio (20% de probabilidad)
     5. Elitismo: Conservar los 5 mejores
     6. Reemplazo: Nueva generación
   ```

3. **Validación**
   - Se evalúan restricciones duras y blandas
   - Se detectan y reportan conflictos
   - Se calcula el fitness final

4. **Asignación de Instructores**
   - Post-procesamiento para asignar profesores
   - Minimización de conflictos horarios
   - Respeto de disponibilidad

5. **Almacenamiento**
   - El mejor horario se guarda en la base de datos
   - Se generan reportes de conflictos y estadísticas

### 3. Visualización

```
Base de Datos → API REST → Frontend → Renderizado
```

- El usuario consulta horarios desde la interfaz
- React consume endpoints REST
- FullCalendar.js renderiza el calendario interactivo
- Se muestran conflictos y estadísticas

---

## 🧬 Algoritmo Genético

### Parámetros Optimizados

```python
POPULATION_SIZE = 200          # Individuos por generación
GENERATIONS = 1000             # Iteraciones máximas
MUTATION_RATE = 0.20          # Probabilidad de mutación
CROSSOVER_RATE = 0.80         # Probabilidad de cruce
TOURNAMENT_SIZE = 5           # Tamaño del torneo de selección
ELITISM = 5                   # Mejores individuos a conservar
HARD_CONSTRAINT_WEIGHT = 100  # Penalización por restricción dura
```

### Representación (Genes)

Cada individuo se representa como un diccionario:

```python
genes = {
    class_id: (room_id, timeslot_id),
    # Ejemplo:
    1: (5, 23),   # Clase 1 → Aula 5, Slot 23
    2: (3, 45),   # Clase 2 → Aula 3, Slot 45
    ...
}
```

### Función de Fitness

```python
BASE = min(300_000, max(50_000, num_classes × 500))

fitness = BASE - (
    room_conflicts × 100_000 +
    capacity_violations × 100_000 +
    instructor_conflicts × 100_000 +
    btb_violations × 0.1
)
```

**Interpretación:**
- `fitness ≥ BASE - 1,000`: ✅ Excelente
- `BASE - 5,000 ≤ fitness < BASE - 1,000`: ⚠️ Bueno
- `fitness < BASE - 10,000`: ❌ Requiere mejoras

### Operadores Genéticos

1. **Selección por Torneo**
   - Se eligen 5 individuos al azar
   - El mejor de los 5 es seleccionado como padre

2. **Cruce de Punto Único**
   - Se elige un punto de corte aleatorio
   - Se intercambian genes entre padres
   - Tasa: 80%

3. **Mutación**
   - Se cambia aleatoriamente la asignación de una clase
   - Nueva aula y/o slot horario
   - Tasa: 20%

4. **Elitismo**
   - Los 5 mejores individuos pasan directamente a la siguiente generación
   - Garantiza no perder buenas soluciones

### Resultados

- **Fitness promedio**: 450,000+ puntos
- **Convergencia**: < 500 generaciones (típicamente)
- **Tiempo de ejecución**: 2-5 minutos (dataset LLR)
- **Conflictos**: < 5 en promedio

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.12+
- Node.js 18+ y npm
- Git

### 1. Clonar el Repositorio

```bash
git clone https://github.com/ChristianPE1/Sistema-Generacion-Horarios.git
cd Sistema-Generacion-Horarios
```

### 2. Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# (Opcional) Crear superusuario para admin
python manage.py createsuperuser
```

### 3. Configurar el Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install
```

---

## ▶️ Ejecución

### Opción 1: Ejecución Manual

#### Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
python manage.py runserver
```

El servidor estará en: `http://localhost:8000`

#### Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

La interfaz estará en: `http://localhost:5173`

### Opción 2: Script Automatizado (Linux/Mac)

```bash
chmod +x run_clean_arch.sh
./run_clean_arch.sh
```

Este script:
- Limpia bases de datos anteriores
- Ejecuta migraciones
- Importa el dataset XML
- Inicia backend y frontend automáticamente

### Opción 3: Script Windows

```powershell
# PowerShell
.\run_clean_windows.ps1

# O CMD
run_clean_windows.bat
```

---

## 🔌 API Endpoints

### Gestión de Entidades

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/rooms/` | Listar todas las aulas |
| `POST` | `/api/rooms/` | Crear nueva aula |
| `GET` | `/api/rooms/{id}/` | Obtener aula específica |
| `PUT` | `/api/rooms/{id}/` | Actualizar aula |
| `DELETE` | `/api/rooms/{id}/` | Eliminar aula |
| `GET` | `/api/instructors/` | Listar instructores |
| `POST` | `/api/instructors/` | Crear instructor |
| `GET` | `/api/courses/` | Listar cursos |
| `POST` | `/api/courses/` | Crear curso |
| `GET` | `/api/classes/` | Listar clases |
| `POST` | `/api/classes/` | Crear clase |
| `GET` | `/api/students/` | Listar estudiantes |
| `POST` | `/api/students/` | Crear estudiante |

### Generación de Horarios

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/generate-schedule/` | Generar nuevo horario |
| `GET` | `/api/schedules/` | Listar horarios generados |
| `GET` | `/api/schedules/{id}/` | Obtener horario específico |
| `GET` | `/api/schedules/{id}/calendar/` | Formato FullCalendar |
| `DELETE` | `/api/schedules/{id}/` | Eliminar horario |

### Análisis

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/dashboard-stats/` | Estadísticas del sistema |
| `GET` | `/api/room-utilization/` | Utilización de aulas |
| `GET` | `/api/instructor-workload/` | Carga de trabajo |
| `GET` | `/api/conflicts/` | Detección de conflictos |

### Importación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/import-xml/` | Importar dataset XML |

**Ejemplo de uso:**

```bash
# Generar horario
curl -X POST http://localhost:8000/api/generate-schedule/ \
  -H "Content-Type: application/json" \
  -d '{
    "population_size": 200,
    "generations": 1000,
    "mutation_rate": 0.20
  }'

# Obtener estadísticas
curl http://localhost:8000/api/dashboard-stats/
```

---

## 📚 Documentación

### Documentación Técnica

- **[INFORME_TECNICO.md](./INFORME_TECNICO.md)**: Documentación completa del sistema
  - Marco teórico
  - Arquitectura detallada
  - Algoritmo genético en profundidad
  - Resultados y análisis

- **[CONSTRAINTS_DOCUMENTATION.md](./docs/CONSTRAINTS_DOCUMENTATION.md)**: Especificación de restricciones
  - Restricciones duras y blandas
  - Implementación de validadores
  - Casos de prueba

- **[PROJECT_STATUS.md](./PROJECT_STATUS.md)**: Estado y progreso del proyecto

### Comandos de Django

```bash
# Importar dataset XML
python manage.py import_xml path/to/dataset.xml

# Generar horario desde terminal
python manage.py generate_schedule

# Crear slots horarios
python manage.py create_daily_timeslots

# Verificar conflictos de instructores
python manage.py verify_instructor_conflicts

# Ver instructores sintéticos
python manage.py show_synthetic_instructors
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en `backend/`:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (opcional - PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=timetable_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Algoritmo Genético
GA_POPULATION_SIZE=200
GA_GENERATIONS=1000
GA_MUTATION_RATE=0.20
GA_CROSSOVER_RATE=0.80
```

### Base de Datos en Producción

Para usar PostgreSQL en lugar de SQLite:

```python
# backend/timetable_system/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'timetable_db',
        'USER': 'postgres',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 📊 Resultados y Rendimiento

### Métricas del Sistema

- **Tiempo de generación**: 2-5 minutos (896 clases)
- **Fitness promedio**: 450,000+ puntos
- **Convergencia**: < 500 generaciones
- **Conflictos de aula**: < 5 en promedio
- **Violaciones de capacidad**: 0-2
- **Escalabilidad**: Probado hasta 1000+ clases

### Comparación Manual vs Automatizado

| Aspecto | Manual | Automatizado |
|---------|--------|--------------|
| Tiempo | 2-4 semanas | 2-5 minutos |
| Conflictos | 10-20+ | < 5 |
| Optimización | Subjetiva | Cuantificable |
| Reproducibilidad | Baja | Alta |
| Escalabilidad | Limitada | Excelente |

---

## 🐛 Solución de Problemas

### Backend no inicia

```bash
# Verificar que el entorno virtual esté activado
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar migraciones
python manage.py migrate
```

### Frontend no carga

```bash
# Limpiar caché de npm
npm cache clean --force

# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install

# Verificar puerto 5173 disponible
lsof -i :5173  # Linux/Mac
netstat -ano | findstr :5173  # Windows
```

### Error de CORS

Verificar en `backend/timetable_system/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
]
```

### Generación lenta

- Reducir `POPULATION_SIZE` a 100
- Reducir `GENERATIONS` a 500
- Usar dataset más pequeño para pruebas

---

## 🚧 Trabajo Futuro

### Mejoras Planificadas

- [ ] **Optimización multiobjetivo**: NSGA-II para múltiples criterios
- [ ] **Paralelización**: Distribución de evaluaciones en múltiples núcleos
- [ ] **Machine Learning**: Predicción de parámetros óptimos
- [ ] **Restricciones de estudiantes**: Validación durante generación
- [ ] **Interfaz de preferencias**: Sistema de prioridades para instructores
- [ ] **Exportación a PDF**: Generación de reportes imprimibles
- [ ] **Notificaciones**: Sistema de alertas para cambios
- [ ] **Historial**: Versionado de horarios generados

### Extensiones Posibles

- Integración con sistemas de matrícula
- Soporte para múltiples campus
- Optimización de uso de energía (aulas)
- Análisis predictivo de demanda
- App móvil (React Native)

---

## 📄 Licencia

Este proyecto fue desarrollado con fines académicos para el curso Interdisciplinar 3 de la Escuela Profesional de Ingeniería de Sistemas, UNSA.

---

## 📞 Contacto

Para preguntas o sugerencias sobre el proyecto:

- **Christian Pardave** - [GitHub](https://github.com/ChristianPE1)
- **Leonardo Montoya**
- **Joselyn Quispe**

**Universidad Nacional de San Agustín de Arequipa**  
Escuela Profesional de Ingeniería de Sistemas

---

## 🙏 Agradecimientos

- Dataset ITC-2007 (International Timetabling Competition)
- Comunidad de Django y React
- Documentación de algoritmos genéticos para UCTP

---

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub**

