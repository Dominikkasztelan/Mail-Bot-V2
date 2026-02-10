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

async def test_browserinfo():
    logger.info("🎬 Opening Browser Info Bot Test...")
    
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
        
        url = "https://deviceandbrowserinfo.com/are_you_a_bot"
        logger.info(f"🌐 Navigating to {url}...")
        await page.goto(url)
        
        logger.info("👀 Browser Info Bot Test loaded.")
        logger.info("⏳ Browser will stay open for 1000 seconds (or until you terminate it).")
        logger.info("💡 Check if it detects automation or bot behavior.")
        
        # Keep it open for a long time
        await asyncio.sleep(1000)
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await browser.stop()
        logger.info("👋 Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_browserinfo())
