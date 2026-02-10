"""
Proxy manager with auto-selection based on availability and priority.
"""


from loguru import logger

from .proxy_provider import ProxyConfig, ProxyProvider


class ProxyManager:
    """
    Manages multiple proxy providers and auto-selects the best available one.

    Usage:
        manager = ProxyManager()
        manager.register(TorProxyProvider())
        manager.register(HttpProxyProvider("http://proxy.com:8080"))
        manager.auto_select()

        config = manager.get_config()  # Returns best available proxy
    """

    def __init__(self) -> None:
        self._providers: list[ProxyProvider] = []
        self._selected: ProxyProvider | None = None

    def register(self, provider: ProxyProvider) -> None:
        """
        Register a proxy provider.

        Args:
            provider: ProxyProvider instance to register
        """
        self._providers.append(provider)
        logger.debug(f"Registered proxy provider: {provider.name}")

    def auto_select(self) -> ProxyProvider | None:
        """
        Automatically select the best available proxy based on priority.

        Returns:
            Selected ProxyProvider, or None if none available
        """
        # Filter only available providers
        available = [p for p in self._providers if p.is_available()]

        if not available:
            logger.warning("⚠️ No proxy providers available")
            self._selected = None
            return None

        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: p.priority)
        selected = available[0]

        logger.info(f"🌐 Selected proxy: {selected.name} (priority: {selected.priority})")
        self._selected = selected
        return selected

    def get_config(self) -> ProxyConfig | None:
        """
        Get proxy configuration from the selected provider.

        Returns:
            ProxyConfig if a provider is selected, None otherwise
        """
        if not self._selected:
            logger.warning("No proxy selected. Call auto_select() first.")
            return None

        return self._selected.get_proxy()

    @property
    def active_provider(self) -> ProxyProvider | None:
        """Get the currently selected provider."""
        return self._selected

    @property
    def available_providers(self) -> list[ProxyProvider]:
        """Get list of all available providers."""
        return [p for p in self._providers if p.is_available()]

    def get_playwright_proxy(self) -> dict[str, str] | None:
        """
        Get proxy configuration in Playwright format.

        Returns:
            Dict suitable for playwright.launch(proxy=...) or None
        """
        config = self.get_config()
        if not config or not config.server:
            return None

        proxy_dict = {"server": config.server}

        if config.username:
            proxy_dict["username"] = config.username
        if config.password:
            proxy_dict["password"] = config.password
        if config.bypass:
            proxy_dict["bypass"] = config.bypass

        return proxy_dict
