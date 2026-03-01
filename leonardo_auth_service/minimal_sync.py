from patchright.sync_api import sync_playwright
import time
from loguru import logger
import traceback

def run():
    logger.info("Starting sync Playwright verification with injected STEALTH...")
    with sync_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--use-gl=angle",
            "--use-angle=gl",
        ]
        
        # Ominięcie błędów DNS
        browser = p.chromium.launch(
            headless=False, 
            args=args, 
            ignore_default_args=["--enable-automation"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL",
            timezone_id="Europe/Warsaw"
        )
        
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
        target_url = "https://arh.antoinevastel.com/bots/areyouheadless"
        
        try:
            logger.info(f"Navigating to {target_url} ...")
            # We don't wait for networkidle because DNS is failing in Python, but might work for the user manually
            page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
            
            logger.info("Waiting 7 seconds for tests to complete...")
            time.sleep(7)
            
            screenshot_path = "stealth_result_sync.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.success(f"Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            traceback.print_exc()
            
        print("\n" + "="*50)
        print("   BROWSER IS OPEN. INSPECT THE RESULTS.")
        print("   The script will keep running to keep the browser open.")
        print("   Press Ctrl+C to stop in the terminal.")
        print("="*50 + "\n")
        
        # Keep the browser open indefinitely for user inspection
        while True:
            time.sleep(1)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nZakończono przez użytkownika.")
