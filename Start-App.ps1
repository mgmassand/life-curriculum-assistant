# Life Curriculum Assistant - PowerShell Launcher
# Run with: powershell -ExecutionPolicy Bypass -File Start-App.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Life Curriculum Assistant - Starting..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ScriptDir

# Check if Docker is running
try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start containers
Write-Host "[1/4] Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start containers!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Wait for database
Write-Host "[2/4] Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run migrations
Write-Host "[3/4] Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T app alembic upgrade head 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Retrying migrations..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    docker-compose exec -T app alembic upgrade head
}

# Seed data
Write-Host "[4/4] Seeding database..." -ForegroundColor Yellow
docker-compose exec -T app python -m app.db.seed

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Application is ready!" -ForegroundColor Green
Write-Host "  Open: http://localhost:8000" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Open browser
Start-Process "http://localhost:8000"

Write-Host "Press Enter to close this window (app will keep running)..." -ForegroundColor Gray
Read-Host
