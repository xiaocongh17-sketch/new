@echo off
cd /d "E:\AI客服（"
start "AI-Store-Tunnel" /min "E:\AI客服（\cloudflared.exe" tunnel run ai-store-copilot
echo Cloudflare Tunnel started
