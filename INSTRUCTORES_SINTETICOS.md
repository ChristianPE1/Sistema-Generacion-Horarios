# Instructores Sintéticos - Documentación

**Fecha**: 13 de octubre de 2025  
**Funcionalidad**: Generación automática de instructores sintéticos para facilitar la planificación

---

## 🎯 ¿Qué son los Instructores Sintéticos?

Los **instructores sintéticos** son profesores ficticios creados automáticamente por el sistema cuando una clase **no tiene instructor asignado**. 

### Propósito:

1. **Facilitar la generación de horarios** → No bloquear el proceso por falta de asignación
2. **Identificar necesidades** → Ver claramente qué cursos necesitan profesores
3. **Planificación de recursos** → Calcular cuántos profesores se necesitan contratar
4. **Distribución de carga** → Visualizar cómo se distribuirían las clases

---

## 🔍 ¿Cómo Funcionan?

### Detección Automática

Cuando ejecutas `generate_schedule`, el sistema:

1. **Escanea todas las clases** del sistema
2. **Identifica** cuáles NO tienen instructor asignado
3. **Agrupa** las clases sin instructor por curso
4. **Crea un instructor sintético por curso**
5. **Asigna** el instructor sintético a todas las clases de ese curso

### Nomenclatura

Los instructores sintéticos son fácilmente identificables:

- **Nombre**: `[SINTÉTICO] Profesor para [Nombre del Curso]`
- **Email**: `synthetic.instructor.N@sistema.edu`
- **XML ID**: ≥ 900,000 (nunca conflictúa con IDs reales)

### Ejemplo

```
Curso: Algoritmos y Estructuras de Datos
Clases sin instructor: 12 clases (secciones A, B, C, etc.)

Sistema crea:
  Instructor: [SINTÉTICO] Profesor para Algoritmos y Estructuras de Datos
  Email: synthetic.instructor.0@sistema.edu
  XML ID: 900000
  
Resultado: Las 12 clases ahora tienen este instructor asignado
```

---

## 📊 Beneficios para la Planificación

### 1. Identificar Carencias

**Sin instructores sintéticos:**
```
❌ Horario incompleto
❌ No se sabe cuántos profesores faltan
❌ No se puede planificar
```

**Con instructores sintéticos:**
```
✓ Horario completo generado
✓ 503 instructores sintéticos = 503 profesores necesarios
✓ Se puede ver distribución de carga por curso
```

### 2. Calcular Necesidades

El reporte muestra:
- **Cuántos** profesores se necesitan (total de sintéticos)
- **Para qué cursos** se necesitan
- **Cuántas clases** debe cubrir cada uno

### 3. Visualizar Distribución

Puedes ver:
- Cómo se distribuyen los horarios si contratas X profesores
- Qué días/horarios quedan para cada curso
- Posibles solapamientos si un profesor cubre varios cursos

---

## 🚀 Uso en la Práctica

### Paso 1: Generar Horario

```bash
cd backend
./venv/bin/python3 manage.py generate_schedule --name "Planificación Semestre 2025-2" --population 100 --generations 150
```

**Output esperado:**
```
⚠️ Se encontraron 596 clases sin instructor asignado
Creando instructores sintéticos...
✓ 503 instructores sintéticos creados
✓ 596 clases ahora tienen instructor asignado

Generación completada!
⚠️ ATENCIÓN: Instructores Sintéticos
  - Total: 503 instructores sintéticos
  - Estos representan cursos que AÚN necesitan profesores reales
```

### Paso 2: Ver Reporte Detallado

```bash
./venv/bin/python3 manage.py show_synthetic_instructors
```

**Output esperado:**
```
============================================================
  REPORTE DE INSTRUCTORES SINTÉTICOS
============================================================

⚠️  Total de instructores sintéticos: 503

Estos instructores representan cursos que AÚN necesitan
profesores reales asignados. Use esta información para:
  1. Identificar qué cursos necesitan profesores
  2. Calcular cuántos profesores contratar
  3. Planificar la asignación de carga docente

------------------------------------------------------------

1. [SINTÉTICO] Profesor para Algoritmos I
   Curso: Algoritmos I
   Clases a cargo: 3
   IDs de clases: 101, 102, 103

2. [SINTÉTICO] Profesor para Cálculo II
   Curso: Cálculo II
   Clases a cargo: 5
   IDs de clases: 201, 202, 203, 204, 205

[... más instructores ...]

------------------------------------------------------------
⚠️  ACCIÓN REQUERIDA:
   Asigne 503 profesores reales a estos cursos
```

### Paso 3: Tomar Decisiones

Con esta información puedes:

1. **Planificar contrataciones**: "Necesitamos 503 profesores"
2. **Priorizar cursos**: Ver qué cursos tienen más clases
3. **Distribuir carga**: Asignar profesores existentes a múltiples cursos
4. **Ajustar oferta**: Decidir qué clases eliminar si no hay suficientes profesores

---

## 🔄 Flujo Completo de Trabajo

### Escenario: Universidad al inicio de semestre

