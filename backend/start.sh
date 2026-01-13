#!/bin/bash
set -e

echo "Setting up storage directories..."
mkdir -p /app/storage/templates /app/storage/uploads /app/storage/generated

# Copy template files if they don't exist on disk (first deploy)
if [ ! -f /app/storage/templates/IRB_v6.docx ]; then
    echo "Copying template files to persistent storage..."
    if [ -d /app/templates_source ]; then
        cp -r /app/templates_source/* /app/storage/templates/ 2>/dev/null || true
    fi
fi

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -m scripts.seed || echo "Seeding complete (or already seeded)"

echo "Starting server..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
