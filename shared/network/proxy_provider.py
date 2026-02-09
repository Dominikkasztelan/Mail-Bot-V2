"""
Proxy configuration and provider abstractions.

This module provides a clean interface for proxy management across all projects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyConfig:
    """Immutable proxy configuration (thread-safe)."""
    
    server: str
    username: str | None = None
    password: str | None = None
    bypass: str | None = None


class ProxyProvider(ABC):
    """
    Abstract base class for all proxy providers.
    
    Implementations must provide:
    - Proxy configuration via get_proxy()
    - Availability check via is_available()
    - Priority for auto-selection
    - Human-readable name
    """
    
    @abstractmethod
    def get_proxy(self) -> ProxyConfig:
        """Returns proxy configuration."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if this proxy type is currently available."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Priority for auto-selection (lower number = higher priority).
        
        Recommended values:
        - 1: Tor (most anonymous)
        - 2-50: Premium proxies
        - 51-100: Free proxies
        - 999: Direct connection (fallback)
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging."""
        pass
