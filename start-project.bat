@echo off
title AI Store Copilot - 启动中
set PROJECT_DIR=%~dp0

echo ============================================
echo  AI Store Copilot - 一键启动
echo ============================================
echo.

:: 1. Verify Docker
echo [1/3] 检查 Docker 容器...
docker ps --format "{{.Names}}" 2>nul | findstr "docker-db-1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo   ! Docker 未运行，请先启动 Docker Desktop
    pause
)
echo   Docker 容器已就绪
echo.

:: 2. Start Backend
echo [2/3] 启动后端 (FastAPI :8000)...
start "Backend" cmd /k "cd /d %PROJECT_DIR%backend && echo   后端启动中... && python run.py"

:: Wait for backend to start
timeout /t 5 /nobreak >nul

:: 3. Start Frontend
echo [3/3] 启动前端 (Next.js :3000)...
start "Frontend" cmd /k "cd /d %PROJECT_DIR%frontend && echo   前端启动中... && npx next dev --port 3000"

echo.
echo ============================================
echo  所有服务启动命令已执行！
echo.
echo  后端：http://localhost:8000
echo  前端：http://localhost:3000
echo  API 文档：http://localhost:8000/api/docs
echo.
echo  如需 Cloudflare Tunnel，请手动运行：
echo    cloudflared.exe tunnel run ai-store-copilot
echo ============================================
echo.
echo  按任意键关闭此窗口...
pause >nul
