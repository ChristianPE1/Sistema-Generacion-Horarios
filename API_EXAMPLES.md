# API Examples - Sistema de Generación de Horarios

Este archivo contiene ejemplos prácticos de uso de la API REST del sistema.

## 📋 Tabla de Contenidos
1. [Importar Datos](#importar-datos)
2. [Generar Horarios](#generar-horarios)
3. [Consultar Horarios](#consultar-horarios)
4. [Gestión de Recursos](#gestión-de-recursos)

---

## 1. Importar Datos

### Importar archivo XML
```bash
curl -X POST http://localhost:8000/api/import-xml/ \
  -F "file=@pu-fal07-cs.xml" \
  -F "clear_existing=true"
```

**Respuesta exitosa**:
```json
{
  "message": "Datos importados exitosamente",
  "stats": {
    "rooms": 25,
    "instructors": 42,
    "courses": 18,
    "classes": 156,
    "time_slots": 780,
    "students": 320,
    "enrollments": 1560
  }
}
```

---

## 2. Generar Horarios

### 2.1 Generación Básica (Parámetros por Defecto)
```bash
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Horario Semestre 2025-I"
  }'
```

### 2.2 Generación con Parámetros Personalizados
```bash
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Horario Optimizado CS",
    "description": "Horario para Computer Science con optimización avanzada",
    "population_size": 150,
    "generations": 300,
    "mutation_rate": 0.15,
    "crossover_rate": 0.85,
    "elitism_size": 8,
    "tournament_size": 6
  }'
```

### 2.3 Generación Rápida (Testing)
```bash
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Rápido",
    "population_size": 50,
    "generations": 100,
    "mutation_rate": 0.1
  }'
```

**Respuesta**:
```json
{
  "schedule": {
    "id": 1,
    "name": "Horario Optimizado CS",
    "description": "Horario para Computer Science...",
    "fitness_score": 97845.50,
    "is_active": false,
    "created_at": "2025-10-12T10:30:00Z",
    "updated_at": "2025-10-12T10:35:00Z"
  },
  "summary": {
    "total_assignments": 145,
    "unassigned_classes": 11,
    "instructor_count": 38,
    "room_count": 22
  },
  "message": "Horario generado exitosamente"
}
```

---

## 3. Consultar Horarios

### 3.1 Listar Todos los Horarios
```bash
curl http://localhost:8000/api/schedules/
```

**Respuesta**:
```json
[
  {
    "id": 1,
    "name": "Horario Optimizado CS",
    "fitness_score": 97845.50,
    "is_active": false,
    "created_at": "2025-10-12T10:30:00Z"
  },
  {
    "id": 2,
    "name": "Horario Test",
    "fitness_score": 95320.25,
    "is_active": true,
    "created_at": "2025-10-12T09:15:00Z"
  }
]
```

### 3.2 Detalle de un Horario
```bash
curl http://localhost:8000/api/schedules/1/
```

### 3.3 Resumen Detallado
```bash
curl http://localhost:8000/api/schedules/1/summary/
```

**Respuesta**:
```json
{
  "schedule_id": 1,
  "schedule_name": "Horario Optimizado CS",
  "fitness_score": 97845.50,
  "total_assignments": 145,
  "unassigned_classes": 11,
  "instructor_schedules": [
    {
      "instructor_id": 101,
      "instructor_name": "Dr. Smith",
      "class_count": 4
    },
    {
      "instructor_id": 102,
      "instructor_name": "Prof. Johnson",
      "class_count": 3
    }
  ],
  "room_schedules": [
    {
      "room_id": 201,
      "room_capacity": 40,
      "class_count": 8
    },
    {
      "room_id": 202,
      "room_capacity": 30,
      "class_count": 6
    }
  ]
}
```

### 3.4 Vista de Calendario (FullCalendar.js)
```bash
curl http://localhost:8000/api/schedules/1/calendar_view/
```

**Respuesta**:
```json
[
  {
    "id": "123_0",
    "title": "Algoritmos Avanzados",
    "daysOfWeek": [1],
    "startTime": "08:00",
    "endTime": "09:00",
    "extendedProps": {
      "classId": 456,
      "room": "Room 101",
      "roomCapacity": 40,
      "instructors": ["Dr. Smith", "Prof. Johnson"],
      "classLimit": 35
    }
  },
  {
    "id": "124_2",
    "title": "Bases de Datos",
    "daysOfWeek": [3],
    "startTime": "10:00",
    "endTime": "11:30",
    "extendedProps": {
      "classId": 457,
      "room": "Room 102",
      "roomCapacity": 30,
      "instructors": ["Dr. Williams"],
      "classLimit": 28
    }
  }
]
```

### 3.5 Activar un Horario
```bash
curl -X POST http://localhost:8000/api/schedules/1/activate/
```

**Respuesta**:
```json
{
  "status": "Horario activado"
}
```

---

## 4. Gestión de Recursos

### 4.1 Aulas (Rooms)

#### Listar Aulas
```bash
curl http://localhost:8000/api/rooms/
```

#### Crear Aula
```bash
curl -X POST http://localhost:8000/api/rooms/ \
  -H "Content-Type: application/json" \
  -d '{
    "xml_id": 301,
    "capacity": 50,
    "location": "Edificio A - Piso 3",
    "is_constraint": false
  }'
```

#### Estadísticas de Aulas
```bash
curl http://localhost:8000/api/rooms/statistics/
```

**Respuesta**:
```json
{
  "total_rooms": 25,
  "average_capacity": 35.2,
  "max_capacity": 80
}
```

### 4.2 Instructores

#### Listar Instructores
```bash
curl http://localhost:8000/api/instructors/
```

#### Crear Instructor
```bash
curl -X POST http://localhost:8000/api/instructors/ \
  -H "Content-Type: application/json" \
  -d '{
    "xml_id": 401,
    "name": "Dr. Jane Doe",
    "email": "jane.doe@university.edu"
  }'
```

#### Clases de un Instructor
```bash
curl http://localhost:8000/api/instructors/1/classes/
```

#### Estadísticas de Instructores
```bash
curl http://localhost:8000/api/instructors/statistics/
```

### 4.3 Cursos

#### Listar Cursos
```bash
curl http://localhost:8000/api/courses/
```

#### Clases de un Curso
```bash
curl http://localhost:8000/api/courses/1/classes/
```

### 4.4 Clases

#### Listar Clases
```bash
curl http://localhost:8000/api/classes/
```

#### Detalle de Clase
```bash
curl http://localhost:8000/api/classes/1/
```

#### Estudiantes de una Clase
```bash
curl http://localhost:8000/api/classes/1/students/
```

#### Estadísticas de Clases
```bash
curl http://localhost:8000/api/classes/statistics/
```

### 4.5 Estudiantes

#### Listar Estudiantes
```bash
curl http://localhost:8000/api/students/
```

#### Clases de un Estudiante
```bash
curl http://localhost:8000/api/students/1/classes/
```

---

## 5. Ejemplos con Python (requests)

### Generar Horario con Python
```python
import requests
import json

url = "http://localhost:8000/api/schedules/generate/"
payload = {
    "name": "Horario Automatizado",
    "description": "Generado vía script Python",
    "population_size": 120,
    "generations": 250,
    "mutation_rate": 0.12,
    "crossover_rate": 0.82
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Horario ID: {result['schedule']['id']}")
print(f"Fitness: {result['schedule']['fitness_score']}")
print(f"Asignaciones: {result['summary']['total_assignments']}")
```

### Obtener Vista de Calendario
```python
import requests

schedule_id = 1
url = f"http://localhost:8000/api/schedules/{schedule_id}/calendar_view/"

response = requests.get(url)
events = response.json()

print(f"Total de eventos: {len(events)}")
for event in events[:5]:  # Primeros 5
    print(f"{event['title']}: {event['startTime']} - {event['endTime']}")
```

### Monitorear Generación (Polling)
```python
import requests
import time

def generate_and_monitor():
    # Iniciar generación
    url = "http://localhost:8000/api/schedules/generate/"
    payload = {"name": "Test Monitor", "generations": 200}
    
    response = requests.post(url, json=payload)
    schedule_id = response.json()['schedule']['id']
    
    # Obtener resumen
    summary_url = f"http://localhost:8000/api/schedules/{schedule_id}/summary/"
    summary = requests.get(summary_url).json()
    
    print(f"Generación completada:")
    print(f"  Fitness: {summary['fitness_score']:.2f}")
    print(f"  Asignaciones: {summary['total_assignments']}")
    print(f"  Sin asignar: {summary['unassigned_classes']}")
    
    return schedule_id

schedule_id = generate_and_monitor()
```

---

## 6. Ejemplos con JavaScript (Axios)

### Generar Horario
```javascript
const axios = require('axios');

async function generateSchedule() {
  try {
    const response = await axios.post('http://localhost:8000/api/schedules/generate/', {
      name: 'Horario JS',
      population_size: 100,
      generations: 200,
      mutation_rate: 0.1,
      crossover_rate: 0.8
    });
    
    console.log('Horario generado:', response.data.schedule);
    console.log('Resumen:', response.data.summary);
    
    return response.data.schedule.id;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

generateSchedule();
```

### Obtener Eventos de Calendario
```javascript
async function getCalendarEvents(scheduleId) {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/schedules/${scheduleId}/calendar_view/`
    );
    
    const events = response.data;
    console.log(`Total eventos: ${events.length}`);
    
    // Formatear para FullCalendar
    const calendarEvents = events.map(event => ({
      ...event,
      backgroundColor: '#3788d8',
      borderColor: '#3788d8'
    }));
    
    return calendarEvents;
  } catch (error) {
    console.error('Error:', error.message);
  }
}
```

---

## 7. Ejemplos Avanzados

### Generar Múltiples Horarios y Elegir el Mejor
```bash
#!/bin/bash

BEST_FITNESS=0
BEST_ID=0

for i in {1..5}; do
  echo "Generando horario $i..."
  
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/schedules/generate/ \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Test $i\", \"population_size\": 100, \"generations\": 200}")
  
  ID=$(echo $RESPONSE | jq -r '.schedule.id')
  FITNESS=$(echo $RESPONSE | jq -r '.schedule.fitness_score')
  
  echo "ID: $ID, Fitness: $FITNESS"
  
  if (( $(echo "$FITNESS > $BEST_FITNESS" | bc -l) )); then
    BEST_FITNESS=$FITNESS
    BEST_ID=$ID
  fi
