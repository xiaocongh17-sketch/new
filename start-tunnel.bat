@echo off
if exist "%~dp0cloudflared.exe" (
    cd /d "%~dp0"
    start "AI-Store-Tunnel" /min "%~dp0cloudflared.exe" tunnel run ai-store-copilot
    echo Cloudflare Tunnel started
) else (
    echo cloudflared.exe not found in project root.
    echo Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
)
