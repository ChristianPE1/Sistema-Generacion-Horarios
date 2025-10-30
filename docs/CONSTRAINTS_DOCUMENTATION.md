# Documentación de Constraints del Sistema

Este documento describe todos los constraints (restricciones) evaluados por el sistema de generación de horarios.

## Tipos de Constraints

El sistema evalúa dos tipos de constraints:

### 1. **Hard Constraints** (Restricciones Duras)
**DEBEN cumplirse** para tener un horario válido. Cada violación penaliza fuertemente el fitness.

#### HC1: Conflictos de Instructor
- **Descripción**: Un instructor no puede estar en dos clases al mismo tiempo
- **Verificación**: Se verifica que no haya solapamiento de horarios (mismo día + tiempo que se cruza)
- **Penalización**: 100 puntos por cada violación
- **Implementación**: `_check_instructor_conflicts()`

#### HC2: Conflictos de Aula
- **Descripción**: Una aula no puede tener dos clases al mismo tiempo
- **Verificación**: Se verifica que no haya solapamiento de horarios en la misma aula
- **Penalización**: 100 puntos por cada violación
- **Implementación**: `_check_room_conflicts()`

#### HC3: Conflictos de Estudiantes
- **Descripción**: Un estudiante no puede estar en dos clases al mismo tiempo
- **Verificación**: Se verifica que clases del mismo offering no se solapen
- **Estado**: **DESHABILITADO** temporalmente (se resolverá manualmente)
- **Implementación**: `_check_student_conflicts()`

#### HC4: Violaciones de Capacidad
- **Descripción**: La capacidad del aula debe ser >= al límite de estudiantes de la clase
- **Verificación**: `room.capacity >= class.class_limit`
- **Penalización**: 100 puntos por cada violación
- **Implementación**: `_check_capacity_violations()`

---

### 2. **Soft Constraints** (Restricciones Blandas)
**SON PREFERENCIAS** - No cumplirlas reduce el fitness pero no invalida el horario.

#### SC1: Preferencias de Aula
- **Descripción**: Cada clase puede tener aulas preferidas o no preferidas
- **Verificación**: Se revisa el atributo `preference` en `ClassRoom`
- **Penalización**: `abs(preference)` si preference < 0
- **Implementación**: `_check_room_preferences()`
- **Estado**: **ACTUALMENTE EVALUADO** - se eliminará según tu solicitud

#### SC2: Preferencias de Horario
- **Descripción**: Cada clase puede tener horarios preferidos o no preferidos
- **Verificación**: Se revisa el atributo `preference` en `TimeSlot`
- **Penalización**: `abs(preference)` si preference < 0
- **Implementación**: `_check_time_preferences()`
- **Estado**: **ACTUALMENTE EVALUADO** - se eliminará según tu solicitud

#### SC3: Gaps de Instructor
- **Descripción**: Minimizar ventanas horarias (gaps) en el horario del instructor
- **Verificación**: Se calcula la diferencia entre clases consecutivas del mismo instructor
- **Penalización**: `(gap - 12) * 0.1` si gap > 12 slots (1 hora)
- **Implementación**: `_check_instructor_gaps()`

#### SC4: Restricciones de Grupo (GroupConstraints)
Restricciones entre múltiples clases relacionadas:

##### SC4.1: BTB (Back-To-Back)
- **Descripción**: Clases consecutivas deberían estar en aulas cercanas
- **Verificación**: Si dos clases son consecutivas (end1 == start2), se calcula distancia entre aulas
- **Penalización**:
  - PROHIBITED: 100 puntos si distancia > 200m, 20 si > 50m, 2 si < 50m
  - STRONGLY_DISCOURAGED: 50 / 10 / 1
  - DISCOURAGED: 20 / 5 / 0.5
- **Implementación**: `_evaluate_btb_constraint()`

##### SC4.2: DIFF_TIME
- **Descripción**: Clases relacionadas deberían estar en horarios diferentes (sin solapamiento)
- **Verificación**: Verifica si las clases se solapan
- **Penalización**:
  - REQUIRED: 50 puntos si se solapan
  - STRONGLY_PREFERRED: 20 puntos
  - PREFERRED: 10 puntos
- **Implementación**: `_evaluate_diff_time_constraint()`

##### SC4.3: SAME_TIME
- **Descripción**: Clases relacionadas deberían estar al mismo tiempo (solapándose)
- **Verificación**: Verifica si las clases NO se solapan
- **Penalización**:
  - REQUIRED: 50 puntos si NO se solapan
  - STRONGLY_PREFERRED: 20 puntos
  - PREFERRED: 10 puntos
- **Implementación**: `_evaluate_same_time_constraint()`

---

## Fórmula de Fitness

```
fitness = BASE_FITNESS - (hard_violations * 100 + soft_violations * 1)
```

Donde:
- `BASE_FITNESS = num_classes * 500` (mínimo 50,000, máximo 300,000)
- `hard_violations`: suma de todas las violaciones HC1-HC4
- `soft_violations`: suma ponderada de SC1-SC4

### Escala de Calidad

| Fitness | Calidad | Descripción |
|---------|---------|-------------|
| BASE - 1000 | ⭐⭐⭐⭐⭐ Perfecto | Sin violaciones críticas |
| BASE - 5000 | ⭐⭐⭐⭐ Excelente | Muy pocas violaciones |
| BASE - 10000 | ⭐⭐⭐ Bueno | Algunas violaciones menores |
| < BASE - 20000 | ⭐⭐ Regular | Necesita mejoras |
| < BASE - 50000 | ⭐ Malo | Muchas violaciones |

---

## Cambios Propuestos

Según tu solicitud, se eliminarán las siguientes evaluaciones:

### A Eliminar:
1. ❌ **SC1: Preferencias de Aula** (`_check_room_preferences()`)
2. ❌ **SC2: Preferencias de Horario** (`_check_time_preferences()`)

### A Mantener:
1. ✅ **HC1: Conflictos de Instructor** (crítico)
2. ✅ **HC2: Conflictos de Aula** (crítico)
3. ✅ **HC4: Violaciones de Capacidad** (crítico)
4. ✅ **SC3: Gaps de Instructor** (optimización)
5. ✅ **SC4: Restricciones de Grupo** (BTB, DIFF_TIME, SAME_TIME)

### Nueva Lógica:
- **Fase 1 (Algoritmo Genético)**: Asignar clases a aulas/horarios usando SOLO hard constraints + SC3 + SC4
- **Fase 2 (Post-procesamiento)**: Asignar instructores usando sus preferencias de horario
  - Permitir clases sin instructor si no hay disponibilidad
  - No afecta validez del horario

---

## Archivos Relacionados

- **`backend/schedule_app/constraints.py`**: Implementación de todos los constraints
- **`backend/schedule_app/genetic_algorithm.py`**: Usa ConstraintValidator para evaluar fitness
- **`backend/schedule_app/models.py`**: Modelos de datos (Class, Room, TimeSlot, ClassRoom, GroupConstraint)
