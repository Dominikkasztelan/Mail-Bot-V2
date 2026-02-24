import asyncio
from patchright.async_api import async_playwright

async def run_diagnostic():
    print("🎬 Running connection diagnostic...")
    async with async_playwright() as p:
        # Launch without any special args first
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=30000)
            print("✅ google.com loaded!")
            
            print("🌐 Navigating to app.leonardo.ai...")
            await page.goto("https://app.leonardo.ai/auth/login", timeout=30000)
            print("✅ app.leonardo.ai loaded!")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            # Take a screenshot of the error
            await page.screenshot(path="diagnostic_error.png")
            print("📸 Error screenshot saved as diagnostic_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
