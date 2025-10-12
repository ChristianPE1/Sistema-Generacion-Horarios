# Algoritmo Genético - Sistema de Generación de Horarios

## 📋 Descripción

Se ha implementado un **algoritmo genético** completo para la generación automática de horarios académicos. El sistema optimiza la asignación de clases, aulas y horarios, respetando restricciones duras y optimizando preferencias blandas.

## 🏗️ Arquitectura

### Módulos Implementados

#### 1. **genetic_algorithm.py** - Motor del Algoritmo Genético
- **Clase `Individual`**: Representa una solución candidata (cromosoma)
  - Genes: `{class_id: (room_id, timeslot_id)}`
  - Inicialización aleatoria
  - Cálculo de fitness

- **Clase `GeneticAlgorithm`**: Implementa el algoritmo completo
  - **Inicialización de población**: Crea individuos aleatorios
  - **Selección por torneo**: Elige padres para reproducción
  - **Operador de cruce**: Combina dos padres (cruce de un punto)
  - **Operador de mutación**: Modifica genes aleatoriamente
  - **Elitismo**: Preserva mejores soluciones entre generaciones

#### 2. **constraints.py** - Sistema de Restricciones
- **Clase `ConstraintValidator`**: Evalúa y penaliza violaciones

**Restricciones Duras** (peso: 1000):
- ❌ No solapamiento de clases del mismo instructor
- ❌ No solapamiento de clases en la misma aula
- ❌ No solapamiento de estudiantes del mismo curso
- ❌ Capacidad de aula suficiente para estudiantes

**Restricciones Blandas** (peso: 1):
- ⭐ Preferencias de aula por clase
- ⭐ Preferencias de horario por clase
- ⭐ Minimización de gaps en horarios de instructores
- ⭐ Distribución equilibrada de clases

**Función de Fitness**:
```python
fitness = 100000 - (violaciones_duras * 1000 + violaciones_blandas * 1)
```

#### 3. **schedule_generator.py** - Servicio de Generación
- **Clase `ScheduleGenerator`**: Orquesta el proceso completo
  - Carga datos de la BD
  - Inicializa el algoritmo genético
  - Ejecuta la evolución
  - Guarda la mejor solución en la BD
  - Genera reportes y estadísticas

#### 4. **views.py** - API REST
Nuevos endpoints agregados:

**POST `/api/schedules/generate/`**
Genera un nuevo horario usando el algoritmo genético.

```json
{
  "name": "Horario Semestre 2025-I",
  "description": "Horario optimizado para ciencias",
  "population_size": 100,
  "generations": 200,
  "mutation_rate": 0.1,
  "crossover_rate": 0.8,
  "elitism_size": 5,
  "tournament_size": 5
}
```

Respuesta:
```json
{
  "schedule": {
    "id": 1,
    "name": "Horario Semestre 2025-I",
    "fitness_score": 95847.5,
    "created_at": "2025-10-12T10:30:00Z"
  },
  "summary": {
    "total_assignments": 145,
    "unassigned_classes": 5,
    "instructor_count": 32,
    "room_count": 18
  },
  "message": "Horario generado exitosamente"
}
```

**GET `/api/schedules/{id}/summary/`**
Obtiene un resumen detallado del horario.

**GET `/api/schedules/{id}/calendar_view/`**
Retorna eventos en formato FullCalendar.js:

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
      "instructors": ["Dr. Smith"],
      "classLimit": 35
    }
  }
]
```

## 🚀 Uso

### 1. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Importar datos XML

```bash
# Desde la interfaz web o usando curl
curl -X POST http://localhost:8000/api/import-xml/ \
  -F "file=@pu-fal07-cs.xml" \
  -F "clear_existing=true"
```

### 4. Generar horario

**Opción A: Usando la API**
```bash
curl -X POST http://localhost:8000/api/schedules/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Horario Optimizado",
    "population_size": 150,
    "generations": 300,
    "mutation_rate": 0.15,
    "crossover_rate": 0.85
  }'
```

**Opción B: Usando comando de Django**
```bash
python manage.py generate_schedule \
  --name "Horario Test" \
  --population 150 \
  --generations 300 \
  --mutation-rate 0.15 \
  --crossover-rate 0.85
```

### 5. Ver resultados

```bash
# Obtener resumen
curl http://localhost:8000/api/schedules/1/summary/

# Obtener vista de calendario
curl http://localhost:8000/api/schedules/1/calendar_view/

