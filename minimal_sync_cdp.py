from patchright.sync_api import sync_playwright
import time

def run():
    print("Starting sync_playwright with CDP injection...")
    with sync_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--use-gl=angle",
            "--use-angle=gl",
        ]
        
        browser = p.chromium.launch(
            headless=False, 
            args=args, 
            ignore_default_args=["--enable-automation"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        
        # Omijamy add_init_script używając Chrome DevTools Protocol (CDP)
        print("Creating CDP session for page...")
        client = context.new_cdp_session(page)
        
        stealth_js = """
            console.log('Stealth script from CDP attached');
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11, vs_5_0, ps_5_0)';
                return originalGetParameter.call(this, parameter);
            };
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
        
        # Evaluate on every new document (stamps our javascript stealthily)
        client.send("Page.enable")
        client.send("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
        
        target_url = "https://example.com"
        # target_url = "https://bot.sannysoft.com/" # We'll check example.com first
        print(f"Navigating to {target_url} ...")
        
        try:
            page.goto(target_url, wait_until="load", timeout=15000)
            print("Loaded successfully without DNS breaks!")
            time.sleep(3)
            
            # Now let's try the bot page
            print("Trying Sannysoft...")
            page.goto("https://bot.sannysoft.com/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(5)
            page.screenshot(path="cdp_stealth_test.png", full_page=True)
            print("Screenshot saved to cdp_stealth_test.png")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
