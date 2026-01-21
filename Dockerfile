FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all application files first
COPY . .

# Install Python dependencies (including psycopg2 for alembic sync operations)
RUN pip install --no-cache-dir . psycopg2-binary

# Make startup script executable
RUN chmod +x scripts/start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./scripts/start.sh"]
