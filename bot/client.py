"""
Binance Futures Testnet REST API Client.

Handles all direct communication with the Binance API:
    - HMAC-SHA256 request signing
    - Authenticated POST/GET requests
    - Retry mechanism for transient network failures
    - Response parsing and error translation

This module is the ONLY place that imports `requests` and touches
the network — every other module works with Python dicts.
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from bot.config import Settings
from bot.exceptions import APIError, NetworkError, OrderError
from bot.utils import get_timestamp_ms


logger = logging.getLogger("trading_bot")


# ---------------------------------------------------------------------------
# API Endpoints (relative to base URL)
# ---------------------------------------------------------------------------
ENDPOINTS = {
    "order": "/fapi/v1/order",
    "exchange_info": "/fapi/v1/exchangeInfo",
    "server_time": "/fapi/v1/time",
}


class BinanceClient:
    """Authenticated client for Binance Futures Testnet REST API.

    Responsibilities:
        - Sign requests with HMAC-SHA256
        - Send authenticated HTTP requests
        - Retry on transient network errors (ConnectionError, Timeout)
        - Translate HTTP/API errors into custom exceptions

    Usage:
        settings = load_settings()
        client = BinanceClient(settings)
        response = client.place_order(params)
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the client with application settings.

        Args:
            settings: Validated, immutable Settings instance.
        """
        self.settings = settings
        self.base_url = settings.base_url
        self.timeout = settings.timeout
        self.max_retries = settings.max_retries

        # Persistent session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": settings.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    # ------------------------------------------------------------------
    # Request Signing
    # ------------------------------------------------------------------
    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """Add timestamp and HMAC-SHA256 signature to request parameters.

        Binance requires:
            1. A `timestamp` parameter (server time in ms).
            2. A `signature` generated from the query string using
               the API secret as the HMAC key.

        Args:
            params: Request parameters to sign.

        Returns:
            Parameters with `timestamp` and `signature` appended.
        """
        params["timestamp"] = get_timestamp_ms()
        query_string = urlencode(params)
        signature = hmac.new(
            self.settings.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    # ------------------------------------------------------------------
    # HTTP Request with Retry
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """Execute an HTTP request with retry logic for transient failures.

        Args:
            method:   HTTP method ('GET' or 'POST').
            endpoint: API endpoint key from ENDPOINTS dict.
            params:   Query/body parameters.
            signed:   Whether to add HMAC signature.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            NetworkError: After all retry attempts are exhausted.
            APIError:     If Binance returns an error response.
        """
        url = f"{self.base_url}{ENDPOINTS[endpoint]}"
        params = params or {}

        if signed:
            params = self._sign(params)

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "API %s %s (attempt %d/%d) | params: %s",
                    method, url, attempt, self.max_retries,
                    {k: v for k, v in params.items() if k != "signature"},
                )

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params if method == "GET" else None,
                    data=params if method == "POST" else None,
                    timeout=self.timeout,
                )

                logger.debug(
                    "API response [%d]: %s", response.status_code, response.text
                )

                return self._handle_response(response)

            except requests.exceptions.Timeout as exc:
                last_exception = exc
                logger.warning(
                    "Request timeout (attempt %d/%d): %s",
                    attempt, self.max_retries, exc,
                )

            except requests.exceptions.ConnectionError as exc:
                last_exception = exc
                logger.warning(
                    "Connection error (attempt %d/%d): %s",
                    attempt, self.max_retries, exc,
                )

            except (APIError, OrderError):
                # API errors are not transient — don't retry
                raise

            # Exponential backoff: 1s, 2s, 4s...
            if attempt < self.max_retries:
                wait = 2 ** (attempt - 1)
                logger.info("Retrying in %ds...", wait)
                time.sleep(wait)

        raise NetworkError(
            f"Request failed after {self.max_retries} attempts. "
            f"Last error: {last_exception}"
        )

    # ------------------------------------------------------------------
    # Response Handling
    # ------------------------------------------------------------------
    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Parse API response and raise appropriate exceptions on errors.

        Args:
            response: Raw HTTP response from Binance.

        Returns:
            Parsed JSON response dictionary.

        Raises:
            APIError: If the response indicates a client or server error.
        """
        try:
            data = response.json()
        except ValueError:
            raise APIError(
                status_code=response.status_code,
                error_msg=f"Invalid JSON response: {response.text[:200]}",
            )

        if response.status_code >= 400:
            error_code = data.get("code")
            error_msg = data.get("msg", "Unknown error")

            logger.error(
                "API error [HTTP %d] [Code %s]: %s",
                response.status_code, error_code, error_msg,
            )

            raise APIError(
                status_code=response.status_code,
                error_code=error_code,
                error_msg=error_msg,
            )

        return data

    # ------------------------------------------------------------------
    # Public API Methods
    # ------------------------------------------------------------------
    def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """Place an order on Binance Futures Testnet.

        Args:
            params: Order parameters — must include at minimum:
                    symbol, side, type, quantity.
                    For LIMIT orders: price, timeInForce.

        Returns:
            Parsed order response from Binance API.

        Raises:
            OrderError:   If the order is rejected by Binance.
            NetworkError: If the request fails after retries.
        """
        logger.info(
            "Placing order: %s %s %s qty=%s price=%s",
            params.get("symbol"),
            params.get("side"),
            params.get("type"),
            params.get("quantity"),
            params.get("price", "MARKET"),
        )

        try:
            return self._request("POST", "order", params)
        except APIError as exc:
            raise OrderError(
                status_code=exc.status_code,
                error_code=exc.error_code,
                error_msg=exc.error_msg,
            )

    def get_server_time(self) -> dict[str, Any]:
        """Fetch the Binance server time (useful for clock sync checks).

        Returns:
            Dictionary with 'serverTime' key (Unix ms).
        """
        return self._request("GET", "server_time", signed=False)
