import asyncio
import random

from playwright.async_api import Locator, Page


class Humanizer:
    """
    Utilities to simulate human behavior (typing, mouse movement, delays).
    """

    @staticmethod
    async def type_like_human(locator: Locator, text: str, min_delay: int = 50, max_delay: int = 150) -> None:
        """
        Types text with variable delays between keystrokes.
        """
        await locator.focus()
        for char in text:
            delay = random.randint(min_delay, max_delay)
            await locator.type(char, delay=delay)

            # Occasionally pause longer (simulating thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.1, 0.4))

    @staticmethod
    async def random_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Sleeps for a random duration."""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    @staticmethod
    async def natural_mouse_move(page: Page) -> None:
        """Simulates random mouse movements (simple version)."""
        # Complex Bezier curves would go here for advanced stealth
        viewport = page.viewport_size
        width = viewport["width"] if viewport else 1920
        height = viewport["height"] if viewport else 1080

        for _ in range(random.randint(2, 5)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            await page.mouse.move(x, y, steps=random.randint(5, 20))
            await asyncio.sleep(random.uniform(0.05, 0.2))
