"""
E2E test: AreYouHeadless detection check using sync_playwright + CDP stealth.
Uses the same approach as verify_stealth.py to avoid asyncio NotImplementedError
on Windows/Python 3.13.
"""
import sys
import time
from pathlib import Path

from loguru import logger
from patchright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.stealth.injector import StealthConfig, StealthInjector


def inject_cdp_stealth(context, page, injector: StealthInjector) -> None:
    """Inject stealth via CDP — avoids the Patchright/Windows DNS bug."""
    client = context.new_cdp_session(page)
    client.send("Page.enable")
    client.send("Page.addScriptToEvaluateOnNewDocument", {"source": injector._stealth_script})
    try:
        client.send("Emulation.setAutomationOverride", {"enabled": False})
    except Exception:
        pass


def test_areyouheadless():
    """Verify that Patchright with CDP stealth is not detected as headless Chrome."""
    logger.info("🎬 AreYouHeadless test starting...")

    config = StealthConfig()
    injector = StealthInjector(config)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"],
            ignore_default_args=["--enable-automation"],
        )
        context = browser.new_context(
            user_agent=config.user_agent,
            viewport={"width": 1920, "height": 1080},
        )

        try:
            page = context.new_page()
            inject_cdp_stealth(context, page, injector)

            url = "https://arh.antoinevastel.com/bots/areyouheadless"
            logger.info(f"🌐 Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            time.sleep(5)

            # Verify no headless detection
            body_text = page.inner_text("body")
            logger.info(f"Page text: {body_text[:200]}")
            assert "not Chrome headless" in body_text or "not headless" in body_text.lower(), (
                f"Headless was detected! Body: {body_text[:300]}"
            )
            logger.success("✅ Not detected as headless!")

        finally:
            browser.close()
            logger.info("👋 Browser closed.")
