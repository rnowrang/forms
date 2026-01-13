#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
