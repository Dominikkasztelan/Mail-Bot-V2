from abc import ABC, abstractmethod
from typing import Any

from playwright.async_api import Page


class AuthProvider(ABC):
    """
    Abstract Base Class for authentication strategies (Email, Google, Microsoft).
    """

    @abstractmethod
    async def login(self, page: Page, credentials: dict[str, str]) -> dict[str, Any]:
        """
        Performs login strategy.
        Returns session data (cookies, tokens, etc).
        """
        pass

    @abstractmethod
    async def is_logged_in(self, page: Page) -> bool:
        """Checks if the current page session is valid."""
        pass
