# 🎓 Sistema de Generación de Horarios - Guía de Uso Rápido

## ✅ Estado del Sistema

**INSTALACIÓN COMPLETADA EXITOSAMENTE** ✨

- ✅ Backend Django instalado y corriendo en http://127.0.0.1:8000
- ✅ Frontend React+Vite instalado y corriendo en http://localhost:3000
- ✅ Base de datos SQLite creada y migrada
- ✅ Superusuario creado: `admin` / `12345678`
- ✅ Todos los componentes funcionando correctamente

---

## 🚀 Inicio Rápido

### Opción 1: Usar script automático
```bash
cd ~/Documentos/ti3/proyecto-ti3
./run.sh
```

### Opción 2: Inicio manual (2 terminales)

**Terminal 1 - Backend:**
```bash
cd ~/Documentos/ti3/proyecto-ti3/backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd ~/Documentos/ti3/proyecto-ti3/frontend
npm run dev
```

---

## 🌐 URLs del Sistema

| Servicio | URL | Descripción |
|----------|-----|-------------|
| 🖥️ **Frontend** | http://localhost:3000 | Aplicación web principal |
| 🔧 **API Backend** | http://127.0.0.1:8000/api/ | REST API endpoints |
| 👨‍💼 **Admin Django** | http://127.0.0.1:8000/admin/ | Panel de administración |

**Credenciales Admin:**
- Usuario: `admin`
- Contraseña: `12345678`

---

## 📊 Funcionalidades Disponibles

### 1. Dashboard Principal
**URL:** http://localhost:3000

Visualiza estadísticas en tiempo real:
- 🏛️ Total de salas
- 👨‍🏫 Instructores registrados
- 📚 Cursos disponibles
- 📝 Clases programadas
- 👨‍🎓 Estudiantes inscritos
- ⏰ Franjas horarias

### 2. Importar Datos XML
**URL:** http://localhost:3000/import-xml

**Pasos:**
1. Haz clic en "Seleccionar archivo XML"
2. Selecciona el archivo `pu-fal07-cs.xml` (ubicado en la raíz del proyecto)
3. ✅ Marca "Limpiar datos existentes" si quieres reemplazar todo
4. Clic en "Importar XML"
5. Espera a que termine el procesamiento

**Nota:** El archivo tiene ~28,688 líneas, puede tardar 10-30 segundos.

### 3. Gestión de Salas
**URL:** http://localhost:3000/rooms

- Ver todas las salas
- Agregar nueva sala (botón + Agregar Sala)
- Editar sala existente
- Eliminar sala

**Campos:**
- ID XML
- Capacidad
- Ubicación
- ¿Es restricción?

### 4. Gestión de Instructores
**URL:** http://localhost:3000/instructors

- Ver todos los instructores
- Agregar instructor
- Editar datos
- Eliminar instructor

**Campos:**
- ID XML
- Nombre
- Email

### 5. Gestión de Cursos
**URL:** http://localhost:3000/courses

- Ver todos los cursos importados
- Código del curso
- Nombre completo
- Cantidad de clases

### 6. Gestión de Clases
**URL:** http://localhost:3000/classes

- Ver todas las clases
- ID XML
- Curso asociado
- Límite de estudiantes
- Instructores asignados
- Estado (Comprometida/Pendiente)

### 7. Gestión de Estudiantes
**URL:** http://localhost:3000/students

- Ver todos los estudiantes
- Agregar estudiante
- Editar información
- Eliminar estudiante
- Ver clases inscritas

**Campos:**
- ID XML
- Nombre
- Email

### 8. Horarios
**URL:** http://localhost:3000/schedules

**Estado:** 🚧 Módulo en desarrollo

Esta sección mostrará los horarios generados por el algoritmo genético (próxima fase).

---

## 🛠️ API Endpoints

### Recursos CRUD

