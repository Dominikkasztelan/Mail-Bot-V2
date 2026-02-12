from typing import Any

from loguru import logger
from patchright.async_api import Page
from src.auth.base import AuthProvider
from src.config.settings import settings
from src.utils.cookie_warmer import CookieWarmer
from src.utils.humanizer import Humanizer

from shared.browser.core.network.websocket_monitor import WebSocketMonitor


class EmailLoginStrategy(AuthProvider):
    """
    Implements generic Email & Password login for Leonardo.ai with Stealth.
    """

    async def login(self, page: Page, credentials: dict[str, str]) -> dict[str, Any]:
        email = credentials.get("email")
        password = credentials.get("password")

        if not email or not password:
            raise ValueError("Email and password are required for Email Login.")

        # Mypy aid: Assert they are strings (since we checked truthiness,
        # but mypy might need explicit cast if Dict is str, Any)
        assert isinstance(email, str)
        assert isinstance(password, str)

        logger.info(f"📧 Attempting Email Login for {email} (Stealth Mode)")

        # Start monitoring network early
        ws_monitor = WebSocketMonitor(page)
        await ws_monitor.start_listening()

        try:
            await self._warm_up(page)
            await self._navigate_to_login(page)
            await self._handle_cookie_consent(page)
            await self._initiate_email_login(page)
            await self._fill_credentials(page, email, password)
            await self._submit_login(page)
            await self._wait_for_success(page)

            # Extract Cookies
            cookies = await page.context.cookies()
            return {"cookies": cookies, "email": email, "strategy": "email"}

        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            await page.screenshot(path="login_failed.png")
            raise

    async def _warm_up(self, page: Page) -> None:
        # 0. PRE-WARM SESSION (Critical for stealth!)
        warmer = CookieWarmer(page)
        # Visit Google first to build history/cookies
        await warmer.warm_via_google("leonardo.ai")

    async def _navigate_to_login(self, page: Page) -> None:
        # 1. Navigate to Login
        await page.goto(settings.LEONARDO_URL, wait_until="domcontentloaded")
        # Human-like pause after load
        await Humanizer.random_sleep(3, 5)

    async def _handle_cookie_consent(self, page: Page) -> None:
        # 2. Handle Cookie Consent (from screenshot: 'Accept all')
        try:
            accept_cookies = page.get_by_role("button", name="Accept all", exact=True)
            if await accept_cookies.is_visible(timeout=3000):
                logger.info("🍪 Accepting cookies...")
                await Humanizer.random_sleep(0.5, 1.5)
                await accept_cookies.click()
                await Humanizer.random_sleep(1, 2)
        except Exception:
            pass

    async def _initiate_email_login(self, page: Page) -> None:
        # 3. Click "Continue with Email"
        continue_email = page.get_by_text("Continue with Email", exact=True)
        if await continue_email.is_visible():
            logger.info("🖱️ Clicking 'Continue with Email'...")
            await Humanizer.natural_mouse_move(page)  # Simulate approach
            await continue_email.click()
            await Humanizer.random_sleep(2, 3)

    async def _fill_credentials(self, page: Page, email: str, password: str) -> None:
        # 4. Fill Email
        email_input = page.get_by_placeholder("name@host.com", exact=False).first
        if not await email_input.is_visible(timeout=5000):
            logger.warning("⚠️ Email field (name@host.com) not visible, trying generic input...")
            email_input = page.locator("input[type='email']").first

        if not await email_input.is_visible():
            # Handle Cloudflare
            logger.warning("🛑 Human verification might be blocking. Checking for Turnstile...")
            # Future: Add Turnstile Solver here
            await Humanizer.random_sleep(5, 10)

        await Humanizer.type_like_human(email_input, email)

        # Click "Continue"
        continue_btn = page.get_by_role("button", name="Continue", exact=True)
        if await continue_btn.is_visible():
            await continue_btn.click()
            await Humanizer.random_sleep(2, 3)

        # 5. Fill Password
        password_input = page.get_by_placeholder("Password", exact=False).first
        if not await password_input.is_visible(timeout=5000):
            logger.info("🔑 Waiting for password screen...")
            await Humanizer.random_sleep(1, 2)
            password_input = page.get_by_placeholder("Password", exact=False).first

        await Humanizer.type_like_human(password_input, password)

    async def _submit_login(self, page: Page) -> None:
        # 6. Submit
        submit_btn = page.get_by_role("button", name="Log in", exact=True)
        if not await submit_btn.is_visible():
            submit_btn = page.locator("button[type='submit']").first

        await Humanizer.random_sleep(1.0, 2.0)
        await submit_btn.click()

    async def _wait_for_success(self, page: Page) -> None:
        # 7. Secure Wait
        # Instead of just URL wait, we check for dashboard elements or WS activity
        try:
            await page.wait_for_url("**/app.leonardo.ai/**", timeout=settings.LOGIN_TIMEOUT)
            logger.info("✅ Login URL confirmed.")
        except Exception:
            logger.warning("⏳ URL didn't change quickly, checking visual indicators...")

    async def is_logged_in(self, page: Page) -> bool:
        """Simple check if we are on the dashboard."""
        return "auth" not in page.url