```
1. Importar XML con datos de cursos
   → 630 clases creadas
   → Solo 34 tienen instructor asignado (596 sin asignar)

2. Generar horario con instructores sintéticos
   → Sistema crea 503 instructores sintéticos
   → Horario completo generado

3. Revisar reporte
   → Ver qué cursos necesitan profesores
   → Calcular presupuesto: 503 profesores × salario

4. Asignar profesores reales
   a) Contratar nuevos profesores
   b) Asignar profesores existentes
   c) Distribuir carga entre varios

5. Actualizar asignaciones en el sistema
   → Reemplazar instructores sintéticos por reales
   → Regenerar horario con datos reales

6. Limpiar sintéticos
   → Eliminar instructores sintéticos
   → Sistema queda con solo profesores reales
```

---

## 🛠️ Comandos Útiles

### Ver todos los instructores sintéticos

```bash
./venv/bin/python3 manage.py shell
```

```python
from schedule_app.models import Instructor

# Listar todos los sintéticos
synthetic = Instructor.objects.filter(xml_id__gte=900000)
print(f"Total: {synthetic.count()}")

for inst in synthetic:
    print(f"{inst.name} - {inst.email}")
```

### Eliminar instructores sintéticos después de asignar reales

```bash
./venv/bin/python3 manage.py shell
```

```python
from schedule_app.models import Instructor

# Eliminar todos los sintéticos
Instructor.objects.filter(xml_id__gte=900000).delete()
print("Instructores sintéticos eliminados")
```

### Reemplazar un sintético por uno real

```python
from schedule_app.models import Instructor, ClassInstructor

# Encontrar sintético
synthetic = Instructor.objects.get(xml_id=900000)

# Crear o buscar instructor real
real_instructor = Instructor.objects.create(
    xml_id=12345,
    name="Dr. Juan Pérez",
    email="juan.perez@universidad.edu"
)

# Reemplazar en todas las clases
ClassInstructor.objects.filter(instructor=synthetic).update(instructor=real_instructor)

# Eliminar sintético
synthetic.delete()
```

---

## 📋 Características Importantes

### ✅ Ventajas

1. **No bloquea la generación**: Siempre genera horario completo
2. **Fácil identificación**: Nombre con [SINTÉTICO] y XML ID ≥ 900000
3. **Agrupación inteligente**: Un sintético por curso, no por clase
4. **Sin conflictos**: No genera restricciones adicionales
5. **Reversible**: Fácil de eliminar después

### ⚠️ Consideraciones

1. **No son profesores reales**: Solo marcadores de posición
2. **Deben ser reemplazados**: Antes de usar el horario en producción
3. **No tienen restricciones**: Pueden tener horarios imposibles para humanos
4. **Inflan el conteo**: Aparecen en estadísticas de instructores

---

## 🎓 Casos de Uso

### Universidad Pequeña
```
Escenario: 50 clases, 5 profesores de planta
Resultado: 45 clases → 10 sintéticos
Decisión: Contratar 10 profesores part-time
```

### Universidad Grande
```
Escenario: 630 clases, 29 profesores asignados
Resultado: 596 clases → 503 sintéticos
Decisión: 
  - Contratar 200 profesores nuevos
  - Reasignar 150 existentes
  - Reducir oferta en 153 clases
```

### Planificación de Semestre
```
Escenario: Nuevo semestre, cursos sin asignar
Uso:
  1. Generar horario con sintéticos
  2. Ver distribución temporal
  3. Asignar profesores basado en disponibilidad
  4. Regenerar horario final
```

---

## 📈 Métricas e Interpretación

### Reporte del Sistema

```
⚠️ 503 instructores sintéticos creados
```

**Interpretación:**
- Necesitas asignar 503 profesores (mínimo)
- Puedes distribuir la carga (ej: 1 profesor = 2-3 clases)
- Número real necesario: 503 ÷ carga_promedio

**Ejemplo:**
- Si cada profesor da 3 clases: 503 ÷ 3 ≈ 168 profesores reales
- Si cada profesor da 2 clases: 503 ÷ 2 ≈ 252 profesores reales

---

## 🔮 Mejoras Futuras Posibles

1. **Asignación inteligente**: Sugerir qué profesor podría cubrir qué clases
2. **Carga balanceada**: Distribuir automáticamente entre profesores existentes
3. **Restricciones de disponibilidad**: Considerar horarios de profesores
4. **Optimización de costos**: Minimizar número de profesores necesarios
5. **Integración con RRHH**: Sincronizar con sistema de recursos humanos

---

## 📝 Resumen Ejecutivo

### ¿Por qué usar instructores sintéticos?

**SIN esta funcionalidad:**
- ❌ No puedes generar horarios si faltan profesores
- ❌ No sabes cuántos profesores necesitas
- ❌ No puedes planificar con anticipación

**CON esta funcionalidad:**
- ✅ Genera horarios completos siempre
- ✅ Identifica exactamente cuántos profesores faltan
- ✅ Facilita la planificación y presupuestación
- ✅ Permite tomar decisiones informadas

### Flujo recomendado:

```
Inicio de semestre
    ↓
Importar cursos (XML)
    ↓
Generar horario → Crea sintéticos automáticamente
    ↓
Ver reporte → Identifica necesidades
    ↓
Asignar profesores reales
    ↓
Regenerar horario final
    ↓
Limpiar sintéticos
    ↓
¡Horario listo!
```

---

**¡Los instructores sintéticos son una herramienta de PLANIFICACIÓN, no un producto final!**
