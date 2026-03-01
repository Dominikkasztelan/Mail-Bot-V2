from playwright.sync_api import sync_playwright
import time

def run():
    print("Starting sync_playwright (STANDARD) with empty init script...")
    with sync_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars"
        ]
        
        browser = p.chromium.launch(
            headless=False, 
            args=args, 
            ignore_default_args=["--enable-automation"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        print("Adding empty init script...")
        context.add_init_script("console.log('init');")
        
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
