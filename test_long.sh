#!/bin/bash
# Script de prueba EXTENDIDA para el algoritmo genético optimizado
# Tiempo estimado: 8-12 minutos

cd backend

echo "==================================================="
echo "  PRUEBA EXTENDIDA - Algoritmo Genético Optimizado"
echo "==================================================="
echo ""
echo "Parámetros:"
echo "  - Población: 200 (4x más grande)"
echo "  - Generaciones: 400 (13x más)"
echo "  - Mutation rate: 0.15"
echo "  - Crossover rate: 0.80"
echo "  - Tournament size: 5"
echo ""
echo "Objetivo: Fitness > -1,000,000 (menos de 1,000 violaciones duras)"
echo ""
echo "Iniciando en 3 segundos..."
sleep 3

./venv/bin/python3 manage.py generate_schedule \
  --name "Test Extendido - 200x400" \
  --population 200 \
  --generations 400

echo ""
echo "==================================================="
echo "  ANÁLISIS DEL RESULTADO"
echo "==================================================="
echo ""
echo "Para ver el reporte de instructores sintéticos, ejecuta:"
echo "  ./venv/bin/python3 manage.py show_synthetic_instructors"
echo ""
