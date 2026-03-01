import asyncio
from patchright.async_api import async_playwright

async def apply_cdp_stealth(page):
    try:
        print("Page created, attaching CDP stealth...")
        client = await page.context.new_cdp_session(page)
        await client.send("Page.enable")
        await client.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": "console.log('Stealth injected via context listener CDP'); Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
        print("CDP attached to page")
    except Exception as e:
        print(f"Error in CDP injection: {e}")

async def run():
    print("Starting async_playwright with CDP injection via context listener...")
    async with async_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars"
        ]
        
        browser = await p.chromium.launch(
            headless=False, 
            args=args, 
            ignore_default_args=["--enable-automation"]
        )
        context = await browser.new_context()
        
        # Listen for new pages to inject CDP
        context.on("page", apply_cdp_stealth)
        
        page = await context.new_page()
        # Sleep a bit to ensure the event listener runs before goto
        await asyncio.sleep(0.5)
        
        target_url = "https://example.com"
        print(f"Navigating to {target_url} ...")
        
        try:
            await page.goto(target_url, wait_until="load", timeout=15000)
            print("Loaded successfully without DNS breaks!")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
