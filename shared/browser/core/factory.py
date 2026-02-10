from typing import Any

from loguru import logger
from patchright.async_api import Browser, BrowserContext, Playwright, async_playwright
from shared.browser.core.stealth.injector import StealthConfig, StealthInjector
from shared.network.proxy_provider import ProxyProvider


class BrowserCore:
    """
    Core class to manage Playwright browser instances with built-in stealth and proxy support.
    """

    def __init__(self, headless: bool = True, stealth_config: StealthConfig | None = None) -> None:
        self.headless = headless
        self.stealth_config = stealth_config or StealthConfig()
        self.stealth_injector = StealthInjector(self.stealth_config)
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    @property
    def browser(self) -> Browser | None:
        """Access to the underlying browser instance."""
        return self._browser

    async def start(self, proxy_provider: ProxyProvider | None = None) -> None:
        """Starts the browser engine."""
        if self._playwright:
            return

        # Fix for Windows: Use SelectorEventLoop instead of ProactorEventLoop
        # to support subprocess operations required by Playwright
        import sys
        import asyncio
        if sys.platform == "win32":
            try:
                from asyncio import WindowsSelectorEventLoopPolicy
                if not isinstance(asyncio.get_event_loop_policy(), WindowsSelectorEventLoopPolicy):
                    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
                    logger.debug("Applied WindowsSelectorEventLoopPolicy for Playwright compatibility.")
            except Exception as e:
                logger.debug(f"Could not set WindowsSelectorEventLoopPolicy: {e}")

        logger.info("🚀 Starting Browser Core...")
        self._playwright = await async_playwright().start()

        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--password-store=basic",
            # Improve WebGL stealth in headless
            "--use-gl=angle",
            "--use-angle=gl",
        ]

        if self.headless:
            # Additional headless masking
            args.extend(["--hide-scrollbars", "--mute-audio"])

        proxy_args: dict[str, str] | None = None
        if proxy_provider:
            proxy_conf = proxy_provider.get_proxy()
            if proxy_conf.server:
                proxy_args = {"server": proxy_conf.server}
                if proxy_conf.username:
                    proxy_args["username"] = proxy_conf.username
                    proxy_args["password"] = proxy_conf.password or ""
                logger.info(f"🌐 Using Proxy: {proxy_conf.server}")

        args.append("--excludeSwitches=enable-automation")
        args.append("--disable-extensions")

        launch_options: dict[str, Any] = {
            "headless": self.headless, 
            "channel": "chrome",
            "args": args,
            "ignore_default_args": ["--enable-automation"]
        }
        if proxy_args:
            launch_options["proxy"] = proxy_args
        if not self._playwright:
             raise RuntimeError("Playwright not started. Call start() first.")

        try:
            # Launch Chromium (default, most compatible)
            self._browser = await self._playwright.chromium.launch(**launch_options)
        except Exception as e:
            logger.error(f"❌ Failed to launch browser: {e}")
            raise

        logger.info("✅ Browser Core started successfully.")

    async def create_context(self, storage_state: Any | None = None, user_agent: str | None = None) -> BrowserContext:
        """Creates a secure context with stealth injections."""
        if not self._browser:
            await self.start()

        # Mypy assertion
        assert self._browser is not None

        context = await self._browser.new_context(
            storage_state=storage_state,
            user_agent=user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL",
            timezone_id="Europe/Warsaw",  # Should match proxy in prod
        )

        # Apply Stealth
        await self.stealth_injector.apply_stealth(context)

        return context

    async def stop(self) -> None:
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
            
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                # Silence common Windows pipe errors during shutdown
                if "closed pipe" not in str(e).lower():
                    logger.debug(f"Non-critical shutdown error: {e}")
            self._playwright = None
            
        logger.info("🛑 Browser Core stopped.")
