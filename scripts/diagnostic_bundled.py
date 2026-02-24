import asyncio
from patchright.async_api import async_playwright

async def test_injection():
    print("🎬 Testing injection on bundled Chromium...")
    async with async_playwright() as p:
        # Launch without channel="chrome" to use bundled chromium
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Inject a simple log
        await context.add_init_script("console.log('HELLO FROM INJECTION');")
        
        page = await context.new_page()
        try:
            print("🌐 Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=15000)
            print("✅ google.com loaded with injection on bundled Chromium!")
            
            print("🌐 Navigating to app.leonardo.ai...")
            await page.goto("https://app.leonardo.ai/auth/login", timeout=15000)
            print("✅ app.leonardo.ai loaded with injection on bundled Chromium!")
        except Exception as e:
            print(f"❌ Failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_injection())