# Activar horario
curl -X POST http://localhost:8000/api/schedules/1/activate/
```

## ⚙️ Parámetros del Algoritmo

| Parámetro | Descripción | Valor por defecto | Rango recomendado |
|-----------|-------------|-------------------|-------------------|
| `population_size` | Tamaño de la población | 100 | 50-200 |
| `generations` | Número de iteraciones | 200 | 100-500 |
| `mutation_rate` | Probabilidad de mutación | 0.1 | 0.05-0.20 |
| `crossover_rate` | Probabilidad de cruce | 0.8 | 0.70-0.95 |
| `elitism_size` | Individuos élite preservados | 5 | 2-10 |
| `tournament_size` | Tamaño del torneo | 5 | 3-7 |

## 📊 Proceso de Optimización

1. **Inicialización**: Se crea una población de soluciones aleatorias
2. **Evaluación**: Cada solución es evaluada usando la función de fitness
3. **Selección**: Se eligen padres mediante torneos
4. **Cruce**: Los padres se combinan para crear hijos
5. **Mutación**: Se modifican genes aleatoriamente
6. **Elitismo**: Se preservan las mejores soluciones
7. **Iteración**: Se repite por N generaciones
8. **Resultado**: Se retorna la mejor solución encontrada

## 📈 Métricas de Rendimiento

El sistema registra:
- **Fitness por generación**: Evolución de la calidad
- **Mejora total**: Diferencia entre primera y última generación
- **Violaciones de restricciones**: Desglose por tipo
- **Estadísticas de asignación**: Clases, aulas, instructores

## 🔍 Reporte de Conflictos

Cada horario incluye un reporte detallado:

```python
{
  'hard_constraints': {
    'instructor_conflicts': 0,      # Objetivo: 0
    'room_conflicts': 0,            # Objetivo: 0
    'student_conflicts': 0,         # Objetivo: 0
    'capacity_violations': 0        # Objetivo: 0
  },
  'soft_constraints': {
    'room_preference_penalty': 12.5,
    'time_preference_penalty': 8.3,
    'instructor_gaps_penalty': 5.2
  },
  'total_fitness': 97845.0
}
```

## 🎯 Objetivos del Algoritmo

1. **Factibilidad**: Cumplir 100% de restricciones duras
2. **Optimización**: Minimizar penalización de restricciones blandas
3. **Eficiencia**: Converger en tiempo razonable (<5 min para 200 clases)
4. **Robustez**: Manejar diferentes tamaños de problema

## 🔧 Personalización

### Modificar pesos de restricciones

En `constraints.py`:
```python
validator = ConstraintValidator(
    hard_constraint_weight=2000.0,  # Aumentar para priorizar factibilidad
    soft_constraint_weight=0.5      # Reducir para flexibilizar preferencias
)
```

### Agregar nuevas restricciones

1. Implementar método en `ConstraintValidator`
2. Llamar desde `_evaluate_hard_constraints()` o `_evaluate_soft_constraints()`
3. Actualizar reporte de conflictos

### Modificar operadores genéticos

En `genetic_algorithm.py`:
- `crossover()`: Cambiar a cruce de dos puntos, uniforme, etc.
- `mutate()`: Ajustar probabilidades o tipos de mutación
- `tournament_selection()`: Implementar selección por ruleta, rango, etc.

## 📝 Notas Importantes

- **Datos requeridos**: El sistema necesita clases, aulas y preferencias cargadas
- **Tiempo de ejecución**: Depende de parámetros y tamaño del problema
- **Slots de tiempo**: Si no hay slots definidos, se generan automáticamente
- **Convergencia**: Si fitness no mejora, ajustar parámetros (aumentar mutación/población)

## 🐛 Solución de Problemas

**Problema**: Muchos conflictos de restricciones duras
- **Solución**: Aumentar `population_size` y `generations`

**Problema**: Solución no mejora
- **Solución**: Aumentar `mutation_rate` (0.15-0.20)

**Problema**: Clases sin asignar
- **Solución**: Verificar disponibilidad de aulas y slots de tiempo

**Problema**: Ejecución muy lenta
- **Solución**: Reducir `population_size` o `generations`

## 🔗 Integración con Frontend

El frontend puede consumir:
1. `/api/schedules/generate/` - Generar nuevo horario
2. `/api/schedules/` - Listar horarios
3. `/api/schedules/{id}/calendar_view/` - Vista FullCalendar
4. `/api/schedules/{id}/summary/` - Resumen y estadísticas

## 📚 Referencias

- Algoritmos Genéticos: Holland, 1992
- Timetabling Problem: Burke & Petrovic, 2002
- UniTime Dataset: Purdue University