```bash
# Salas
GET    http://127.0.0.1:8000/api/rooms/
POST   http://127.0.0.1:8000/api/rooms/
GET    http://127.0.0.1:8000/api/rooms/{id}/
PUT    http://127.0.0.1:8000/api/rooms/{id}/
DELETE http://127.0.0.1:8000/api/rooms/{id}/

# Instructores
GET    http://127.0.0.1:8000/api/instructors/
POST   http://127.0.0.1:8000/api/instructors/
GET    http://127.0.0.1:8000/api/instructors/{id}/
PUT    http://127.0.0.1:8000/api/instructors/{id}/
DELETE http://127.0.0.1:8000/api/instructors/{id}/

# Cursos
GET    http://127.0.0.1:8000/api/courses/
GET    http://127.0.0.1:8000/api/courses/{id}/

# Clases
GET    http://127.0.0.1:8000/api/classes/
GET    http://127.0.0.1:8000/api/classes/{id}/

# Estudiantes
GET    http://127.0.0.1:8000/api/students/
POST   http://127.0.0.1:8000/api/students/
GET    http://127.0.0.1:8000/api/students/{id}/
PUT    http://127.0.0.1:8000/api/students/{id}/
DELETE http://127.0.0.1:8000/api/students/{id}/

# Horarios
GET    http://127.0.0.1:8000/api/schedules/
GET    http://127.0.0.1:8000/api/schedules/{id}/

# Franjas horarias
GET    http://127.0.0.1:8000/api/timeslots/
```

### Endpoints Especiales

```bash
# Importar XML
POST http://127.0.0.1:8000/api/import-xml/
Content-Type: multipart/form-data
Body: file (archivo XML), clear_existing (boolean)

# Estadísticas del Dashboard
GET http://127.0.0.1:8000/api/dashboard-stats/

# Activar horario
POST http://127.0.0.1:8000/api/schedules/{id}/activate/

# Vista de calendario
GET http://127.0.0.1:8000/api/schedules/{id}/calendar-view/
```

---

## 📦 Estructura de Datos

### Room (Sala)
```json
{
  "id": 1,
  "xml_id": 1001,
  "capacity": 30,
  "location": "Edificio A - Piso 2",
  "is_constraint": false
}
```

### Instructor
```json
{
  "id": 1,
  "xml_id": 2001,
  "name": "Dr. Juan Pérez",
  "email": "juan.perez@university.edu",
  "class_count": 3
}
```

### Course (Curso)
```json
{
  "id": 1,
  "xml_id": 3001,
  "name": "Algoritmos y Estructura de Datos",
  "code": "CS-101",
  "class_count": 2
}
```

### Class (Clase)
```json
{
  "id": 1,
  "xml_id": 4001,
  "offering_name": "CS-101 Lab A",
  "class_limit": 25,
  "committed": true,
  "instructor_names": ["Dr. Juan Pérez"],
  "room_names": ["Lab 301"]
}
```

### Student (Estudiante)
```json
{
  "id": 1,
  "xml_id": 5001,
  "name": "María González",
  "email": "maria.gonzalez@student.edu",
  "enrolled_classes_count": 5
}
```

---

## 🧪 Casos de Prueba

### Test 1: Importar XML
1. Ve a http://localhost:3000/import-xml
2. Sube `pu-fal07-cs.xml`
3. Marca "Limpiar datos existentes"
4. Verifica que muestre estadísticas de importación

**Resultado esperado:**
```
✓ Salas importadas: ~50-100
✓ Instructores importados: ~100-200
✓ Cursos importados: ~50-100
✓ Clases importadas: ~200-500
✓ Estudiantes importados: ~500-2000
✓ Franjas horarias: ~100-300
```

### Test 2: Ver Dashboard
1. Ve a http://localhost:3000
2. Verifica que todas las tarjetas muestren números

**Resultado esperado:**
- Todas las métricas > 0
- Sin mensajes de error

### Test 3: CRUD de Salas
1. Ve a http://localhost:3000/rooms
2. Clic en "+ Agregar Sala"
3. Completa el formulario:
   - ID XML: 9999
   - Capacidad: 40
   - Ubicación: "Sala de Prueba"
4. Guarda
5. Verifica que aparezca en la tabla
6. Edita la sala
7. Elimina la sala

### Test 4: CRUD de Instructores
1. Ve a http://localhost:3000/instructors
2. Clic en "+ Agregar Instructor"
3. Completa:
   - ID XML: 9998
   - Nombre: "Prof. Test"
   - Email: "test@test.com"
4. Guarda y verifica

