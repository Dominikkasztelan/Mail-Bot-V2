#!/usr/bin/env python3
"""
Startup script for Leonardo Auth Service.
Fixes Windows asyncio subprocess issues by setting event loop policy BEFORE uvicorn starts.
"""
import asyncio
import sys

# CRITICAL: Set event loop policy BEFORE any imports that use asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("✅ Windows SelectorEventLoop policy set")

import uvicorn
from src.config.settings import settings

if __name__ == "__main__":
    print("🚀 Starting Leonardo Auth Service...")
    print(f"   Host: {settings.API_HOST}:{settings.API_PORT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Headless: {settings.HEADLESS}")

    # On Windows, force reload=False due to subprocess limitations
    use_reload = settings.DEBUG and sys.platform != "win32"
    if sys.platform == "win32" and settings.DEBUG:
        print("⚠️  Auto-reload disabled on Windows (subprocess limitation)")

    print("-" * 50)

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=use_reload,
        log_level="info"
    )
