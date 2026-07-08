"""Run the FastAPI app with Windows-compatible async settings."""
import os
import sys
import asyncio

# CRITICAL: Clear proxy settings so httpx/openai can connect directly
# LightningX VPN sets a system proxy that breaks SSL to DeepSeek API
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)

# CRITICAL: Set SelectorEventLoop BEFORE any imports
# asyncpg + greenlet requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="asyncio",
    )
