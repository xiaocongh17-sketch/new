@echo off
title AI Store Copilot - Starting Services
echo ============================================
echo   AI Store Copilot - Starting All Services
echo ============================================
echo.

REM Step 1: Wait for Docker Desktop
echo [1/5] Waiting for Docker Desktop...
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto wait_docker
)
echo [1/5] Docker Desktop Ready!

REM Step 2: Start DB & Redis
echo [2/5] Starting DB & Redis...
cd /d "%~dp0docker"
docker compose -p ai-store-copilot up -d db redis
echo [2/5] DB & Redis Started!

REM Step 3: Start Backend (using run.py for Windows async compatibility)
echo [3/5] Starting Backend Server...
cd /d "%~dp0backend"
start "AI-Store-Backend" /min python run.py

REM Wait for backend to start
timeout /t 8 /nobreak >nul

REM Step 4: Start Frontend
echo [4/5] Starting Frontend...
cd /d "%~dp0frontend"
start "AI-Store-Frontend" /min cmd /c "npx next dev --port 3000"

REM Step 5: Start Cloudflare Tunnel (optional, requires cloudflared.exe in project root)
echo [5/5] Starting Cloudflare Tunnel...
if exist "%~dp0cloudflared.exe" (
    start "AI-Store-Tunnel" /min "%~dp0cloudflared.exe" tunnel run ai-store-copilot
) else (
    echo [5/5] cloudflared.exe not found, skipping tunnel.
)

echo.
echo ============================================
echo   All Services Started!
echo   Frontend : http://localhost:3000
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/api/docs
echo ============================================
echo.
pause
