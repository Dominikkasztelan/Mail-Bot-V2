
import pytest
from src.core.browser import browser_factory


@pytest.mark.asyncio
async def test_leonardo_login_flow_visual() -> None:
    from src.auth.email_login import EmailLoginStrategy

    print("\n[STEP 1] Initializing Browser Factory...")
    await browser_factory.start()

    print("[STEP 2] Creating Browser Context...")
    context = await browser_factory.create_context()
    page = await context.new_page()

    try:
        strategy = EmailLoginStrategy()
        # We use dummy credentials just to test selectors/flow
        print("[STEP 3-7] Running EmailLoginStrategy.login flow...")
        # Note: This will likely fail on wait_for_url if credentials are fake
        # but we want to see it reach the password field.
        try:
            await strategy.login(page, {"email": "test@example.com", "password": "password123"})
        except Exception as e:
            print(f"  -> Flow stopped at: {e}")

        print("📸 Final state captured in test_final_state.png")
        await page.screenshot(path="test_final_state.png")

        # Check if we at least reached the password stage or were blocked
        url = page.url
        print(f"📍 Final URL: {url}")

    finally:
        print("[CLEANUP] Closing browser...")
        await context.close()
        await browser_factory.stop()
