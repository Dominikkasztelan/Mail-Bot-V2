import asyncio
import random

from loguru import logger
from patchright.async_api import Page


class CookieWarmer:
    """
    Pre-warms browser session by visiting random sites and performing human-like actions.
    Adapted from Bot_mail_creator for async Playwright.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    async def _human_delay(self, min_s: float = 1.0, max_s: float = 3.0) -> None:
        """Random delay to simulate human thinking."""
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def _human_scroll(self) -> None:
        """Simulate human scrolling behavior."""
        for _ in range(random.randint(3, 6)):
            await self.page.mouse.wheel(0, random.randint(300, 700))
            await asyncio.sleep(random.uniform(0.5, 1.5))

    async def warm_via_google(self, target_site: str = "leonardo.ai") -> bool:
        """
        Warm session by searching on Google and clicking through to target.
        Returns True if successful, False otherwise.
        """
        try:
            logger.info("🔥 Warming session via Google...")

            # 1. Visit Google
            await self.page.goto("https://www.google.com", timeout=15000)
            await self._human_delay(2, 3)

            # 2. Handle consent (if present)
            try:
                consent = self.page.locator("button:has-text('Accept all'), button:has-text('Reject all')").first
                await consent.click(timeout=3000)
                await self._human_delay(1, 2)
            except Exception:
                pass

            # 3. Search for target
            search_box = self.page.locator("textarea[name='q'], input[name='q']").first
            await search_box.focus()
            await self.page.keyboard.type(f"{target_site} login", delay=random.randint(80, 150))
            await self._human_delay(0.5, 1.0)
            await self.page.keyboard.press("Enter")

            # 4. Wait for results
            await self.page.wait_for_load_state("domcontentloaded")
            await self._human_delay(1, 2)

            # 5. Scroll through results (human behavior)
            await self._human_scroll()

            logger.info("✅ Session warmed successfully!")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Warming failed, continuing anyway: {e}")
            return False

    async def quick_warm(self) -> None:
        """Quick warming - just visit a neutral site."""
        try:
            sites = ["https://www.wikipedia.org", "https://www.github.com"]
            await self.page.goto(random.choice(sites), timeout=10000)
            await self._human_delay(2, 3)
            await self._human_scroll()
        except Exception:
            pass
