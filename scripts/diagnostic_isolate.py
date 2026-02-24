import asyncio
from patchright.async_api import async_playwright
import json

# Minimal StealthConfig mock
class MockConfig:
    languages = ["pl-PL", "pl", "en-US", "en"]
    platform = "Win32"
    vendor = "Google Inc."
    renderer = "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"  # noqa: E501

async def test_part(part_name, script_content):
    print(f"🧪 Testing {part_name}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        
        # Inject just this part
        full_script = f"(function() {{ try {{ {script_content} }} catch(e) {{ console.error(e); }} }})();"
        await context.add_init_script(full_script)
        
        page = await context.new_page()
        try:
            await page.goto("https://app.leonardo.ai/auth/login", timeout=15000)
            print(f"✅ {part_name} works!")
        except Exception as e:
            print(f"❌ {part_name} FAILED: {e}")
        finally:
            await browser.close()

async def run_isolation():
    config = MockConfig()
    
    # 1. Navigator Prototypes
    nav_script = f"""
        const CONFIG = {{
            languages: {json.dumps(config.languages)},
            language: '{config.languages[0]}',
            platform: '{config.platform}',
            userAgent: '{config.user_agent}',
            hardwareConcurrency: 8,
            deviceMemory: 8
        }};
        const overrideProto = (proto, table) => {{
            for (const [prop, value] of Object.entries(table)) {{
                try {{
                    Object.defineProperty(proto, prop, {{
                        get: () => value,
                        enumerable: true,
                        configurable: true
                    }});
                }} catch(e) {{}}
            }}
        }};
        overrideProto(Navigator.prototype, {{
            languages: CONFIG.languages,
            language: CONFIG.language,
            platform: CONFIG.platform,
            vendor: "Google Inc.",
            userAgent: CONFIG.userAgent,
            webdriver: false,
            hardwareConcurrency: CONFIG.hardwareConcurrency,
            deviceMemory: CONFIG.deviceMemory,
            maxTouchPoints: 0
        }});
    """
    await test_part("Navigator", nav_script)

    # 2. Worker Injection (Simplified)
    worker_script = """
        const OriginalWorker = window.Worker;
        window.Worker = function Worker(scriptURL, options) {
            return new OriginalWorker(scriptURL, options);
        };
    """
    await test_part("Simple Worker Override", worker_script)

    # 3. WebGL Spoofing (Most likely to crash)
    webgl_script = """
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            return originalGetContext.apply(this, arguments);
        };
    """
    await test_part("Simple WebGL Hook", webgl_script)

if __name__ == "__main__":
    asyncio.run(run_isolation())
