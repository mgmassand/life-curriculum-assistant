#!/bin/sh
set -e

echo "=== Starting Life Curriculum Assistant ==="

# Wait for database to be ready (Render PostgreSQL may take a moment)
echo "Waiting for database..."
sleep 5

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head || {
    echo "Migration failed, retrying in 10 seconds..."
    sleep 10
    python -m alembic upgrade head
}

echo "Migrations complete!"

# Seed database (optional, won't fail if already seeded)
echo "Checking database seed..."
python -c "
import asyncio
from app.db.seed import seed_database
try:
    asyncio.run(seed_database())
    print('Seeding complete!')
except Exception as e:
    print(f'Seeding skipped: {e}')
"

# Start the application
echo "Starting uvicorn server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
