import asyncio
from playwright.async_api import async_playwright

async def test_standard_playwright():
    print("🎬 Testing injection on STANDARD Playwright...")
    async with async_playwright() as p:
        # Standard playwright Chromium
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Inject a simple log
        await context.add_init_script("console.log('HELLO FROM STANDARD INJECTION');")
        
        page = await context.new_page()
        try:
            print("🌐 Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=15000)
            print("✅ google.com loaded with standard playwright!")
            
            print("🌐 Navigating to app.leonardo.ai...")
            await page.goto("https://app.leonardo.ai/auth/login", timeout=15000)
            print("✅ app.leonardo.ai loaded with standard playwright!")
        except Exception as e:
            print(f"❌ Failed on standard playwright: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_standard_playwright())
