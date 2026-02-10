from abc import ABC, abstractmethod


class ProxyConfig:
    server: str
    username: str | None = None
    password: str | None = None
    bypass: str | None = None

    def __init__(self, server: str, username: str | None = None, password: str | None = None, bypass: str | None = None) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.bypass = bypass


class ProxyProvider(ABC):
    @abstractmethod
    def get_proxy(self) -> ProxyConfig:
        pass


class TorProxyProvider(ProxyProvider):
    """
    Provider for local TOR proxy (SOCKS5).
    """

    def __init__(self, port: int = 9050, password: str | None = None) -> None:
        self.host = "127.0.0.1"
        self.port = port
        self.password = password

    def get_proxy(self) -> ProxyConfig:
        # Playwright supports SOCKS5
        # To force new circuit in Tor, one usually needs to send SIGNAL NEWNYM to control port (9051)
        # For sticky session within one run, using the same connection is default behavior.
        return ProxyConfig(
            server=f"socks5://{self.host}:{self.port}",
            username="tor" if self.password else None,  # Some proxies use auth to switch IP
            password=self.password,
        )
