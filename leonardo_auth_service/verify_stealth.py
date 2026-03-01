"""
Stealth verification script for Leonardo Auth Service.

Uses patchright sync_playwright + CDP injection to:
1. Bypass net::ERR_NAME_NOT_RESOLVED (caused by add_init_script in Patchright/Windows/Python 3.13)
2. Bypass asyncio.NotImplementedError (caused by ProactorEventLoop + subprocesses on Windows)

The sync API uses greenlets internally — no asyncio subprocesses, no loop conflicts.
"""
import sys
import time
import traceback
from pathlib import Path

from loguru import logger
from patchright.sync_api import BrowserContext, Page, sync_playwright

# Add project root to path to allow importing 'shared'
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from shared.browser.core.stealth.injector import StealthConfig, StealthInjector


def create_cdp_stealth_context(playwright, headless: bool = False) -> tuple:
    """Launch Patchright browser + context with full CDP stealth injection."""
    config = StealthConfig()
    injector = StealthInjector(config)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-first-run",
        "--password-store=basic",
        "--use-gl=angle",
        "--use-angle=gl",
    ]

    browser = playwright.chromium.launch(
        headless=headless,
        args=args,
        ignore_default_args=["--enable-automation"],
    )

    context = browser.new_context(
        user_agent=config.user_agent,
        viewport={"width": 1920, "height": 1080},
        locale="pl-PL",
        timezone_id="Europe/Warsaw",
    )

    return browser, context, injector


def inject_cdp_stealth(context: BrowserContext, page: Page, injector: StealthInjector) -> None:
    """Inject stealth script + remove native webdriver flag via CDP."""
    client = context.new_cdp_session(page)
    client.send("Page.enable")

    # JS stealth payload (navigator, WebGL, canvas noise, workers, chrome obj)
    client.send("Page.addScriptToEvaluateOnNewDocument", {
        "source": injector._stealth_script
    })

    # Kill the native C++ webdriver flag that deep scanners (fp-collect) read directly
    try:
        client.send("Emulation.setAutomationOverride", {"enabled": False})
    except Exception:
        pass

    logger.debug("✅ CDP stealth injected into page")


def verify():
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time} {level} {message}",
        level="INFO",
        colorize=False,
        enqueue=False
    )

    logger.info("🚀 Starting stealth verification (sync mode)...")

    with sync_playwright() as p:
        browser, context, injector = create_cdp_stealth_context(p, headless=False)

        # All major anti-bot test sites
        test_sites = [
            ("sannysoft",    "https://bot.sannysoft.com/",                         "domcontentloaded", 7),
            ("headless",     "https://arh.antoinevastel.com/bots/areyouheadless",  "domcontentloaded", 5),
            ("incolumitas",  "https://bot.incolumitas.com/",                       "domcontentloaded", 8),
            ("creepjs",      "https://abrahamjuliot.github.io/creepjs/",           "domcontentloaded", 10),
            ("deviceinfo",   "https://www.deviceinfo.me/",                         "domcontentloaded", 5),
        ]

        try:
            page = context.new_page()
            inject_cdp_stealth(context, page, injector)

            for name, url, wait_until, sleep_s in test_sites:
                logger.info(f"🌐 Navigating to [{name}] {url} ...")
                try:
                    page.goto(url, wait_until=wait_until, timeout=20000)
                    logger.info(f"⏱  Waiting {sleep_s}s for [{name}] tests to render...")
                    time.sleep(sleep_s)

                    screenshot_path = f"stealth_result_{name}.png"
                    page.screenshot(path=screenshot_path, full_page=True)
                    logger.success(f"✅ Screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.error(f"❌ [{name}] failed: {e}")

        finally:
            logger.info("Closing browser...")
            browser.close()
            logger.info("🛑 Browser stopped.")


if __name__ == "__main__":
    verify()
