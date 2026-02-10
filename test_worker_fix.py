import asyncio
import sys
import os
import shutil
import tempfile
import traceback
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level:<7} | {message}")

ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

async def test():
    from patchright.async_api import async_playwright
    from shared.browser.core.stealth.injector import StealthInjector, StealthConfig
    
    # Fresh profile dir every time
    user_data_dir = os.path.join(tempfile.gettempdir(), "patchright_worker_test")
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir, ignore_errors=True)
    os.makedirs(user_data_dir, exist_ok=True)
    
    logger.info("🎬 Launching persistent context with stealth...")
    
    pw = await async_playwright().start()
    
    try:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--disable-infobars",
            ],
            ignore_default_args=["--enable-automation"],
        )
        logger.info("✅ Persistent context launched!")
        
        # Apply stealth injections
        stealth = StealthInjector(StealthConfig())
        await stealth.apply_stealth(context)
        logger.info("✅ Stealth injections applied!")
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate - try Google first for DNS
        logger.info("🌐 Navigating to Google first...")
        try:
            await page.goto("https://www.google.com", timeout=15000)
            logger.info("✅ Google loaded!")
        except Exception as e:
            logger.warning(f"Google failed: {e}")
        
        # Now try bot detection page
        logger.info("🌐 Navigating to bot detection page...")
        try:
            await page.goto("https://deviceandbrowserinfo.com/are_you_a_bot", wait_until="domcontentloaded", timeout=30000)
            logger.info("✅ Bot detection page loaded!")
        except Exception as e:
            logger.warning(f"⚠️ Auto-nav failed: {e}")
            logger.info("👉 Navigate manually to: https://deviceandbrowserinfo.com/are_you_a_bot")
        
        logger.info("⏳ Keeping open for 300 seconds - check the results...")
        
        await asyncio.sleep(300)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await pw.stop()
        logger.info("👋 Done.")

if __name__ == "__main__":
    asyncio.run(test())
