#!/bin/sh
set -e

echo "Waiting for database to be ready..."
until python manage.py migrate --noinput; do
  echo "Database not ready yet, retrying in 2s..."
  sleep 2
done

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3