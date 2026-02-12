import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add root to sys.path for shared imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore  # noqa: E402
from shared.browser.core.stealth.injector import StealthConfig  # noqa: E402


async def check_site(browser, url, name):
    logger.info(f"🔍 Testing {name}...")
    context = await browser.create_context()
    page = await context.new_page()

    try:
        # Some sites might take longer to load or check
        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait a bit longer for scripts to run
        await asyncio.sleep(5)

        # Save screenshot
        screenshot_path = f"stealth_results/{name.lower().replace(' ', '_')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"📸 Screenshot saved: {screenshot_path}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to test {name}: {e}")
        return False
    finally:
        await context.close()

async def run_ultimate_test():
    # Make sure results dir exists
    results_dir = Path("stealth_results")
    results_dir.mkdir(exist_ok=True)

    # Configure stealth
    stealth = StealthConfig(
        spoof_webgl=True,
        mask_navigator=True,
        canvas_noise=True,
        audio_noise=True
    )

    # Run in non-headless mode for visual if possible,
    # but since this is an agent environment, we use headless for stability
    # unless the user environment supports visual window.
    # Usually, we stick to headless here.
    browser = BrowserCore(headless=True, stealth_config=stealth)

    sites = [
        ("https://bot.sannysoft.com/", "Sannysoft Bot Test"),
        ("https://bot.incolumitas.com/proxy_detect.html", "Incolumitas Proxy Detect"),
        ("https://pixelscan.net/", "Pixelscan Consistency"),
        ("https://abrahamjuliot.github.io/creepjs/", "CreepJS Fingerprint")
    ]

    try:
        await browser.start()

        for url, name in sites:
            await check_site(browser, url, name)

        logger.info("✅ All tests completed! Check the 'stealth_results/' folder for screenshots.")

    except Exception as e:
        logger.error(f"Ultimate test failed: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(run_ultimate_test())
