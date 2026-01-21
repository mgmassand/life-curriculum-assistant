#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database if needed..."
python -c "
import asyncio
from app.db.seed import seed_database
asyncio.run(seed_database())
" || echo "Seeding skipped or already done"

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
