@echo off
cd /d "E:\AI客服（\backend"
start "AI-Store-Backend" /min "E:\AI客服（\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo Backend started at http://localhost:8000
