import pytest
from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig


@pytest.mark.asyncio
async def test_stealth_injection() -> None:
    """
    Verifies that stealth scripts are correctly injected into the page.
    """
    config = StealthConfig(
        spoof_webgl=True,
        mask_navigator=True
    )
    core = BrowserCore(headless=True, stealth_config=config)
    await core.start()

    # Assert core started correctly (tests our type assertions implicitly)
    assert core._browser is not None
    assert core._playwright is not None

    context = await core.create_context()
    page = await context.new_page()

    # Check Navigator Masking
    webdriver = await page.evaluate("navigator.webdriver")
    assert webdriver is None, "navigator.webdriver should be undefined"

    plugins = await page.evaluate("navigator.plugins.length")
    assert plugins == 3, "navigator.plugins should satisfy realistic length"

    # Check WebGL Spoofing
    vendor = await page.evaluate("""
        (() => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl');
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            return gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        })()
    """)
    assert vendor == config.vendor, f"WebGL Vendor should be {config.vendor}"

    await core.stop()
