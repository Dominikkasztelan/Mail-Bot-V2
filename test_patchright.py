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
    
    # Fresh profile dir every time
    user_data_dir = os.path.join(tempfile.gettempdir(), "patchright_test_profile_v2")
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir, ignore_errors=True)
    os.makedirs(user_data_dir, exist_ok=True)
    
    logger.info(f"🎬 Launching persistent context...")
    
    pw = await async_playwright().start()
    
    try:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
            ],
            ignore_default_args=["--enable-automation"],
        )
        logger.info("✅ Persistent context launched!")
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Try Google first to test DNS
        logger.info("Testing DNS with google.com...")
        try:
            await page.goto("https://www.google.com", timeout=10000)
            logger.info("✅ Google loaded - DNS works!")
        except Exception as e:
            logger.error(f"❌ Google failed: {e}")
            logger.info("Trying direct IP navigation...")
        
        # Now try the bot detection page
        logger.info("Navigating to bot detection page...")
        await page.goto("https://deviceandbrowserinfo.com/are_you_a_bot", wait_until="domcontentloaded", timeout=30000)
        logger.info("✅ Bot detection page loaded!")
        logger.info("⏳ Keeping open for 600 seconds...")
        
        await asyncio.sleep(600)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await pw.stop()
        logger.info("👋 Done.")

if __name__ == "__main__":
    asyncio.run(test())