done

echo ""
echo "Mejor horario: ID=$BEST_ID, Fitness=$BEST_FITNESS"

# Activar el mejor
curl -s -X POST http://localhost:8000/api/schedules/$BEST_ID/activate/
echo "Horario $BEST_ID activado"
```

### Exportar Horario a JSON
```bash
curl http://localhost:8000/api/schedules/1/calendar_view/ | jq '.' > horario.json
echo "Horario exportado a horario.json"
```

### Comparar Dos Horarios
```python
import requests

def compare_schedules(id1, id2):
    s1 = requests.get(f"http://localhost:8000/api/schedules/{id1}/").json()
    s2 = requests.get(f"http://localhost:8000/api/schedules/{id2}/").json()
    
    print(f"Comparación:")
    print(f"  {s1['name']}: Fitness={s1['fitness_score']:.2f}")
    print(f"  {s2['name']}: Fitness={s2['fitness_score']:.2f}")
    
    if s1['fitness_score'] > s2['fitness_score']:
        print(f"  → {s1['name']} es mejor")
    else:
        print(f"  → {s2['name']} es mejor")

compare_schedules(1, 2)
```

---

## 8. Troubleshooting API

### Verificar Estado del Servidor
```bash
curl http://localhost:8000/api/
```

### Ver Errores Detallados
```bash
curl -v -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
```

### Verificar Datos Importados
```bash
echo "Aulas:" && curl -s http://localhost:8000/api/rooms/ | jq 'length'
echo "Instructores:" && curl -s http://localhost:8000/api/instructors/ | jq 'length'
echo "Cursos:" && curl -s http://localhost:8000/api/courses/ | jq 'length'
echo "Clases:" && curl -s http://localhost:8000/api/classes/ | jq 'length'
```

---

## 📚 Referencias

- **API Base URL**: `http://localhost:8000/api/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **Documentación Completa**: Ver `GENETIC_ALGORITHM.md`
- **Guía de Configuración**: Ver `GA_CONFIG_GUIDE.md`
