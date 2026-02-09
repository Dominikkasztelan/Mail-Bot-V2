import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add root to sys.path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig

async def open_headed_test():
    logger.info("🎬 Opening Sannysoft in HEADED mode...")
    
    # Use full stealth config
    stealth = StealthConfig(
        spoof_webgl=True,
        mask_navigator=True,
        canvas_noise=True,
        audio_noise=True
    )
    
    # Launch in HEADED mode
    browser = BrowserCore(headless=False, stealth_config=stealth)
    
    try:
        await browser.start()
        context = await browser.create_context()
        page = await context.new_page()
        
        url = "https://bot.sannysoft.com/"
        logger.info(f"🌐 Navigating to {url}...")
        await page.goto(url)
        
        logger.info("👀 Browser is open. You can now inspect the results.")
        logger.info("⏳ Script will keep the browser open for 1000 seconds (or until you terminate it).")
        
        # Keep it open for 1000 seconds (~16.5 minutes)
        await asyncio.sleep(1000)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await browser.stop()
        logger.info("👋 Browser closed.")

if __name__ == "__main__":
    asyncio.run(open_headed_test())