### Test 5: API con curl
```bash
# Ver estadísticas
curl http://127.0.0.1:8000/api/dashboard-stats/

# Ver todas las salas
curl http://127.0.0.1:8000/api/rooms/

# Crear una sala
curl -X POST http://127.0.0.1:8000/api/rooms/ \
  -H "Content-Type: application/json" \
  -d '{"xml_id": 9997, "capacity": 30, "location": "Test Room"}'
```

---

## 🐛 Solución de Problemas

### Problema: "Cannot connect to backend"
**Solución:**
```bash
# Verifica que el backend esté corriendo
cd ~/Documentos/ti3/proyecto-ti3/backend
source venv/bin/activate
python manage.py runserver
```

### Problema: Frontend no carga
**Solución:**
```bash
# Verifica que Vite esté corriendo
cd ~/Documentos/ti3/proyecto-ti3/frontend
npm run dev
```

### Problema: Error al importar XML
**Posibles causas:**
1. Backend no está corriendo
2. Archivo XML corrupto
3. Base de datos bloqueada

**Solución:**
```bash
# Reiniciar backend
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py runserver
```

### Problema: Puerto 8000 en uso
**Solución:**
```bash
# Usar otro puerto
python manage.py runserver 8001

# Actualizar en frontend/vite.config.ts:
# proxy: '/api' -> 'http://localhost:8001'
```

### Problema: Base de datos corrupta
**Solución:**
```bash
cd backend
rm db.sqlite3
python manage.py migrate
# Volver a importar XML
```

---

## 📝 Comandos Útiles

### Backend (Django)
```bash
# Activar entorno virtual
cd backend
source venv/bin/activate

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Shell de Django
python manage.py shell

# Ver todas las rutas
python manage.py show_urls  # Requiere django-extensions
```

### Frontend (React)
```bash
cd frontend

# Iniciar desarrollo
npm run dev

# Build para producción
npm run build

# Preview de producción
npm run preview

# Linter
npm run lint
```

### Base de Datos
```bash
# Abrir SQLite
cd backend
sqlite3 db.sqlite3

# Comandos SQLite útiles
.tables                    # Ver todas las tablas
.schema schedule_app_room  # Ver esquema de tabla
SELECT COUNT(*) FROM schedule_app_room;  # Contar registros
.quit                      # Salir
```

---

## 🔍 Monitoreo

### Ver logs del backend
```bash
cd backend
tail -f ../logs/backend.log
```

### Ver logs del frontend
```bash
cd frontend
tail -f ../logs/frontend.log
```

### Ver requests en tiempo real
Abre las DevTools del navegador (F12) → Pestaña Network

---

## 🎯 Próximos Pasos (Fase 2)

1. **Algoritmo Genético**
   - Implementar generación de horarios
   - Función de fitness
   - Operadores genéticos (selección, cruce, mutación)

2. **Restricciones**
   - Configuración de constraints
   - Validación de horarios
   - Manejo de conflictos

3. **Visualización**
   - Calendario interactivo con FullCalendar
   - Vista por instructor
   - Vista por sala
   - Vista por estudiante

4. **Exportación**
   - PDF de horarios
   - Excel/CSV
   - iCal para calendarios

5. **Optimizaciones**
   - Cache de consultas
   - Paginación
   - Búsqueda y filtros avanzados

---

## 📚 Documentación Adicional

- **Django REST Framework:** https://www.django-rest-framework.org/
- **React:** https://react.dev/
- **Vite:** https://vitejs.dev/
- **TypeScript:** https://www.typescriptlang.org/
- **FullCalendar:** https://fullcalendar.io/

---

## ✅ Checklist de Verificación

- [ ] Backend corriendo en http://127.0.0.1:8000
- [ ] Frontend corriendo en http://localhost:3000
- [ ] Admin Django accesible (admin/12345678)
- [ ] Dashboard muestra estadísticas
- [ ] Importación XML funciona
- [ ] CRUD de Salas funciona
- [ ] CRUD de Instructores funciona
- [ ] CRUD de Estudiantes funciona
- [ ] API responde correctamente
- [ ] No hay errores en consola del navegador

---

**¡Sistema listo para usar!** 🎉

Para cualquier duda, consulta el README.md o los comentarios en el código.
