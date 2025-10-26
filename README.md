# 🎓 Sistema de Generación de Horarios Universitarios# 🎓 Sistema de Generación de Horarios



## 📌 Estado Actual del ProyectoSistema de gestión y generación automática de horarios universitarios desarrollado con Django REST Framework y React + TypeScript. Utiliza un **algoritmo genético** para optimizar la asignación de clases, aulas y horarios.



> **Fecha:** Octubre 2025  [![Estado](https://img.shields.io/badge/Estado-Completo-success)](./PROJECT_STATUS.md)

> **Branch:** `christiam` (desarrollo activo)  [![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)](./IMPLEMENTATION_SUMMARY.md)

> **Estado:** 🟡 En optimización de fitness (56% → 70%+)[![Documentación](https://img.shields.io/badge/Docs-Completa-green)](./INDEX.md)



### 🎯 Objetivo Actual> 🚀 **¡Implementación completa del algoritmo genético!** Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para detalles.

Mejorar el **fitness del algoritmo genético** de **56.5%** a **70%+** mediante la optimización de restricciones y operadores genéticos.

---

---

## 📋 Índice Rápido

## 📊 Situación Actual

- [🎯 Características](#-características)

### Resultados Anteriores- [🛠️ Stack Tecnológico](#️-stack-tecnológico)

```- [📚 Documentación](#-documentación)

Dataset: LLR (Large Lecture Room)- [🚀 Instalación](#-instalación)

- 896 clases- [▶️ Ejecución](#️-ejecución)

- 455 instructores  - [🧬 Algoritmo Genético](#-algoritmo-genético)

- 63 aulas- [🔌 API Endpoints](#-api-endpoints)

- 210 restricciones de grupo (BTB, DIFF_TIME, SAME_TIME)

---

Fitness alcanzado: 253,005 / 448,000 = 56.5%

Conflictos de aula: 213## 🎯 Características

Violaciones de capacidad: 99

```### ✅ Implementado

- **Importación de datos** desde archivos XML (formato UniTime)

### Problemas Identificados- **Dashboard** con estadísticas del sistema

1. ❌ **Restricciones de instructor desactivadas** - No se consideraban durante evolución- **Gestión CRUD** completa de salas, instructores, cursos, clases y estudiantes

2. ❌ **Peso de restricciones muy alto** (1000) - Convergencia lenta- **API REST** completa con Django REST Framework

3. ❌ **Restricciones BTB no evaluadas** - 210 restricciones ignoradas- **Interfaz moderna** con React + TypeScript + Vite

4. ❌ **Operador de reparación limitado** - Solo corregía capacidad- **🧬 Algoritmo Genético** para generación automática de horarios

5. ❌ **Tasa de mutación conservadora** (0.15) - Poca exploración- **Optimización de restricciones** duras y blandas

- **Visualización de calendario** compatible con FullCalendar.js

---

### Pipeline de Datos

## 🚀 Mejoras Implementadas (v2.0)

1. **Entrada**: CSV/XML o carga manual de datos institucionales

### 1️⃣ **Peso de Restricciones Reducido** ✅2. **Procesamiento**: Algoritmo genético optimiza asignaciones

```python3. **Generación**: Matriz de horarios factible y optimizada

# Antes: hard_constraint_weight=1000.04. **Visualización**: Interfaz interactiva con FullCalendar.js

# Ahora: hard_constraint_weight=100.0

```## 🛠️ Stack Tecnológico

- **Impacto:** +5-10% fitness

- **Beneficio:** Convergencia más rápida### Backend

- Framework: Django 4.2+

### 2️⃣ **Restricciones de Instructor Habilitadas** ✅- API: Django REST Framework 3.14+

```python- Base de Datos: SQLite

# Ahora se evalúan conflictos de profesor durante la evolución- **Optimización**: Algoritmo Genético con NumPy

violations += self._check_instructor_conflicts(individual, time_slots_map)

```### Frontend

- **Impacto:** +8-12% fitness- Build Tool: Vite 5.0

- **Beneficio:** Horarios más realistas- Framework: React 18.2

- Lenguaje: TypeScript 5.2

### 3️⃣ **Restricciones BTB Implementadas** ✅- Routing: React Router 6.20

- Evalúa las 210 restricciones de grupo (Back-To-Back, DIFF_TIME, SAME_TIME)- HTTP Client: Axios 1.6

- Penaliza clases consecutivas en edificios lejanos:- **Calendario**: FullCalendar.js (planeado)

  - `>200m`: penalización +100

  - `50-200m`: penalización +20## 📋 Requisitos Previos

  - `0-50m`: penalización +2

- **Impacto:** +3-5% fitness- Python 3.8+

- Node.js 18+ y npm

### 4️⃣ **Mutación Aumentada** ✅- Git

```python

# Antes: mutation_rate=0.15## 🚀 Instalación

# Ahora: mutation_rate=0.20

```### Instalación Automática (Recomendada)

- **Impacto:** +2-4% fitness

- **Beneficio:** Mayor exploración del espacio de soluciones```bash

cd Sistemas-Generacion-Horarios

### 5️⃣ **Operador de Reparación Mejorado** ✅chmod +x setup.sh

Ahora corrige:./setup.sh

- ✅ Violaciones de capacidad```

- ✅ Conflictos de aula (NUEVO)

- ✅ Reasignación inteligente de clases### Instalación Manual

- **Impacto:** +5-8% fitness

#### Backend (Django)

### 6️⃣ **Script de Verificación** ✅

Nuevo comando para verificar conflictos de instructores:```bash

```bashcd backend

python manage.py verify_instructor_conflicts --schedule_id <ID>python3 -m venv venv

```source venv/bin/activate

pip install -r requirements.txt

---python manage.py makemigrations

python manage.py migrate

## 📈 Resultados Esperados```



### Mejora Total Estimada: +23-39%#### Frontend (React)



| Métrica | Antes | Objetivo | Mejora |```bash

|---------|-------|----------|--------|cd frontend

| **Fitness** | 253,005 (56.5%) | 313,600+ (70%+) | +13.5% |npm install

| **Conflictos Aula** | 213 | <50 | -77% |```

| **Conflictos Instructor** | ? | <30 | N/A |

| **Violaciones Capacidad** | 99 | <20 | -80% |## ▶️ Ejecución



---### Opción 1: Script Automático



## 🛠️ Stack Tecnológico```bash

chmod +x run.sh

### Backend./run.sh

- **Framework:** Django 4.2+```

- **API:** Django REST Framework 3.14+

- **Base de Datos:** SQLite### Opción 2: Manual

- **Algoritmo:** Genético con NumPy

- **Restricciones:** Hard (peso 100) + Soft (peso 1.0)**Terminal 1 - Backend:**

```bash

### Frontendcd backend

- **Build Tool:** Vite 5.0source venv/bin/activate

- **Framework:** React 18.2 + TypeScript 5.2python manage.py runserver

- **Routing:** React Router 6.20```

- **HTTP Client:** Axios 1.6

**Terminal 2 - Frontend:**

### Algoritmo Genético```bash

- **Población:** 200 individuoscd frontend

- **Generaciones:** 200-400npm run dev

- **Selección:** Torneo (tamaño 5)```

- **Cruce:** Un punto (80%)

- **Mutación:** Inteligente (20%)## 🌐 Acceso al Sistema

- **Elitismo:** Top 10 individuos

- **Heurísticas:** Población híbrida (30% greedy, 30% greedy+mutación, 40% random)- Frontend: http://localhost:3000

- Backend API: http://localhost:8000/api/

---- Admin Django: http://localhost:8000/admin/



## 📋 Estructura del Proyecto## 📁 Estructura del Proyecto



``````

proyecto-ti3/Sistemas-Generacion-Horarios/

├── backend/├── backend/

│   ├── schedule_app/│   ├── timetable_system/        # Configuración Django

│   │   ├── models.py                    # Modelos Django│   ├── schedule_app/

│   │   ├── genetic_algorithm.py         # 🧬 Algoritmo genético│   │   ├── models.py            # Modelos de datos

│   │   ├── constraints.py               # 🔍 Validación de restricciones│   │   ├── views.py             # API endpoints

│   │   ├── schedule_generator.py        # 🎯 Orquestador principal│   │   ├── serializers.py       # Serializadores DRF

│   │   ├── heuristics.py                # 🧠 Inicialización inteligente│   │   ├── genetic_algorithm.py # 🧬 Algoritmo genético

│   │   ├── xml_parser.py                # 📄 Importador XML│   │   ├── constraints.py       # Restricciones y validación

│   │   └── management/commands/│   │   ├── schedule_generator.py # Servicio de generación

│   │       ├── generate_schedule.py     # CLI generación│   │   └── management/

│   │       └── verify_instructor_conflicts.py  # Verificador│   │       └── commands/

│   ├── db.sqlite3                       # Base de datos│   │           └── generate_schedule.py

│   └── manage.py│   ├── manage.py

├── frontend/│   └── requirements.txt

│   └── src/                             # React + TypeScript├── frontend/

├── docs/│   ├── src/

│   ├── MEJORAS_FITNESS_V2.md           # 📘 Guía completa de mejoras│   │   ├── components/

│   ├── RESUMEN_MEJORAS.md              # 📄 Resumen ejecutivo│   │   ├── services/

│   ├── CHANGELOG_V2.md                 # 📝 Changelog técnico│   │   ├── types/

│   └── OPTIMIZACION_RESTRICCIONES.md   # 🔧 Optimizaciones│   │   ├── App.tsx

├── pu-fal07-llr.xml                    # Dataset LLR (896 clases)│   │   └── main.tsx

├── consultas_bd_llr.sql                # 📊 Queries de análisis│   ├── package.json

└── README.md                           # 📖 Este archivo│   └── tsconfig.json

```├── pu-fal07-cs.xml             # Dataset de prueba (UniTime)

├── setup.sh

---├── run.sh

├── README.md

## 🚀 Instalación y Ejecución└── GENETIC_ALGORITHM.md        # 📖 Documentación del algoritmo

```

### 1. Instalación Backend

## 📚 Uso del Sistema

```bash

cd backend### 1. Importar Datos XML

python3 -m venv venv

source venv/bin/activate1. Accede a http://localhost:3000/import

pip install -r requirements.txt2. Selecciona el archivo `pu-fal07-cs.xml`

python manage.py migrate3. Marca "Limpiar datos existentes" si deseas reemplazar todo

```4. Haz clic en "Importar XML"



### 2. Importar Dataset LLR### 2. Generar Horario con Algoritmo Genético



```bash#### Opción A: Usando la API REST

curl -X POST http://localhost:8000/api/import-xml/ \

  -F "file=@pu-fal07-llr.xml" \```bash

  -F "clear_existing=true"curl -X POST http://localhost:8000/api/schedules/generate/ \

```  -H "Content-Type: application/json" \

  -d '{

### 3. Generar Horario (Mejoras v2.0)    "name": "Horario Optimizado 2025-I",

    "description": "Horario generado con algoritmo genético",

```bash    "population_size": 150,

cd backend    "generations": 300,

source venv/bin/activate    "mutation_rate": 0.15,

python manage.py generate_schedule \    "crossover_rate": 0.85,

  --name "LLR Mejorado v2.0" \    "elitism_size": 5,

  --population 200 \    "tournament_size": 5

  --generations 200  }'

``````



**Tiempo estimado:** 15-20 minutos  #### Opción B: Usando comando de Django

**Fitness esperado:** 310,000-340,000 (69-76%)

```bash

### 4. Verificar Conflictoscd backend

python manage.py generate_schedule \

```bash  --name "Horario Test" \

# Obtener ID del horario generado (ejemplo: 25)  --population 150 \

python manage.py verify_instructor_conflicts --schedule_id 25  --generations 300 \

  --mutation-rate 0.15 \

# Exportar conflictos a CSV  --crossover-rate 0.85

python manage.py verify_instructor_conflicts --schedule_id 25 --export```

```

### 3. Ver Resultados

---

```bash

## 📊 Comandos de Análisis# Obtener resumen del horario

curl http://localhost:8000/api/schedules/1/summary/

### Contar Asignaciones

```bash# Obtener vista de calendario (FullCalendar.js format)

sqlite3 db.sqlite3 "SELECT COUNT(*) FROM schedule_assignments WHERE schedule_id = 25;"curl http://localhost:8000/api/schedules/1/calendar_view/

```

# Activar horario como activo

### Detectar Conflictos de Aulacurl -X POST http://localhost:8000/api/schedules/1/activate/

```bash```

sqlite3 db.sqlite3 "$(cat consultas_bd_llr.sql | grep -A 20 'Conflictos de aula')"

```### 4. Gestionar Datos



### Calcular Porcentaje de FitnessAccede a las diferentes secciones desde el menú:

```python- **Salas**: Agregar, editar o eliminar aulas

fitness_obtenido = 340000  # Reemplazar con tu valor- **Instructores**: Gestión de profesores

porcentaje = (fitness_obtenido / 448000) * 100- **Cursos**: Visualizar cursos importados

print(f"Fitness: {porcentaje:.1f}%")- **Clases**: Ver clases y sus asignaciones

```- **Estudiantes**: Administrar estudiantes

- **Horarios**: Ver y generar horarios

---

## 🧬 Algoritmo Genético

## 🎯 Métricas de Éxito

El sistema implementa un algoritmo genético completo para optimizar la asignación de horarios. Ver [GENETIC_ALGORITHM.md](./GENETIC_ALGORITHM.md) para documentación detallada.

### ✅ Mínimo Aceptable (70%)

- Fitness >= 313,600### Restricciones Duras (DEBEN cumplirse)

- Conflictos aula < 50- ❌ No solapamiento de clases del mismo instructor

- Conflictos instructor < 30- ❌ No solapamiento de clases en la misma aula

- Violaciones capacidad < 20- ❌ No solapamiento de estudiantes del mismo curso

- ❌ Capacidad de aula suficiente

### ⭐ Objetivo (75%)

- Fitness >= 336,000### Restricciones Blandas (Preferencias)

- Conflictos aula < 30- ⭐ Preferencias de aula por clase

- Conflictos instructor < 20- ⭐ Preferencias de horario

- Violaciones capacidad < 10- ⭐ Minimización de gaps en horarios de instructores



### 🏆 Excelente (80%)### Parámetros Recomendados

- Fitness >= 358,400

- Conflictos aula < 20| Parámetro | Por Defecto | Descripción |

- Conflictos instructor < 10|-----------|-------------|-------------|

- Violaciones capacidad < 5| `population_size` | 100 | Tamaño de la población |

| `generations` | 200 | Número de iteraciones |

---| `mutation_rate` | 0.1 | Probabilidad de mutación (0-1) |

| `crossover_rate` | 0.8 | Probabilidad de cruce (0-1) |

## 📝 Archivos Importantes| `elitism_size` | 5 | Individuos élite preservados |

| `tournament_size` | 5 | Tamaño del torneo de selección |

### Documentación Técnica (en `docs/`)

- **MEJORAS_FITNESS_V2.md** - Guía completa de mejoras implementadas## 🔌 API Endpoints

- **RESUMEN_MEJORAS.md** - Resumen ejecutivo para stakeholders

- **CHANGELOG_V2.md** - Changelog técnico detallado### Recursos Principales

- **OPTIMIZACION_RESTRICCIONES.md** - Detalles de optimizaciones

```

### ScriptsGET    /api/rooms/              # Listar salas

- **backend/ejecutar_mejoras_v2.sh** - Script automático de ejecución con análisisPOST   /api/rooms/              # Crear sala

- **consultas_bd_llr.sql** - 10 consultas SQL para análisis de horariosGET    /api/rooms/{id}/         # Detalle de sala

PUT    /api/rooms/{id}/         # Actualizar sala

### DatasetsDELETE /api/rooms/{id}/         # Eliminar sala

- **pu-fal07-llr.xml** - Dataset Large Lecture Room (896 clases, 455 instructores)

GET    /api/instructors/        # Listar instructores

---POST   /api/instructors/        # Crear instructor

GET    /api/courses/            # Listar cursos

## 🔧 Configuración del AlgoritmoGET    /api/classes/            # Listar clases

GET    /api/students/           # Listar estudiantes

### Archivo: `schedule_app/constraints.py````



**Restricciones Duras (peso 100):**### Endpoints de Horarios (Algoritmo Genético)

- ✅ Conflictos de instructor (HABILITADO)

- ✅ Conflictos de aula```

- ✅ Violaciones de capacidadPOST   /api/schedules/generate/        # Generar horario con AG

- ⏸️ Conflictos de estudiantes (post-procesamiento)GET    /api/schedules/                 # Listar horarios

GET    /api/schedules/{id}/            # Detalle de horario

**Restricciones Blandas (peso 1.0):**POST   /api/schedules/{id}/activate/   # Activar horario

- Preferencias de aulaGET    /api/schedules/{id}/summary/    # Resumen detallado

- Preferencias de horarioGET    /api/schedules/{id}/calendar_view/  # Vista FullCalendar

- Gaps en instructores```

- Restricciones BTB (distancia entre edificios)

### Endpoints Especiales

### Archivo: `schedule_app/genetic_algorithm.py`

```

**Operadores:**POST   /api/import-xml/         # Importar archivo XML

- **Selección:** Torneo (tamaño 5)GET    /api/dashboard-stats/    # Estadísticas del dashboard

- **Cruce:** Un punto (80%)```

- **Mutación:** Inteligente (20%, adapta aulas por capacidad)

- **Reparación:** Capacidad + Conflictos de aula (10% probabilidad)## 📊 Dataset de Prueba

- **Elitismo:** Top 10 individuos

El proyecto incluye el dataset **UniTime pu-fal07-cs** (XML) con:

**Anti-estancamiento:**- Cursos de Computer Science

- Detecta estancamiento cada 30 generaciones- Múltiples instructores y aulas

- Aumenta mutación temporalmente- Restricciones de horarios

- Inyecta 20% de población nueva- Preferencias de asignación

- Aplica mutación intensa a 30% de población

## 🤝 Contribución

---

Las contribuciones son bienvenidas. Por favor:

## 🐛 Problemas Conocidos1. Fork el proyecto

2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)

### 1. Heurísticas Lentas en Dataset Grande3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)

**Síntoma:** Inicialización tarda >2 minutos con 896 clases  4. Push a la rama (`git push origin feature/AmazingFeature`)

**Solución temporal:** Usar `--no-heuristics` para inicialización rápida5. Abre un Pull Request

```bash

python manage.py generate_schedule --no-heuristics --population 200 --generations 200## 📄 Licencia

```

Licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

### 2. Fitness No Alcanza 70% con 200 Generaciones

**Solución:** Aumentar generaciones y población## 👥 Autores

```bash

python manage.py generate_schedule --population 250 --generations 300- Equipo de desarrollo TI3

```

## 🔗 Enlaces Útiles

---

- [Django Documentation](https://docs.djangoproject.com/)

## 📚 Recursos Adicionales- [Django REST Framework](https://www.django-rest-framework.org/)

- [React Documentation](https://react.dev/)

### Documentación- [FullCalendar](https://fullcalendar.io/)

- [Guía de Mejoras v2.0](docs/MEJORAS_FITNESS_V2.md)- [UniTime Project](https://www.unitime.org/)

- [Merge Guide](MERGE_GUIDE.md)

---

### Datasets UniTime

- [UniTime Project](https://www.unitime.org/)**Nota**: Para información detallada sobre el algoritmo genético, consulta [GENETIC_ALGORITHM.md](./GENETIC_ALGORITHM.md)
- Formato XML v2.4 soportado

### Papers de Referencia
- Algoritmos genéticos para timetabling
- Constraint satisfaction problems
- Heurísticas de inicialización para poblaciones

---

## 👥 Equipo de Desarrollo

**Branch actual:** `christiam` (desarrollo)  
**Objetivo:** Optimización de fitness 56% → 70%+  
**Próximo milestone:** Merge a `main` cuando fitness >= 70%

---

## 📞 Contacto y Soporte

Para dudas o sugerencias sobre las mejoras implementadas:
1. Revisar documentación en `docs/`
2. Ejecutar script de prueba: `./backend/ejecutar_mejoras_v2.sh`
3. Verificar conflictos con: `python manage.py verify_instructor_conflicts`

---

## 🔄 Próximos Pasos

1. ✅ Implementar mejoras v2.0 (COMPLETADO)
2. 🔄 Ejecutar pruebas con 200 pop / 200 gen (EN PROGRESO)
3. ⏳ Validar fitness >= 70%
4. ⏳ Resolver heurísticas lentas
5. ⏳ Merge a branch `main`
6. ⏳ Documentar resultados finales

---

**Última actualización:** Octubre 2025  
**Versión:** 2.0 (Optimización de Fitness)
