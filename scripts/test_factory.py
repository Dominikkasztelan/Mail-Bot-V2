import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig

async def test_factory():
    print("🎬 Testing BrowserCore with Leonardo.ai...")
    stealth = StealthConfig(
        spoof_webgl=True,
        mask_navigator=True,
        canvas_noise=True,
        audio_noise=True
    )
    browser = BrowserCore(headless=True, stealth_config=stealth)
    
    try:
        await browser.start()
        context = await browser.create_context()
        page = await context.new_page()
        
        url = "https://app.leonardo.ai/auth/login"
        print(f"🌐 Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("✅ Page goto finished.")
        except Exception as e:
            print(f"❌ Page goto failed: {e}")
            
        await asyncio.sleep(5)
        await page.screenshot(path="factory_test.png")
        print("📸 Screenshot saved as factory_test.png")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(test_factory())
