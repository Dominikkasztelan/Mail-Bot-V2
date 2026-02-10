import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add root to sys.path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore  # noqa: E402
from shared.browser.core.stealth.injector import StealthConfig  # noqa: E402


async def run_test(headless: bool):
    mode = "HEADLESS" if headless else "HEADED"
    logger.info(f"🎬 Starting {mode} test...")

    stealth = StealthConfig()
    browser = BrowserCore(headless=headless, stealth_config=stealth)

    try:
        await browser.start()
        context = await browser.create_context()
        page = await context.new_page()

        url = "https://arh.antoinevastel.com/bots/areyouheadless"
        logger.info(f"🌐 [{mode}] Navigating to {url}...")
        await page.goto(url)

        await asyncio.sleep(5)

        # Take a screenshot to see results
        screenshot_path = f"areyouheadless_{mode.lower()}.png"
        await page.screenshot(path=screenshot_path)
        logger.info(f"📸 [{mode}] Screenshot saved to {screenshot_path}")

        # Try to extract result text
        result = await page.evaluate("() => document.body.innerText")
        logger.info(f"📄 [{mode}] Result summary: {result[:500]}...")

    except Exception as e:
        logger.error(f"❌ [{mode}] Error: {e}")
    finally:
        await browser.stop()

async def main():
    # Run headless first as it's the problematic one
    await run_test(headless=True)
    # Then headed for comparison
    await run_test(headless=False)

if __name__ == "__main__":
    asyncio.run(main())
