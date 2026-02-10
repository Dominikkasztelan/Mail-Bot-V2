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
    
    user_data_dir = os.path.join(tempfile.gettempdir(), "patchright_worker_debug")
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir, ignore_errors=True)
    os.makedirs(user_data_dir, exist_ok=True)
    
    pw = await async_playwright().start()
    
    try:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            ignore_default_args=["--enable-automation"],
        )
        
        stealth = StealthInjector(StealthConfig(
            mask_navigator=True,
            spoof_webgl=True,
            canvas_noise=False, # Disable noise for this test
            audio_noise=False
        ))
        await stealth.apply_stealth(context)
        logger.info("✅ Stealth applied")
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Load debug HTML
        with open("debug_worker.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        await page.set_content(html_content)
        
        # Wait for result
        logger.info("Waiting for consistency check...")
        
        # Monitor console
        page.on("console", lambda msg: logger.info(f"PAGE LOG: {msg.text}"))
        
        await asyncio.sleep(5)
        
        # Check output
        is_consistent = await page.evaluate("window.isConsistent")
        if is_consistent:
             logger.success("✅ Worker consistency PASSED!")
        else:
             logger.error("❌ Worker consistency FAILED!")

        # Keep open for inspection
        await asyncio.sleep(600)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(test())
