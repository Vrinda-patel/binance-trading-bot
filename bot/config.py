"""
Centralized configuration management.

Loads all settings from environment variables (.env file) and exposes
them as a validated, immutable configuration object. No other module
should read os.environ directly — this is the single source of truth.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from bot.exceptions import ConfigurationError


# ---------------------------------------------------------------------------
# Resolve project root and load .env
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment variables.

    Attributes:
        api_key:    Binance Futures Testnet API key.
        api_secret: Binance Futures Testnet API secret.
        base_url:   Testnet REST API base URL.
        timeout:    HTTP request timeout in seconds.
        max_retries: Maximum retry attempts for transient network errors.
        log_level:  Logging verbosity (DEBUG, INFO, WARNING, ERROR).
        log_dir:    Directory path for log file output.
    """

    api_key: str
    api_secret: str
    base_url: str
    timeout: int
    max_retries: int
    log_level: str
    log_dir: Path


def load_settings() -> Settings:
    """Load and validate settings from environment variables.

    Returns:
        A frozen Settings dataclass instance.

    Raises:
        ConfigurationError: If required variables are missing or invalid.
    """
    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key or api_key == "your_api_key_here":
        raise ConfigurationError(
            "BINANCE_TESTNET_API_KEY is missing or still set to the placeholder. "
            "Please copy .env.example to .env and add your testnet API key."
        )

    if not api_secret or api_secret == "your_api_secret_here":
        raise ConfigurationError(
            "BINANCE_TESTNET_API_SECRET is missing or still set to the placeholder. "
            "Please copy .env.example to .env and add your testnet API secret."
        )

    base_url = os.getenv(
        "BINANCE_TESTNET_BASE_URL", "https://testnet.binancefuture.com"
    ).rstrip("/")

    try:
        timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))
        if timeout <= 0:
            raise ValueError
    except ValueError:
        raise ConfigurationError(
            "REQUEST_TIMEOUT must be a positive integer (seconds)."
        )

    try:
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        if max_retries < 0:
            raise ValueError
    except ValueError:
        raise ConfigurationError(
            "MAX_RETRIES must be a non-negative integer."
        )

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        raise ConfigurationError(
            f"LOG_LEVEL must be one of {valid_levels}. Got: '{log_level}'."
        )

    log_dir = PROJECT_ROOT / "logs"

    return Settings(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        log_level=log_level,
        log_dir=log_dir,
    )
