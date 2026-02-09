"""
Tor SOCKS5 proxy provider with auto-detection.
"""

import socket
from loguru import logger

from ..proxy_provider import ProxyProvider, ProxyConfig


class TorProxyProvider(ProxyProvider):
    """
    Tor SOCKS5 proxy provider.
    
    Automatically detects if Tor is running on localhost by attempting
    a connection to the SOCKS5 port.
    """
    
    def __init__(self, port: int = 9050, password: str | None = None, host: str = "127.0.0.1") -> None:
        """
        Initialize Tor proxy provider.
        
        Args:
            port: Tor SOCKS5 port (default: 9050)
            password: Optional Tor control password
            host: Tor host (default: localhost)
        """
        self._host = host
        self._port = port
        self._password = password
        self._available: bool | None = None  # Cache availability check
    
    def is_available(self) -> bool:
        """
        Check if Tor is running by trying to connect to SOCKS5 port.
        
        Returns:
            True if Tor is running and accepting connections
        """
        if self._available is not None:
            return self._available
        
        try:
            with socket.create_connection((self._host, self._port), timeout=1):
                logger.info(f"✅ Tor detected on {self._host}:{self._port}")
                self._available = True
                return True
        except (socket.error, socket.timeout, OSError) as e:
            logger.debug(f"Tor not available on {self._host}:{self._port}: {e}")
            self._available = False
            return False
    
    def get_proxy(self) -> ProxyConfig:
        """
        Returns Tor SOCKS5 proxy configuration.
        
        Note: Playwright supports SOCKS5 natively.
        """
        return ProxyConfig(
            server=f"socks5://{self._host}:{self._port}",
            username="tor" if self._password else None,
            password=self._password,
        )
    
    @property
    def priority(self) -> int:
        """Highest priority - Tor is most anonymous."""
        return 1
    
    @property
    def name(self) -> str:
        """Human-readable name."""
        return f"Tor SOCKS5 ({self._host}:{self._port})"
    
    def request_new_circuit(self) -> None:
        """
        Request a new Tor circuit (new IP address).
        
        Note: Requires Tor control port access (typically 9051).
        This is a future enhancement.
        """
        # TODO: Implement via Tor control protocol
        # Would need to send "SIGNAL NEWNYM" to control port 9051
        logger.warning("New circuit request not yet implemented")
