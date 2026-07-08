@echo off
title AI Store Copilot - Starting Services
echo ============================================
echo   AI Store Copilot - Starting All Services
echo ============================================
echo.

REM Step 1: Wait for Docker Desktop
echo [1/4] Waiting for Docker Desktop...
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto wait_docker
)
echo [1/4] Docker Desktop Ready!

REM Step 2: Start DB ^& Redis
echo [2/4] Starting DB ^& Redis...
cd /d "E:\AI客服（\docker"
docker compose -p ai-store-copilot up -d db redis
echo [2/4] DB ^& Redis Started!

REM Step 3: Start Backend (using run.py for Windows async compatibility)
echo [3/4] Starting Backend Server...
cd /d "E:\AI客服（\backend"
start "AI-Store-Backend" /min python run.py

REM Wait for backend to start
timeout /t 8 /nobreak >nul

REM Step 4: Start Frontend
echo [4/4] Starting Frontend...
cd /d "E:\AI客服（\frontend"
start "AI-Store-Frontend" /min cmd /c "npx next dev --port 3003"

REM Step 5: Start Tunnel
echo [5/5] Starting Cloudflare Tunnel...
start "AI-Store-Tunnel" /min "E:\AI客服（\cloudflared.exe" tunnel run ai-store-copilot

echo.
echo ============================================
echo   All Services Started!
echo   Frontend : http://localhost:3003
echo   Backend  : http://localhost:8000
echo   Tunnel   : https://katol.top
echo ============================================
echo.
pause
