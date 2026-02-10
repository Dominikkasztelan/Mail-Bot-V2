import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from playwright.async_api import async_playwright

from shared.browser.core.stealth.injector import StealthConfig, StealthInjector


async def main():
    # Setup output directory
    output_dir = ROOT_DIR / "output" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Launch in HEADLESS mode with FACTORY settings
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--password-store=basic",
            "--use-gl=angle",
            "--use-angle=gl",
            "--hide-scrollbars",
            "--mute-audio",
            "--excludeSwitches=enable-automation",
            "--disable-extensions"
        ]

        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=args,
            ignore_default_args=["--enable-automation"]
        )

        # Create context with explicit User-Agent AND Timezone (matching factory)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",  # noqa: E501
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL",
            timezone_id="Europe/Warsaw"
        )

        # Apply Stealth
        stealth = StealthInjector(StealthConfig())
        await stealth.apply_stealth(context)

        print("✅ Stealth active. Starting screenshot run...")

        sites = [
            ("sannysoft", "https://bot.sannysoft.com"),
            ("browserleaks_gl", "https://browserleaks.com/webgl"),
            ("iphey", "https://iphey.com"),
            ("creepjs", "https://abrahamjuliot.github.io/creepjs/"),
            ("amiunique", "https://amiunique.org/fingerprint"),
            ("pixelscan", "https://pixelscan.net"),
            ("areyouheadless", "https://arh.antoinevastel.com/bots/areyouheadless")
        ]

        page = await context.new_page()

        for name, url in sites:
            print(f"📸 Visiting {name} ({url})...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # Small delay for dynamic checks
                await asyncio.sleep(5)

                screenshot_path = output_dir / f"{name}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"   Saved to {screenshot_path}")
            except Exception as e:
                print(f"   ❌ Error visiting {url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
