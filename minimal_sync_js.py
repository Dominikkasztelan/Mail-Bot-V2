from patchright.sync_api import sync_playwright
import time

def run():
    print("Starting sync_playwright with scripts...")
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
        
        print("Adding init scripts...")
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        stealth_js = """
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11, vs_5_0, ps_5_0)';
                return originalGetParameter.call(this, parameter);
            };
        """
        context.add_init_script(stealth_js)
        
        page = context.new_page()
        
        target_url = "https://example.com"
        print(f"Navigating to {target_url} ...")
        
        try:
            page.goto(target_url, wait_until="load", timeout=15000)
            print("Loaded successfully!")
            time.sleep(3)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
