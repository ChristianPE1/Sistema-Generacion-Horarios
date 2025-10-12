# Configuración del Algoritmo Genético

Este archivo contiene guías de configuración para optimizar el algoritmo genético según diferentes escenarios.

## Configuraciones Predefinidas

### 🚀 Configuración Rápida (Testing/Development)
Para pruebas rápidas durante desarrollo:
```json
{
  "population_size": 50,
  "generations": 100,
  "mutation_rate": 0.1,
  "crossover_rate": 0.8,
  "elitism_size": 3,
  "tournament_size": 3
}
```
- **Tiempo estimado**: 30-60 segundos
- **Calidad**: Moderada
- **Uso**: Testing inicial, debugging

### ⚡ Configuración Estándar (Producción Normal)
Para uso regular con buenos resultados:
```json
{
  "population_size": 100,
  "generations": 200,
  "mutation_rate": 0.1,
  "crossover_rate": 0.8,
  "elitism_size": 5,
  "tournament_size": 5
}
```
- **Tiempo estimado**: 2-3 minutos
- **Calidad**: Buena
- **Uso**: Generación de horarios regulares

### 🎯 Configuración Optimizada (Alta Calidad)
Para obtener los mejores resultados:
```json
{
  "population_size": 150,
  "generations": 300,
  "mutation_rate": 0.15,
  "crossover_rate": 0.85,
  "elitism_size": 8,
  "tournament_size": 7
}
```
- **Tiempo estimado**: 5-8 minutos
- **Calidad**: Excelente
- **Uso**: Horarios finales de producción

### 🔬 Configuración Experimental (Máxima Exploración)
Para explorar el espacio de soluciones ampliamente:
```json
{
  "population_size": 200,
  "generations": 500,
  "mutation_rate": 0.20,
  "crossover_rate": 0.9,
  "elitism_size": 10,
  "tournament_size": 8
}
```
- **Tiempo estimado**: 10-15 minutos
- **Calidad**: Muy alta
- **Uso**: Problemas complejos o con muchas restricciones

## Guía de Ajuste de Parámetros

### Population Size (Tamaño de Población)
- **Bajo (50-80)**: Convergencia rápida, puede quedar atrapado en óptimos locales
- **Medio (100-150)**: Balance entre velocidad y calidad
- **Alto (200+)**: Mayor exploración, mejor calidad, más tiempo

### Generations (Generaciones)
- **Bajo (50-100)**: Soluciones rápidas pero posiblemente subóptimas
- **Medio (200-300)**: Tiempo suficiente para convergencia
- **Alto (500+)**: Garantiza exploración exhaustiva

### Mutation Rate (Tasa de Mutación)
- **Bajo (0.05-0.08)**: Convergencia rápida, menos exploración
- **Medio (0.10-0.15)**: Balance entre exploración y explotación
- **Alto (0.20-0.30)**: Mucha exploración, puede ser inestable

### Crossover Rate (Tasa de Cruce)
- **Bajo (0.6-0.7)**: Más mutación que cruce
- **Medio (0.8-0.85)**: Balance estándar
- **Alto (0.9-0.95)**: Favorece combinación de soluciones

### Elitism Size (Tamaño Élite)
- **Regla general**: 3-10% del tamaño de población
- Asegura que las mejores soluciones no se pierdan

### Tournament Size (Tamaño Torneo)
- **Bajo (3-5)**: Menor presión selectiva
- **Medio (5-7)**: Balance
- **Alto (8-10)**: Mayor presión, convergencia rápida

## Estrategias de Optimización

### Problema: Convergencia Prematura
**Síntomas**: Fitness se estanca rápidamente
**Solución**:
- Aumentar `mutation_rate` (0.15-0.20)
- Aumentar `population_size` (150-200)
- Reducir `tournament_size` (3-5)

