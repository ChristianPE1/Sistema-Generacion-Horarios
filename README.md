# 🎓 Sistema de Generación de Horarios

Sistema de gestión y generación automática de horarios universitarios desarrollado con Django REST Framework y React + TypeScript. Utiliza un **algoritmo genético** para optimizar la asignación de clases, aulas y horarios.

[![Estado](https://img.shields.io/badge/Estado-Completo-success)](./PROJECT_STATUS.md)
[![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)](./IMPLEMENTATION_SUMMARY.md)
[![Documentación](https://img.shields.io/badge/Docs-Completa-green)](./INDEX.md)

> 🚀 **¡Implementación completa del algoritmo genético!** Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para detalles.

---

## 📋 Índice Rápido

- [🎯 Características](#-características)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [📚 Documentación](#-documentación)
- [🚀 Instalación](#-instalación)
- [▶️ Ejecución](#️-ejecución)
- [🧬 Algoritmo Genético](#-algoritmo-genético)
- [🔌 API Endpoints](#-api-endpoints)

---

## 🎯 Características

### ✅ Implementado
- **Importación de datos** desde archivos XML (formato UniTime)
- **Dashboard** con estadísticas del sistema
- **Gestión CRUD** completa de salas, instructores, cursos, clases y estudiantes
- **API REST** completa con Django REST Framework
- **Interfaz moderna** con React + TypeScript + Vite
- **🧬 Algoritmo Genético** para generación automática de horarios
- **Optimización de restricciones** duras y blandas
- **Visualización de calendario** compatible con FullCalendar.js

### Pipeline de Datos

1. **Entrada**: CSV/XML o carga manual de datos institucionales
2. **Procesamiento**: Algoritmo genético optimiza asignaciones
3. **Generación**: Matriz de horarios factible y optimizada
4. **Visualización**: Interfaz interactiva con FullCalendar.js

## 🛠️ Stack Tecnológico

### Backend
- Framework: Django 4.2+
- API: Django REST Framework 3.14+
- Base de Datos: SQLite
- **Optimización**: Algoritmo Genético con NumPy

### Frontend
- Build Tool: Vite 5.0
- Framework: React 18.2
- Lenguaje: TypeScript 5.2
- Routing: React Router 6.20
- HTTP Client: Axios 1.6
- **Calendario**: FullCalendar.js (planeado)

## 📋 Requisitos Previos

- Python 3.8+
- Node.js 18+ y npm
- Git

## 🚀 Instalación

### Instalación Automática (Recomendada)

```bash
cd Sistemas-Generacion-Horarios
chmod +x setup.sh
./setup.sh
```

### Instalación Manual

#### Backend (Django)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
```

#### Frontend (React)

```bash
cd frontend
npm install
```

## ▶️ Ejecución

### Opción 1: Script Automático

```bash
chmod +x run.sh
./run.sh
```

### Opción 2: Manual

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🌐 Acceso al Sistema

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin Django: http://localhost:8000/admin/

## 📁 Estructura del Proyecto

```
Sistemas-Generacion-Horarios/
├── backend/
│   ├── timetable_system/        # Configuración Django
│   ├── schedule_app/
│   │   ├── models.py            # Modelos de datos
│   │   ├── views.py             # API endpoints
│   │   ├── serializers.py       # Serializadores DRF
│   │   ├── genetic_algorithm.py # 🧬 Algoritmo genético
│   │   ├── constraints.py       # Restricciones y validación
│   │   ├── schedule_generator.py # Servicio de generación
│   │   └── management/
│   │       └── commands/
│   │           └── generate_schedule.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tsconfig.json
├── pu-fal07-cs.xml             # Dataset de prueba (UniTime)
├── setup.sh
├── run.sh
├── README.md
└── GENETIC_ALGORITHM.md        # 📖 Documentación del algoritmo
```

## 📚 Uso del Sistema

### 1. Importar Datos XML

1. Accede a http://localhost:3000/import
2. Selecciona el archivo `pu-fal07-cs.xml`
3. Marca "Limpiar datos existentes" si deseas reemplazar todo
4. Haz clic en "Importar XML"

### 2. Generar Horario con Algoritmo Genético

#### Opción A: Usando la API REST

```bash
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Horario Optimizado 2025-I",
    "description": "Horario generado con algoritmo genético",
    "population_size": 150,
    "generations": 300,
    "mutation_rate": 0.15,
    "crossover_rate": 0.85,
    "elitism_size": 5,
    "tournament_size": 5
  }'
```

#### Opción B: Usando comando de Django

```bash
cd backend
python manage.py generate_schedule \
  --name "Horario Test" \
  --population 150 \
  --generations 300 \
  --mutation-rate 0.15 \
  --crossover-rate 0.85
```

### 3. Ver Resultados

```bash
# Obtener resumen del horario
curl http://localhost:8000/api/schedules/1/summary/

# Obtener vista de calendario (FullCalendar.js format)
curl http://localhost:8000/api/schedules/1/calendar_view/

# Activar horario como activo
curl -X POST http://localhost:8000/api/schedules/1/activate/
```

### 4. Gestionar Datos

Accede a las diferentes secciones desde el menú:
- **Salas**: Agregar, editar o eliminar aulas
- **Instructores**: Gestión de profesores
- **Cursos**: Visualizar cursos importados
- **Clases**: Ver clases y sus asignaciones
- **Estudiantes**: Administrar estudiantes
- **Horarios**: Ver y generar horarios

## 🧬 Algoritmo Genético

El sistema implementa un algoritmo genético completo para optimizar la asignación de horarios. Ver [GENETIC_ALGORITHM.md](./GENETIC_ALGORITHM.md) para documentación detallada.

### Restricciones Duras (DEBEN cumplirse)
- ❌ No solapamiento de clases del mismo instructor
- ❌ No solapamiento de clases en la misma aula
- ❌ No solapamiento de estudiantes del mismo curso
- ❌ Capacidad de aula suficiente

### Restricciones Blandas (Preferencias)
- ⭐ Preferencias de aula por clase
- ⭐ Preferencias de horario
- ⭐ Minimización de gaps en horarios de instructores

### Parámetros Recomendados

| Parámetro | Por Defecto | Descripción |
|-----------|-------------|-------------|
| `population_size` | 100 | Tamaño de la población |
| `generations` | 200 | Número de iteraciones |
| `mutation_rate` | 0.1 | Probabilidad de mutación (0-1) |
| `crossover_rate` | 0.8 | Probabilidad de cruce (0-1) |
| `elitism_size` | 5 | Individuos élite preservados |
| `tournament_size` | 5 | Tamaño del torneo de selección |

## 🔌 API Endpoints

### Recursos Principales

```
GET    /api/rooms/              # Listar salas
POST   /api/rooms/              # Crear sala
GET    /api/rooms/{id}/         # Detalle de sala
PUT    /api/rooms/{id}/         # Actualizar sala
DELETE /api/rooms/{id}/         # Eliminar sala

GET    /api/instructors/        # Listar instructores
POST   /api/instructors/        # Crear instructor
GET    /api/courses/            # Listar cursos
GET    /api/classes/            # Listar clases
GET    /api/students/           # Listar estudiantes
```

### Endpoints de Horarios (Algoritmo Genético)

```
POST   /api/schedules/generate/        # Generar horario con AG
GET    /api/schedules/                 # Listar horarios
GET    /api/schedules/{id}/            # Detalle de horario
POST   /api/schedules/{id}/activate/   # Activar horario
GET    /api/schedules/{id}/summary/    # Resumen detallado
GET    /api/schedules/{id}/calendar_view/  # Vista FullCalendar
```

### Endpoints Especiales

```
POST   /api/import-xml/         # Importar archivo XML
GET    /api/dashboard-stats/    # Estadísticas del dashboard
```

## 📊 Dataset de Prueba

El proyecto incluye el dataset **UniTime pu-fal07-cs** (XML) con:
- Cursos de Computer Science
- Múltiples instructores y aulas
- Restricciones de horarios
- Preferencias de asignación

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## 👥 Autores

- Equipo de desarrollo TI3

## 🔗 Enlaces Útiles

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [FullCalendar](https://fullcalendar.io/)
- [UniTime Project](https://www.unitime.org/)

---

**Nota**: Para información detallada sobre el algoritmo genético, consulta [GENETIC_ALGORITHM.md](./GENETIC_ALGORITHM.md)