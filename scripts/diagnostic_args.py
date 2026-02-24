import asyncio
from patchright.async_api import async_playwright

async def run_diagnostic():
    print("🎬 Running connection diagnostic with BrowserCore args...")
    async with async_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--password-store=basic",
            "--use-gl=angle",
            "--use-angle=gl",
            "--excludeSwitches=enable-automation",
            "--disable-extensions"
        ]
        
        browser = await p.chromium.launch(
            headless=False, 
            channel="chrome", 
            args=args,
            ignore_default_args=["--enable-automation"]
        )
        
        # Test 1: Simple Context
        print("🧪 Test 1: Simple context...")
        context1 = await browser.new_context()
        page1 = await context1.new_page()
        try:
            await page1.goto("https://app.leonardo.ai/auth/login", timeout=20000)
            print("✅ Test 1 success!")
        except Exception as e:
            print(f"❌ Test 1 failed: {e}")
            await page1.screenshot(path="diag_test1_fail.png")

        # Test 2: Context with Locale/Timezone
        print("🧪 Test 2: Context with locale/timezone...")
        context2 = await browser.new_context(
            locale="pl-PL",
            timezone_id="Europe/Warsaw",
            viewport={"width": 1920, "height": 1080}
        )
        page2 = await context2.new_page()
        try:
            await page2.goto("https://app.leonardo.ai/auth/login", timeout=20000)
            print("✅ Test 2 success!")
        except Exception as e:
            print(f"❌ Test 2 failed: {e}")
            await page2.screenshot(path="diag_test2_fail.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
