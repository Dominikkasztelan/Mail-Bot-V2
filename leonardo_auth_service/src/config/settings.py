from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Config
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Browser / Stealth
    HEADLESS: bool = False  # Set to True in production

    # Tor / Proxy Config
    USE_TOR_IF_AVAILABLE: bool = True  # Auto-detect and use Tor if running
    TOR_PORT: int = 9050  # Standard Tor SOCKS5 port
    HTTP_PROXIES: list[str] = []  # Optional HTTP proxy URLs

    USER_DATA_DIR: Path = Path("./browser_profiles")

    # Leonardo Specifics
    LEONARDO_URL: str = "https://app.leonardo.ai/auth/login"

    # Timeouts (seconds)
    DEFAULT_TIMEOUT: int = 30000
    LOGIN_TIMEOUT: int = 60000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

# Ensure profile directory exists
settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
