#!/bin/bash
set -e

if [ "$USE_POSTGRESQL" = "true" ]; then
    echo "Esperando a PostgreSQL..."
    while ! pg_isready -h ${POSTGRES_HOST:-db} -p ${POSTGRES_PORT:-5432} > /dev/null 2>&1; do
        sleep 1
    done
fi

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Creando superusuario..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

echo "Aplicación lista"

exec "$@"