### Problema: No Cumple Restricciones Duras
**Síntomas**: Muchos conflictos de instructores/aulas
**Solución**:
- Aumentar `generations` (300-500)
- Aumentar `population_size` (150+)
- Verificar que hay suficientes aulas y slots disponibles

### Problema: Ejecución Muy Lenta
**Síntomas**: Tarda más de 10 minutos
**Solución**:
- Reducir `population_size` (50-80)
- Reducir `generations` (100-150)
- Optimizar las restricciones en el código

### Problema: Soluciones de Baja Calidad
**Síntomas**: Fitness bajo, muchas violaciones blandas
**Solución**:
- Aumentar `generations` (300-500)
- Aumentar `elitism_size` (8-10)
- Aumentar `crossover_rate` (0.85-0.9)

## Ejemplos de Uso por Tamaño

### Pequeño (< 50 clases)
```bash
python manage.py generate_schedule \
  --population 50 \
  --generations 150 \
  --mutation-rate 0.1
```

### Mediano (50-150 clases)
```bash
python manage.py generate_schedule \
  --population 100 \
  --generations 250 \
  --mutation-rate 0.12
```

### Grande (150-300 clases)
```bash
python manage.py generate_schedule \
  --population 150 \
  --generations 400 \
  --mutation-rate 0.15
```

### Muy Grande (300+ clases)
```bash
python manage.py generate_schedule \
  --population 200 \
  --generations 500 \
  --mutation-rate 0.18 \
  --elitism 10
```

## Métricas de Calidad

### Fitness Score
- **> 99,000**: Excelente (casi sin conflictos)
- **95,000 - 99,000**: Muy bueno (pocos conflictos)
- **90,000 - 95,000**: Bueno (conflictos menores)
- **< 90,000**: Mejorable (revisar restricciones)

### Violaciones Aceptables
- **Restricciones Duras**: 0 (obligatorio)
- **Restricciones Blandas**: < 50 (preferible)

## Análisis de Resultados

### Comando para Ver Estadísticas
```bash
python manage.py shell
>>> from schedule_app.models import Schedule
>>> s = Schedule.objects.latest('created_at')
>>> print(f"Fitness: {s.fitness_score}")
>>> print(f"Descripción:\n{s.description}")
```

### API para Análisis
```bash
# Ver resumen
curl http://localhost:8000/api/schedules/1/summary/ | jq

# Ver conflictos detallados (requiere implementar endpoint)
curl http://localhost:8000/api/schedules/1/conflicts/
```

## Tips Avanzados

1. **Ejecución en Batch**: Genera múltiples horarios y elige el mejor
   ```bash
   for i in {1..5}; do
     python manage.py generate_schedule --name "Test $i"
   done
   ```

2. **Logging Detallado**: Modifica `genetic_algorithm.py` para verbose mode
   ```python
   if (generation + 1) % 1 == 0:  # Cambiar de 10 a 1
       print(f"Generación {generation + 1}...")
   ```

3. **Ajuste Dinámico**: Implementar adaptive mutation rate
   ```python
   # En genetic_algorithm.py
   if generation > self.generations // 2:
       self.mutation_rate *= 1.1  # Aumentar en segunda mitad
   ```

4. **Paralelización**: Usar multiprocessing para evaluación de fitness
   ```python
   from multiprocessing import Pool
   with Pool() as pool:
       fitness_scores = pool.map(validator.evaluate, population)
   ```

## Troubleshooting

### Error: "No hay clases o aulas disponibles"
- Verificar que los datos están importados
- Ejecutar: `python manage.py shell -c "from schedule_app.models import Class; print(Class.objects.count())"`

### Error: "Module not found: numpy"
- Instalar: `pip install numpy>=1.24.0`

### Fitness no mejora después de 100 generaciones
- Aumentar diversidad: mutation_rate = 0.2
- Reiniciar con nueva población aleatoria

### Muchos conflictos de instructores
- Verificar que hay suficientes slots de tiempo disponibles
- Revisar datos de ClassInstructor en la BD
