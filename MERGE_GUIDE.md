# Pasos para Hacer Merge de christiam a main

## Situación Actual
- **Rama actual**: christiam
- **Rama destino**: main
- **Estado**: Todos los cambios ya están committeados en christiam

## Opción 1: Merge Directo (Recomendado si estás seguro)

```bash
# 1. Asegurarte de estar en rama christiam con todo committeado
git status

# 2. Cambiar a rama main
git checkout main

# 3. Hacer merge de christiam
git merge christiam -m "merge: integración de optimizaciones y correcciones desde christiam

- Sistema de instructores reales (23 instructores vs 1 compartido)
- Limpieza de código (eliminados emojis)
- Frontend corregido (visualización de horarios funcionando)
- Documentación técnica agregada (OPTIMIZACION_RESTRICCIONES.md)
- Proyecto limpio (eliminados archivos temporales)"

# 4. Revisar el merge
git log --oneline -10

# 5. Hacer push a main (cuando estés listo)
git push origin main
```

## Opción 2: Merge con Revisión (Más Seguro)

```bash
# 1. Cambiar a main
git checkout main

# 2. Ver qué cambios se van a mergear SIN hacer el merge
git diff main..christiam

# 3. Ver los commits que se van a traer
git log main..christiam --oneline

# 4. Si todo se ve bien, hacer el merge
git merge christiam

# 5. Si hay conflictos, resolverlos y luego:
git add .
git commit -m "merge: resueltos conflictos de merge christiam -> main"

# 6. Push cuando estés listo
git push origin main
```

## Opción 3: Merge con Squash (Un Solo Commit)

Si prefieres que todos los cambios de christiam aparezcan como un solo commit en main:

```bash
# 1. Cambiar a main
git checkout main

# 2. Hacer squash merge (combina todos los commits en uno)
git merge --squash christiam

# 3. Hacer commit con mensaje descriptivo
git commit -m "feat: optimización completa del sistema de horarios

Cambios principales:
- Sistema de instructores reales: 23 instructores distribuidos equitativamente
- Limpieza de código: eliminados emojis, código más profesional
- Frontend: visualización de horarios con tabla por días funcionando
- Backend API: endpoint /timetable/ corregido con formato 'grid'
- Algoritmo genético: mejorado control de estancamiento (threshold 50->30)
- Documentación: agregado OPTIMIZACION_RESTRICCIONES.md con análisis técnico
- Proyecto: eliminados archivos temporales y componentes duplicados

Archivos principales modificados:
- backend/schedule_app/schedule_generator.py
- backend/schedule_app/genetic_algorithm.py
- backend/schedule_app/api.py
- frontend/src/components/TimetableView.tsx
- frontend/src/components/Schedules.tsx

Fixes: #issue-frontend-no-carga, #issue-instructor-compartido"

# 4. Push
git push origin main
```

## Recomendación

**Usa Opción 1** si:
- Quieres mantener el historial completo de commits
- Los commits en christiam están bien organizados

**Usa Opción 3** si:
- Prefieres que main tenga un historial limpio
- Los commits en christiam fueron experimentales

## Después del Merge

```bash
# 1. Verificar que main tiene todos los cambios
git checkout main
git log --oneline -5

# 2. Probar que todo funciona
cd backend
source venv/bin/activate
python manage.py test schedule_app

# 3. Hacer push a origin/main
git push origin main

# 4. (Opcional) Borrar rama christiam si ya no la necesitas
# git branch -d christiam  # local
# git push origin --delete christiam  # remota
```

## Rollback en Caso de Error

Si algo sale mal después del merge:

```bash
# Ver el SHA del commit antes del merge
git log --oneline

# Volver al estado anterior (reemplaza <SHA> con el hash correcto)
git reset --hard <SHA>

# O deshacer el último merge
git reset --hard HEAD~1
```

## Verificación Final

Después del merge a main, verifica:

```bash
# 1. Todos los archivos están
ls -la backend/schedule_app/
ls -la frontend/src/components/

# 2. No hay emojis en el código
grep -r "✓\|⚠️\|📊\|🎯" backend/schedule_app/*.py

# 3. El .gitignore está actualizado
cat .gitignore | grep CHANGELOG

# 4. La documentación está presente
ls -la *.md
```
