"""
Leonardo-specific browser configuration and factory.

This module wraps the shared BrowserCore for the Leonardo authentication service.
"""

from patchright.async_api import Browser, BrowserContext
from src.config.settings import settings

from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig
from shared.network.factory import ProxyFactory


class LeonardoBrowserFactory:
    """
    Leonardo-specific browser factory with enhanced stealth and Tor support.

    Features:
    - Automatic Tor proxy detection
    - Enhanced stealth (CDP removal, realistic fingerprinting)
    - Fallback to HTTP proxies or direct connection
    """

    def __init__(
        self,
        headless: bool = False,
        enable_tor: bool = True,
        http_proxies: list[str] | None = None
    ) -> None:
        """
        Initialize Leonardo browser factory.

        Args:
            headless: Run in headless mode
            enable_tor: Try to use Tor if available
            http_proxies: Optional list of HTTP proxy URLs
        """
        # Configure stealth for Leonardo (Paranoid Mode)
        stealth_config = StealthConfig(
            spoof_webgl=True,
            mask_navigator=True,
            canvas_noise=True,
            audio_noise=True,
            vendor="Google Inc. (Intel)",
            renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11, vs_5_0, ps_5_0)",
        )

        # Create browser core
        self.core = BrowserCore(headless=headless, stealth_config=stealth_config)

        # Setup proxy manager with auto-detection
        self.proxy_manager = ProxyFactory.create_auto(
            enable_tor=enable_tor,
            http_proxies=http_proxies,
            allow_direct=True  # Fallback to direct if no proxy available
        )

    async def start(self) -> None:
        """
        Start the browser with proxy auto-selection.

        Automatically tries:
        1. Tor (if enabled and available)
        2. HTTP proxies (if provided)
        3. Direct connection (fallback)
        """
        # Get selected proxy provider
        provider = self.proxy_manager.active_provider

        # Start browser with proxy
        await self.core.start(proxy_provider=provider)

    async def create_context(self, user_agent: str | None = None) -> BrowserContext:
        """Create a new isolated browser context."""
        return await self.core.create_context(user_agent=user_agent)

    async def stop(self) -> None:
        """Close browser."""
        await self.core.stop()

    @property
    def browser(self) -> "Browser | None":
        """Access to underlying browser instance."""
        return self.core.browser


# Global Singleton with Tor support
browser_factory = LeonardoBrowserFactory(
    headless=settings.HEADLESS,
    enable_tor=settings.USE_TOR_IF_AVAILABLE,
    http_proxies=settings.HTTP_PROXIES if settings.HTTP_PROXIES else None
)
