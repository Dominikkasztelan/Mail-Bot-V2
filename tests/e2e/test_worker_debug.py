import asyncio
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

# Fix sys.path BEFORE imports
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from patchright.async_api import async_playwright

from shared.browser.core.stealth.injector import StealthConfig, StealthInjector

logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level:<7} | {message}")

async def test():
    user_data_dir = Path(tempfile.gettempdir()) / "patchright_worker_debug"
    if user_data_dir.exists():
        shutil.rmtree(user_data_dir, ignore_errors=True)
    user_data_dir.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()

    try:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            ignore_default_args=["--enable-automation"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"  # noqa: E501
        )

        output_file = ROOT_DIR / "output" / "e2e_result.txt"

        # Monitor console for all pages and workers
        def handle_console(msg):
            logger.info(f"PAGE LOG: {msg.text}")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"PAGE LOG: {msg.text}\n")

        def handle_worker(worker):
            logger.info(f"👷 Worker created: {worker.url}")
            def worker_log(msg):
                logger.info(f"WORKER LOG: {msg.text}")
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(f"WORKER LOG: {msg.text}\n")
            worker.on("console", worker_log)

        context.on("page", lambda p: p.on("console", handle_console))
        context.on("worker", handle_worker)

        # Clear file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("--- TEST START ---\n")

        await context.add_init_script("console.log('[STEALTH DEBUG] MINIMAL INIT SCRIPT RUNNING')")

        stealth = StealthInjector(StealthConfig(
            mask_navigator=True,
            spoof_webgl=True,
            canvas_noise=False, # Disable noise for this test
            audio_noise=False
        ))
        await stealth.apply_stealth(context)
        logger.info("✅ Stealth applied")

        page = context.pages[0] if context.pages else await context.new_page()
        page.on("console", handle_console)

        # Load debug HTML
        debug_html_path = ROOT_DIR / "tests" / "assets" / "debug_worker.html"
        await page.goto(debug_html_path.as_uri())

        await asyncio.sleep(10)

        # Check output
        is_consistent = await page.evaluate("window.isConsistent")
        if is_consistent:
             logger.success("✅ Worker consistency PASSED!")
             with open(output_file, "a", encoding="utf-8") as f:
                 f.write("✅ Worker consistency PASSED!\n")
        else:
             logger.error("❌ Worker consistency FAILED!")
             with open(output_file, "a", encoding="utf-8") as f:
                 f.write("❌ Worker consistency FAILED!\n")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await pw.stop()

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(str(e))
            import traceback
            f.write(traceback.format_exc())
        print(f"CRITICAL ERROR: {e}")
