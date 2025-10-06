# Sistema de Generación de Horarios

Sistema de gestión y generación automática de horarios universitarios desarrollado con Django REST Framework y React + TypeScript.

## Características

### Fase 1 (Implementada)
- Importación de datos desde archivos XML (formato UniTime)
- Dashboard con estadísticas del sistema
- Gestión CRUD completa de salas, instructores, cursos, clases y estudiantes
- API REST completa con Django REST Framework
- Interfaz moderna con React + TypeScript + Vite

### Fase 2 (Próximamente)
- Generación automática de horarios con algoritmo genético
- Visualización de horarios en calendario interactivo
- Configuración de restricciones personalizadas

## Stack Tecnológico

### Backend
- Framework: Django 4.2+
- API: Django REST Framework 3.14+
- Base de Datos: SQLite

### Frontend
- Build Tool: Vite 5.0
- Framework: React 18.2
- Lenguaje: TypeScript 5.2
- Routing: React Router 6.20
- HTTP Client: Axios 1.6

## Requisitos Previos

- Python 3.8+
- Node.js 18+ y npm
- Git

## Instalación

### Instalación Automática (Recomendada)

```bash
cd proyecto-ti3
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

## Ejecución

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

## Acceso al Sistema

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin Django: http://localhost:8000/admin/

## Estructura del Proyecto

```
proyecto-ti3/
├── backend/
│   ├── timetable_system/
│   ├── schedule_app/
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
├── pu-fal07-cs.xml
├── setup.sh
├── run.sh
└── README.md
```

## Uso del Sistema

### 1. Importar Datos XML

1. Accede a http://localhost:3000/import
2. Selecciona el archivo `pu-fal07-cs.xml`
3. Marca "Limpiar datos existentes" si deseas reemplazar todo
4. Haz clic en "Importar XML"

### 2. Gestionar Datos

Accede a las diferentes secciones desde el menú:
- Salas: Agregar, editar o eliminar aulas
- Instructores: Gestión de profesores
- Cursos: Visualizar cursos importados
- Clases: Ver clases y sus asignaciones
- Estudiantes: Administrar estudiantes
- Horarios: Ver horarios generados

## API Endpoints

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

### Endpoints Especiales

```
POST   /api/import-xml/         # Importar archivo XML
GET    /api/dashboard-stats/    # Estadísticas del dashboard
```

## Solución de Problemas

### Error: "Cannot find module 'react'"
Ejecuta `npm install` en el directorio frontend.

### Error: "No module named 'django'"
Asegúrate de activar el entorno virtual: `source venv/bin/activate`

### Puerto ocupado
Cambia los puertos en la configuración de Vite o Django.

### Base de datos bloqueada
```bash
cd backend
rm db.sqlite3
python manage.py migrate
```

## Licencia

Proyecto académico para el curso TI3.
