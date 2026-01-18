@echo off
title Life Curriculum Assistant
echo ============================================
echo   Life Curriculum Assistant - Starting...
echo ============================================
echo.

cd /d "%~dp0"

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Starting Docker containers...
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    pause
    exit /b 1
)

:: Wait for database to be ready
echo [2/4] Waiting for database to be ready...
timeout /t 5 /nobreak >nul

:: Run migrations
echo [3/4] Running database migrations...
docker-compose exec -T app alembic upgrade head 2>nul
if errorlevel 1 (
    echo [INFO] Migrations may have already been applied or database is still starting...
    timeout /t 3 /nobreak >nul
    docker-compose exec -T app alembic upgrade head
)

:: Seed data (will skip if already seeded)
echo [4/4] Seeding database...
docker-compose exec -T app python -m app.db.seed

echo.
echo ============================================
echo   Application is ready!
echo   Open: http://localhost:8000
echo ============================================
echo.
echo Press any key to open in browser...
pause >nul

start http://localhost:8000
