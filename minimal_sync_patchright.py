from patchright.sync_api import sync_playwright
import time

def run():
    print("Starting vanilla sync_playwright (patchright)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
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
