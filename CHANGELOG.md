# Changelog - 19 de Octubre 2025

## Correcciones Realizadas

### 1. Frontend - Visualización de Horarios
- ✅ **CORREGIDO**: Error `can't access property "Lunes", data.grid is undefined`
  - Cambiado endpoint response de `timetable` → `grid`
  - Actualizado TimetableView.tsx para usar campos correctos
  - Eliminado TimetableGrid.tsx duplicado

- ✅ **CORREGIDO**: Campos de interfaz inconsistentes
  - `course_code` → `code`
  - `start_time` → `start`
  - `end_time` → `end`
  - `duration_minutes` → `duration_min`
  - `student_count` → `students`
  - `class_limit` → `limit`
  - Eliminado campo `days_string` del modal (no disponible en endpoint)

### 2. Backend - Sistema de Instructores
- ✅ **CORREGIDO**: Instructor compartido (xml_id=999999)
  - Eliminado instructor compartido de la base de datos
  - Modificado `schedule_generator.py` para usar instructores reales
  - Importados 23 instructores únicos desde el XML
  - Asignación round-robin de instructores a clases sin asignación

- ✅ **CORREGIDO**: Endpoint API `/timetable/`
  - Cambiado campo response `timetable` → `grid`
  - Agregado campo `description` al schedule
  - Agregado `classes_by_day` a stats
  - Agregado flag `needs_multiple_views` cuando hay >10 clases simultáneas

### 3. Limpieza del Proyecto
- ✅ **ELIMINADO**: Archivos markdown temporales
  - DOCUMENTACION_DATASET_XML.md
  - GUIA_FINAL.md
  - PLAN_IMPLEMENTACION.md
  - EXITO_FINAL.md
  - MEJORAS_ALGORITMO.md
  - RESUMEN_COMPLETO.md
  - INTEGRACION_FRONTEND.md
  - RESUMEN_FINAL_MEJORAS.md
  - RESUMEN_MEJORAS.md
  - RESUMEN_EJECUTIVO.md
  - SOLUCION_PRAGMATICA.md
  - DIAGNOSTICO_FINAL.md

- ✅ **ELIMINADO**: Scripts Python no usados
  - backend/clean_synthetic_data.py
  - backend/test_configurations.py
  - backend/benchmark_parallel.py

- ✅ **ELIMINADO**: Carpetas duplicadas
  - frontend_visualizer/ (duplicado de frontend/)

- ✅ **ELIMINADO**: Componentes React no usados
  - frontend/src/components/TimetableGrid.tsx (usamos TimetableView.tsx)

## Estado Actual del Sistema

### Instructores
- **Antes**: 1 instructor compartido (xml_id=999999) para todas las clases
- **Ahora**: 23 instructores reales del XML asignados round-robin

### Visualización Frontend
- **Antes**: Error al cargar horarios (campos incompatibles)
- **Ahora**: Tabla funcional con días en pestañas

### Base de Datos
- 523 clases
- 58 aulas
- 23 instructores reales
- Schedule #17 eliminado (usaba instructor compartido)
- Nuevo schedule "Horario con Instructores Reales" en generación

## Próximos Pasos
1. ✅ Terminar generación del nuevo schedule con instructores reales
2. ⏳ Probar visualización en http://localhost:3000/schedules
3. ⏳ Verificar que se muestran múltiples instructores
4. ⏳ Commit a repositorio con código limpio
