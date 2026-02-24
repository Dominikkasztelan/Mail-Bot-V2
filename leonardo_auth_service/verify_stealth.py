import asyncio
import sys
import traceback
from pathlib import Path

# Add project root to path to allow importing 'shared'
# This assumes the script is in leonardo_auth_service/verify_stealth.py
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from loguru import logger  # noqa: E402
from src.config.settings import settings  # noqa: E402
from src.core.browser import LeonardoBrowserFactory  # noqa: E402


async def verify():
    # Configure logger for Windows compatibility
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}", level="INFO", colorize=False, enqueue=True)
    
    logger.info("Starting browser for stealth verification...")
    
    # Force headless=False for visual inspection
    factory = LeonardoBrowserFactory(
        headless=False,
        enable_tor=settings.USE_TOR_IF_AVAILABLE,
        http_proxies=settings.HTTP_PROXIES if settings.HTTP_PROXIES else None
    )

    try:
        await factory.start()
        context = await factory.create_context()
        page = await context.new_page()
        
        target_url = "https://bot.sannysoft.com/"
        logger.info(f"Navigating to {target_url} ...")
        await page.goto(target_url, wait_until="networkidle")
        
        logger.info("Waiting for tests to complete...")
        await page.wait_for_timeout(5000)
        
        # Take screenshot
        screenshot_path = "stealth_result.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.success(f"Screenshot saved to {screenshot_path}")
        
        print("\n" + "="*50)
        print("   BROWSER IS OPEN. INSPECT THE RESULTS.")
        print("   The script will keep running to keep the browser open.")
        print("   Press Ctrl+C to stop.")
        print("="*50 + "\n")
        
        # Keep alive loop
        while True:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.exception(f"Verification failed: {e}")
    finally:
        logger.info("Closing browser...")
        await factory.stop()

if __name__ == "__main__":
    print("Starting verification script...")
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(verify())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
