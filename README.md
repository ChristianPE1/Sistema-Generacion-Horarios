# Sistema de Generación de Horarios Universitarios

Sistema automatizado para generar horarios académicos optimizados utilizando un **sistema híbrido: Algoritmo Greedy + Algoritmo Genético**.

## Integrantes del Equipo

- **Christian Pardavé**
- **Leonardo Montoya**
- **Joselyn Quispe**

**Universidad Nacional de San Agustín de Arequipa**  
Escuela Profesional de Ciencia de la Computación

---

## Descripción del Sistema

Este sistema resuelve el problema de generación de horarios universitarios (University Course Timetabling Problem - UCTP), un problema NP-completo que consiste en asignar clases a aulas y franjas horarias respetando múltiples restricciones.

### Problema que Resuelve

- Asignación automática de clases a aulas disponibles
- Distribución equitativa del uso de aulas (evitar aulas vacías y sobrecargadas)
- Respeto de restricciones: capacidad, tipo de aula, límite de sesiones consecutivas
- Optimización del horario mediante evolución genética

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│              TypeScript + TailwindCSS + Vite                 │
│  ┌────────────┬───────────────┬────────────────────┐        │
│  │ Dashboard  │   Schedules   │  ScheduleViewer    │        │
│  │ (inicio)   │  (generación) │  (visualización)   │        │
│  └────────────┴───────────────┴────────────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST API (JSON)
┌──────────────────────────┴──────────────────────────────────┐
│                     BACKEND (Django)                         │
│              Django REST Framework + Python                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               generation_api_v2.py                    │   │
│  │  ┌────────────────┐    ┌─────────────────────────┐   │   │
│  │  │ schedule_builder│ →  │ Algoritmo Genético     │   │   │
│  │  │   (GREEDY)     │    │ (Refinamiento)         │   │   │
│  │  └────────────────┘    └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Archivos JSON/XML
┌──────────────────────────┴──────────────────────────────────┐
│                       DATOS                                  │
│   escuela.xml │ purdue_clean.xml │ schedules_history.json   │
└──────────────────────────────────────────────────────────────┘
```

---

## Sistema Híbrido: Greedy + Algoritmo Genético

### Fase 1: Inicialización Greedy (`schedule_builder.py`)

El algoritmo Greedy genera una **solución inicial válida** de forma rápida:

1. Carga datos del XML (aulas, instructores, clases, configuración)
2. Ordena clases por prioridad (tipo, año, duración)
3. Asigna cada clase a la mejor aula disponible que cumpla restricciones
4. Genera slots horarios respetando límites de sesiones consecutivas

**Ventaja**: Produce una solución factible en milisegundos.

### Fase 2: Refinamiento Genético (`generation_api_v2.py`)

El Algoritmo Genético **refina la solución greedy** para optimizar la distribución de aulas:

1. **Población Inicial**: Crea variantes de la solución greedy mediante mutaciones
2. **Evaluación (Fitness)**: Mide calidad basada en:
   - Equilibrio de uso de aulas (objetivo principal)
   - Penalización por conflictos de horario
   - Bonus por distribución uniforme
3. **Selección por Torneo**: Elige los mejores individuos para reproducción
4. **Cruce**: Combina asignaciones de aulas de dos padres
5. **Mutación**: Cambia aulas priorizando las subutilizadas
6. **Elitismo**: Preserva los mejores individuos entre generaciones

**Parámetros configurables**:
- `population_size`: Tamaño de la población (default: 50)
- `generations`: Número de generaciones (default: 100)

---

## Endpoints de la API

### Generación de Horarios

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/generate/datasets/` | Lista datasets disponibles |
| POST | `/api/generate/schedule/` | Genera horario con parámetros |
| GET | `/api/generate/last/` | Obtiene último horario generado |
| GET | `/api/generate/saved/` | Lista horarios guardados |
| GET | `/api/generate/saved/<id>/` | Obtiene horario por ID |

### Ejemplo de Generación

```json
POST /api/generate/schedule/
{
    "dataset": "escuela.xml",
    "name": "Horario Semestre 2025-I",
    "population_size": 50,
    "generations": 100
}
```

**Respuesta**:
```json
{
    "success": true,
    "schedule": {
        "id": 1,
        "name": "Horario Semestre 2025-I",
        "fitness_score": 1150.5,
        "conflict_count": 0,
        "classes_assigned": 89,
        "generation_time_ms": 2500,
        "algorithm": "greedy+genetic",
        "assignments": [...]
    }
}
```

---

## Instalación y Ejecución

### Requisitos

- Python 3.10+
- Node.js 18+
- npm o yarn

### Backend (Django)

```bash
# Crear entorno virtual
cd backend
python -m venv ../env
..\env\Scripts\activate  # Windows
source ../env/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python manage.py runserver 8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### Acceder al Sistema

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/

---

## Estructura del Proyecto

```
Sistema-Generacion-Horarios/
├── backend/
│   └── schedule_app/
│       ├── generation_api_v2.py   # API + Algoritmo Genético
│       ├── schedule_builder.py    # Algoritmo Greedy
│       ├── models.py              # Modelos Django
│       └── urls.py                # Rutas API
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Dashboard.tsx      # Página inicio
│       │   ├── Schedules.tsx      # Formulario generación
│       │   └── ScheduleViewer.tsx # Visualización calendario
│       └── services/
│           └── api.ts             # Cliente HTTP
├── escuela.xml                    # Dataset ejemplo (89 clases)
├── purdue_clean.xml               # Dataset grande (1545 clases)
└── schedules_history.json         # Historial de horarios
```

---

## Datasets Incluidos

| Dataset | Clases | Aulas | Instructores |
|---------|--------|-------|--------------|
| escuela.xml | 89 | 9 | 18 |
| purdue_clean.xml | 1545 | 63 | 454 |

---

## Uso del Sistema

1. **Acceder a http://localhost:3000**
2. **Click en "Generar Horario"**
3. **Seleccionar dataset** (escuela.xml o purdue_clean.xml)
4. **Configurar parámetros** (población, generaciones)
5. **Generar** - El sistema ejecuta Greedy + AG
6. **Visualizar** en el calendario interactivo
7. **Exportar a Excel** si es necesario

---
