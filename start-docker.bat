@echo off
cd /d "E:\AI客服（\docker"

:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo Waiting for Docker Desktop...
    timeout /t 5 /nobreak >nul
    goto wait_docker
)

docker compose -p ai-store-copilot up -d db redis
echo DB & Redis started
