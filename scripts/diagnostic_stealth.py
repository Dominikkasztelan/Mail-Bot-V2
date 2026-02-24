import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from patchright.async_api import async_playwright
from shared.browser.core.stealth.injector import StealthConfig, StealthInjector

async def run_diagnostic():
    print("🎬 Running connection diagnostic with StealthInjector...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        
        # Apply Stealth
        config = StealthConfig()
        injector = StealthInjector(config)
        await injector.apply_stealth(context)
        
        page = await context.new_page()
        try:
            print("🌐 Navigating to app.leonardo.ai...")
            await page.goto("https://app.leonardo.ai/auth/login", timeout=30000)
            print("✅ app.leonardo.ai loaded with stealth!")
        except Exception as e:
            print(f"❌ Failed with stealth: {e}")
            await page.screenshot(path="diag_stealth_fail.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
