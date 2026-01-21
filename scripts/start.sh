#!/bin/sh
set -e

echo "=== Starting Life Curriculum Assistant ==="

# Debug: Show database URL format (masked)
echo "Database URL format check..."
python -c "
from app.config import get_settings
settings = get_settings()
url = settings.database_url
# Mask password for logging
if '@' in url:
    prefix = url.split('@')[0]
    if ':' in prefix:
        parts = prefix.rsplit(':', 1)
        masked = parts[0] + ':****@' + url.split('@')[1]
    else:
        masked = url
else:
    masked = url
print(f'DB URL starts with: {url[:20]}...')
"

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
