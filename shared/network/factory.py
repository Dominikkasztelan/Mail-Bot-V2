"""
Proxy factory for convenient ProxyManager creation.
"""


from loguru import logger

from .providers.direct import DirectConnectionProvider
from .providers.http import HttpProxyProvider
from .providers.tor import TorProxyProvider
from .proxy_manager import ProxyManager


class ProxyFactory:
    """
    Convenience factory for creating configured ProxyManager instances.

    Examples:
        # Auto-mode: Try Tor, then HTTP proxies, then direct
        manager = ProxyFactory.create_auto(
            enable_tor=True,
            http_proxies=["http://proxy1.com:8080", "http://proxy2.com:8080"]
        )

        # Tor-only mode (fail if Tor not available)
        manager = ProxyFactory.create_tor_only()

        # Direct connection only
        manager = ProxyFactory.create_direct()
    """

    @staticmethod
    def create_auto(
        enable_tor: bool = True,
        tor_port: int = 9050,
        http_proxies: list[str] | None = None,
        allow_direct: bool = True
    ) -> ProxyManager:
        """
        Create ProxyManager with automatic provider selection.

        Priority order:
        1. Tor (if enabled and available)
        2. HTTP proxies (in list order)
        3. Direct connection (if allowed)

        Args:
            enable_tor: Whether to try Tor (default: True)
            tor_port: Tor SOCKS5 port (default: 9050)
            http_proxies: List of HTTP proxy URLs (optional)
            allow_direct: Allow direct connection as fallback (default: True)

        Returns:
            Configured ProxyManager with best available proxy selected
        """
        manager = ProxyManager()

        # Register Tor if enabled
        if enable_tor:
            tor_provider = TorProxyProvider(port=tor_port)
            manager.register(tor_provider)

        # Register HTTP proxies
        if http_proxies:
            for i, proxy_url in enumerate(http_proxies):
                # Priority: 10, 11, 12, ... (lower than Tor's 1)
                priority = 10 + i
                http_provider = HttpProxyProvider(proxy_url, priority=priority)
                manager.register(http_provider)

        # Register direct connection (fallback)
        if allow_direct:
            manager.register(DirectConnectionProvider())

        # Auto-select best available
        manager.auto_select()

        return manager

    @staticmethod
    def create_tor_only(port: int = 9050) -> ProxyManager:
        """
        Create ProxyManager with Tor only (no fallback).

        Raises warning if Tor is not available.

        Args:
            port: Tor SOCKS5 port (default: 9050)

        Returns:
            ProxyManager configured for Tor only
        """
        manager = ProxyManager()
        tor_provider = TorProxyProvider(port=port)
        manager.register(tor_provider)
        manager.auto_select()

        if not manager.active_provider:
            logger.warning("⚠️ Tor-only mode but Tor is not available!")

        return manager

    @staticmethod
    def create_direct() -> ProxyManager:
        """
        Create ProxyManager with direct connection only (no proxy).

        Returns:
            ProxyManager configured for direct connection
        """
        manager = ProxyManager()
        manager.register(DirectConnectionProvider())
        manager.auto_select()
        return manager

    @staticmethod
    def from_config(
        use_tor: bool = True,
        proxies: list[str] | None = None,
        require_proxy: bool = False
    ) -> ProxyManager:
        """
        Create ProxyManager from simple configuration.

        Args:
            use_tor: Try Tor if available
            proxies: List of proxy URLs
            require_proxy: Don't allow direct connection fallback

        Returns:
            Configured ProxyManager
        """
        return ProxyFactory.create_auto(
            enable_tor=use_tor,
            http_proxies=proxies,
            allow_direct=not require_proxy
        )
