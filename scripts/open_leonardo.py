import asyncio
import sys
from pathlib import Path

# Add root to sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig

async def open_leonardo():
    print("🎬 Opening Leonardo.ai in HEADED mode...")

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

        url = "https://app.leonardo.ai/auth/login"
        print(f"🌐 Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("✅ Leonardo.ai loaded successfully!")
        except Exception as e:
            print(f"⚠️ Page load warning (proceeding anyway): {e}")

        print("👀 Browser is open. You can now use Leonardo.ai.")
        print("⏳ Script will keep the browser open for 3600 seconds (1 hour).")
        print("Press Ctrl+C in the terminal to close it.")

        # Keep it open
        while True:
            await asyncio.sleep(10)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await browser.stop()
        print("👋 Browser closed.")

if __name__ == "__main__":
    asyncio.run(open_leonardo())
