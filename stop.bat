@echo off
title Life Curriculum Assistant - Stopping
echo ============================================
echo   Life Curriculum Assistant - Stopping...
echo ============================================
echo.

cd /d "%~dp0"

docker-compose down

echo.
echo Application stopped.
echo.
pause
