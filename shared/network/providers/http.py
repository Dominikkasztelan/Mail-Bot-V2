"""
HTTP/HTTPS/SOCKS5 proxy provider.
"""

from urllib.parse import urlparse
from loguru import logger

from ..proxy_provider import ProxyProvider, ProxyConfig


class HttpProxyProvider(ProxyProvider):
    """
    HTTP/HTTPS/SOCKS5 proxy from URL string.
    
    Supports formats:
    - http://proxy.com:8080
    - https://proxy.com:8080
    - socks5://proxy.com:1080
    - http://user:pass@proxy.com:8080
    """
    
    def __init__(self, proxy_url: str, priority: int = 10) -> None:
        """
        Initialize HTTP proxy provider.
        
        Args:
            proxy_url: Full proxy URL (e.g., "http://user:pass@host:port")
            priority: Priority for auto-selection (default: 10)
        """
        self._proxy_url = proxy_url
        self._priority = priority
        self._config = self._parse_url(proxy_url)
    
    def _parse_url(self, url: str) -> ProxyConfig:
        """Parse proxy URL into ProxyConfig."""
        parsed = urlparse(url)
        
        # Build server without credentials
        server = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            server += f":{parsed.port}"
        
        return ProxyConfig(
            server=server,
            username=parsed.username,
            password=parsed.password,
        )
    
    def is_available(self) -> bool:
        """
        Check if proxy URL is valid.
        
        Note: This doesn't actually test connectivity - just validates format.
        For production, you might want to add a connectivity test.
        """
        return bool(self._proxy_url and self._config.server)
    
    def get_proxy(self) -> ProxyConfig:
        """Returns parsed proxy configuration."""
        return self._config
    
    @property
    def priority(self) -> int:
        """Configurable priority."""
        return self._priority
    
    @property
    def name(self) -> str:
        """Human-readable name."""
        # Mask password in logs
        if self._config.username:
            return f"HTTP Proxy ({self._config.username}@{urlparse(self._proxy_url).hostname})"
        return f"HTTP Proxy ({urlparse(self._proxy_url).hostname})"
