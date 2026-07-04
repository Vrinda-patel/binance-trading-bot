"""
Custom exception hierarchy for the Trading Bot.

Design:
    All bot-specific exceptions inherit from TradingBotError,
    enabling callers to catch broad or narrow exception types
    depending on their error-handling needs.

    TradingBotError
    ├── ValidationError        - Invalid user input
    ├── ConfigurationError     - Missing or invalid configuration
    ├── APIError               - Binance API returned an error response
    │   └── OrderError         - Order-specific API failure
    └── NetworkError           - Connection / timeout failures
"""


class TradingBotError(Exception):
    """Base exception for all Trading Bot errors."""

    def __init__(self, message: str = "An unexpected trading bot error occurred."):
        self.message = message
        super().__init__(self.message)


class ValidationError(TradingBotError):
    """Raised when user input fails validation.

    Examples:
        - Invalid trading symbol format
        - Negative quantity
        - Missing price for LIMIT orders
    """

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error on '{field}': {message}")


class ConfigurationError(TradingBotError):
    """Raised when required configuration is missing or invalid.

    Examples:
        - Missing API key or secret in .env
        - Invalid base URL format
    """

    def __init__(self, message: str = "Invalid or missing configuration."):
        super().__init__(f"Configuration error: {message}")


class APIError(TradingBotError):
    """Raised when the Binance API returns an error response.

    Attributes:
        status_code: HTTP status code from the API.
        error_code:  Binance-specific error code (e.g., -1121).
        error_msg:   Binance error message.
    """

    def __init__(
        self,
        status_code: int,
        error_code: int | None = None,
        error_msg: str = "Unknown API error.",
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.error_msg = error_msg
        detail = f"[HTTP {status_code}]"
        if error_code is not None:
            detail += f" [Code {error_code}]"
        super().__init__(f"Binance API error {detail}: {error_msg}")


class OrderError(APIError):
    """Raised when an order-specific API call fails.

    Inherits from APIError so callers can catch either
    broad API errors or narrow order failures.
    """

    def __init__(
        self,
        status_code: int,
        error_code: int | None = None,
        error_msg: str = "Order placement failed.",
    ):
        super().__init__(status_code, error_code, error_msg)


class NetworkError(TradingBotError):
    """Raised on connection failures, timeouts, or DNS resolution errors.

    This is the exception that triggers the retry mechanism
    in the client layer.
    """

    def __init__(self, message: str = "Network request failed."):
        super().__init__(f"Network error: {message}")
