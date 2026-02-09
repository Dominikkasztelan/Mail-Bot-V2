"""
Direct connection provider (no proxy).
"""

from ..proxy_provider import ProxyProvider, ProxyConfig


class DirectConnectionProvider(ProxyProvider):
    """
    Direct internet connection (no proxy).
    
    This acts as a fallback when no proxy providers are available.
    """
    
    def is_available(self) -> bool:
        """Direct connection is always available."""
        return True
    
    def get_proxy(self) -> ProxyConfig:
        """Returns empty config (no proxy)."""
        return ProxyConfig(server="")
    
    @property
    def priority(self) -> int:
        """Lowest priority - only use as fallback."""
        return 999
    
    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Direct Connection (No Proxy)"
