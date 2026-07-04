"""
Input validation for trading order parameters.

Every validation function follows the same contract:
    - Accept a raw input value.
    - Return the cleaned/normalized value if valid.
    - Raise ValidationError with field name + actionable message if invalid.

This module is pure logic — no I/O, no side effects, fully unit-testable.
"""

import re
from typing import Optional

from bot.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Binance Futures symbols: uppercase letters + digits (e.g., BTCUSDT, 1000PEPEUSDT)
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,20}$")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a trading pair symbol.

    Args:
        symbol: Raw symbol input (e.g., 'btcusdt', 'ETHUSDT').

    Returns:
        Uppercase symbol string.

    Raises:
        ValidationError: If symbol is empty, too long, or contains
                         invalid characters.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("symbol", "Symbol cannot be empty.")

    cleaned = symbol.strip().upper()

    if not SYMBOL_PATTERN.match(cleaned):
        raise ValidationError(
            "symbol",
            f"'{symbol}' is not a valid symbol. "
            "Use uppercase letters and digits only (e.g., BTCUSDT, ETHUSDT).",
        )

    return cleaned


def validate_side(side: str) -> str:
    """Validate and normalize the order side.

    Args:
        side: Raw side input (e.g., 'buy', 'SELL').

    Returns:
        Uppercase side string ('BUY' or 'SELL').

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    if not side or not side.strip():
        raise ValidationError("side", "Side cannot be empty.")

    cleaned = side.strip().upper()

    if cleaned not in VALID_SIDES:
        raise ValidationError(
            "side",
            f"'{side}' is not a valid side. Must be one of: {VALID_SIDES}.",
        )

    return cleaned


def validate_order_type(order_type: str) -> str:
    """Validate and normalize the order type.

    Args:
        order_type: Raw order type input (e.g., 'market', 'LIMIT').

    Returns:
        Uppercase order type string ('MARKET' or 'LIMIT').

    Raises:
        ValidationError: If order type is not MARKET or LIMIT.
    """
    if not order_type or not order_type.strip():
        raise ValidationError("order_type", "Order type cannot be empty.")

    cleaned = order_type.strip().upper()

    if cleaned not in VALID_ORDER_TYPES:
        raise ValidationError(
            "order_type",
            f"'{order_type}' is not a valid order type. "
            f"Must be one of: {VALID_ORDER_TYPES}.",
        )

    return cleaned


def validate_quantity(quantity: str | float) -> float:
    """Validate that quantity is a positive number.

    Args:
        quantity: Raw quantity input (string or float).

    Returns:
        Quantity as a positive float.

    Raises:
        ValidationError: If quantity is not a valid positive number.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(
            "quantity",
            f"'{quantity}' is not a valid number. Quantity must be a positive number.",
        )

    if qty <= 0:
        raise ValidationError(
            "quantity",
            f"Quantity must be greater than zero. Got: {qty}.",
        )

    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[float]:
    """Validate price — required for LIMIT orders, ignored for MARKET.

    Args:
        price:      Raw price input (may be None for MARKET orders).
        order_type: Already-validated order type ('MARKET' or 'LIMIT').

    Returns:
        Price as a positive float for LIMIT orders, or None for MARKET.

    Raises:
        ValidationError: If LIMIT order has no price, or price is invalid.
    """
    if order_type == "MARKET":
        return None

    # LIMIT order — price is mandatory
    if price is None:
        raise ValidationError(
            "price",
            "Price is required for LIMIT orders. "
            "Use --price to specify (e.g., --price 65000).",
        )

    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(
            "price",
            f"'{price}' is not a valid price. Must be a positive number.",
        )

    if p <= 0:
        raise ValidationError(
            "price",
            f"Price must be greater than zero. Got: {p}.",
        )

    return p


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
) -> dict:
    """Validate all order parameters in a single call.

    This is the main entry point for validation — it runs all individual
    validators and returns a clean, normalized parameter dictionary.

    Args:
        symbol:     Trading pair (e.g., 'BTCUSDT').
        side:       Order side ('BUY' or 'SELL').
        order_type: Order type ('MARKET' or 'LIMIT').
        quantity:   Order quantity.
        price:      Order price (required for LIMIT).

    Returns:
        Dictionary with validated and normalized parameters:
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0.01,
            "price": None
        }

    Raises:
        ValidationError: On the first invalid parameter encountered.
    """
    validated_type = validate_order_type(order_type)

    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validated_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, validated_type),
    }
