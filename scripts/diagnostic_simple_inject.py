import asyncio
from patchright.async_api import async_playwright

async def test_injection():
    print("🎬 Testing injection on google.com...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        
        # Inject a simple log
        await context.add_init_script("console.log('HELLO FROM INJECTION');")
        
        page = await context.new_page()
        try:
            print("🌐 Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=15000)
            print("✅ google.com loaded with injection!")
        except Exception as e:
            print(f"❌ Failed on google.com: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_injection())
