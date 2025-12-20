# Sistema de Generación de Horarios - Guía Técnica

## 🎯 Objetivo
Generar horarios académicos cumpliendo:
- Sin cruces de horario (sala/profesor)
- Máximo 3 sesiones consecutivas del mismo curso
- 10 min break entre cursos diferentes  
- Laboratorios NO cuentan como sesiones consecutivas
- Bloques de 50 minutos

## 📊 Rendimiento
- **Antes**: 5-10 segundos (con BD)
- **Ahora**: ~140 ms (sin BD)
- **Mejora**: 75x más rápido

## 🗂️ Estructura

### Archivos Principales

**Backend**:
- `direct_generator.py` - Generador optimizado sin BD
- `simple_xml_converter.py` - Convierte JSON a XML limpio
- `simple_xml_parser.py` - Lee XML limpio
- `fast_api_views.py` - API endpoints optimizados

**Scripts de Prueba**:
- `test_sistema_limpio.py` - Prueba completa del sistema

**Datos**:
- `datos_horarios.json` - Datos de entrada (38 cursos)
- `pu-fal07-llr_clean.xml` - XML limpio generado

## 🔌 API Endpoints

### POST /api/schedules/generate-from-file/
Genera horario desde archivo (JSON/XML).

```bash
curl -X POST http://localhost:8000/api/schedules/generate-from-file/ \
  -F "file=@datos_horarios.json"
```

**Respuesta**:
```json
{
  "success": true,
  "asignaciones": [...],
  "estadisticas": {
    "cursos_asignados": 38,
    "cursos_totales": 38,
    "tiempo_ms": 141
  }
}
```

### POST /api/schedules/generate-from-data/
Genera desde JSON en body (para bucket/cloud).

```bash
curl -X POST http://localhost:8000/api/schedules/generate-from-data/ \
  -H "Content-Type: application/json" \
  -d @datos_horarios.json
```

## 🧪 Pruebas

```powershell
# Activar entorno
.\env\Scripts\Activate.ps1

# Ejecutar prueba completa
python test_sistema_limpio.py
```

**Resultado esperado**:
```
✅ XML limpio generado
✅ Salas: 9, Instructores: 18, Clases: 38
✅ Tiempo: ~140 ms
✅ Cursos asignados: 38/38
✅ Máximo bloques consecutivos: 3 (≤ 3)
✅ Todos los bloques de 50 min
```

## ⚙️ Configuración

Editar `datos_horarios.json`:

```json
{
  "configuracion_general": {
    "duracion_bloque_min": 50,
    "max_bloques_consecutivos_por_sesion": 3,
    "descanso_entre_bloques_min": 10,
    "inicio_jornada": "07:00",
    "fin_jornada": "20:10"
  }
}
```

## 📱 Integración Frontend (React)

```typescript
// Componente de generación
const handleGenerate = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/schedules/generate-from-file/', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  // Respuesta en ~140ms
  console.log(`Generado en ${result.estadisticas.tiempo_ms}ms`);
  setSchedule(result.asignaciones);
};
```

## 📋 Formato XML Limpio

El XML generado solo incluye campos necesarios:

```xml
<timetable version="3.0">
  <rooms>
    <room id="101" capacity="50" type="normal"/>
  </rooms>
  
  <instructors>
    <instructor id="P001" name="Juan Perez"/>
  </instructors>
  
  <classes>
    <class id="CS101" name="Algoritmos" students="30" 
           instructor="P001" type="normal">
      <timeslot days="1010100" start="24" length="34" 
                blocks="3" is_lab="false"/>
    </class>
  </classes>
</timetable>
```

**Campos eliminados** (innecesarios):
- ❌ dates, committed, config, subpart
- ❌ location, preference, pattern
- ❌ groupConstraints, students (secciones completas)

## 🔍 Reglas Implementadas

### 1. Sin Cruces de Horario
```python
# Verifica sala y profesor en cada slot de 5 min
for slot in range(inicio, fin):
    if (sala, slot, dia) ocupado: conflicto = True
    if (profesor, slot, dia) ocupado: conflicto = True
```

### 2. Máximo 3 Sesiones Consecutivas
```python
# Solo cuenta si es el mismo curso y NO es lab
if mismo_curso and not es_lab and not lab_anterior:
    if num_consecutivas >= 3: conflicto = True
```

### 3. Break de 10 min Entre Cursos
```python
# 10 min = 2 slots de 5 min
break_slots = 2
hora_anterior = hora_inicio - break_slots
# Si hay sesión anterior diferente, se respeta el break
```

### 4. Labs No Cuentan como Consecutivos
```python
if curso.requiere_lab > 0:
    es_lab = True
    # No incrementa contador de sesiones consecutivas
```

## 🚀 Flujo Completo

1. **Preparar datos**: `datos_horarios.json`
2. **Generar XML** (opcional): `python test_sistema_limpio.py`
3. **Generar horario**: API endpoint o script
4. **Resultado**: JSON con asignaciones + estadísticas

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
cd "d:\Documentos\UNSA CICLO 10\INTERDISCIPLINAR 3\Sistema-Generacion-Horarios"
python test_sistema_limpio.py
```

### Frontend lento
```typescript
// Verificar endpoint correcto
// ❌ /api/schedules/generate/
// ✅ /api/schedules/generate-from-file/
```

### Bloques no se respetan
```bash
# Ejecutar verificación
python test_sistema_limpio.py
# Debe mostrar: ✅ Máximo bloques: 3 (≤ 3)
```

## 📦 Archivos Generados

- `pu-fal07-llr_clean.xml` - XML limpio (sin campos innecesarios)
- `horario_final.json` - Horario generado con todas las reglas

## ✅ Validación

```bash
# Ejecutar test completo
python test_sistema_limpio.py

# Debe pasar todas las verificaciones:
✅ XML limpio generado
✅ Generación < 200ms
✅ 100% cursos asignados
✅ Máx 3 bloques consecutivos
✅ Bloques de 50 min
```

---

**Versión**: 3.0 | **Fecha**: Diciembre 2025
