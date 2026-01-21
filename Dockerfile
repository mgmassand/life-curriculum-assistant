FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml .

# Install Python dependencies (including psycopg2 for alembic sync operations)
RUN pip install --no-cache-dir . psycopg2-binary

# Copy application files
COPY . .

# Fix line endings and make startup script executable
RUN dos2unix scripts/start.sh && chmod +x scripts/start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./scripts/start.sh"]
