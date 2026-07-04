"""
Unit tests for bot.validators module.

Tests cover all validation functions with both valid and invalid inputs.
These tests require NO network access, NO API keys, and NO external state.
"""

# pyrefly: ignore [missing-import]
import pytest

from bot.exceptions import ValidationError
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_order_params,
)


# =========================================================================
# validate_symbol
# =========================================================================
class TestValidateSymbol:
    """Tests for symbol validation."""

    def test_valid_symbol_uppercase(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_valid_symbol_lowercase_normalized(self):
        assert validate_symbol("ethusdt") == "ETHUSDT"

    def test_valid_symbol_with_whitespace(self):
        assert validate_symbol("  BTCUSDT  ") == "BTCUSDT"

    def test_valid_symbol_with_digits(self):
        assert validate_symbol("1000PEPEUSDT") == "1000PEPEUSDT"

    def test_empty_symbol_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_symbol("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_symbol("   ")

    def test_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="not a valid symbol"):
            validate_symbol("BTC-USDT")

    def test_symbol_too_long_raises(self):
        with pytest.raises(ValidationError, match="not a valid symbol"):
            validate_symbol("A" * 21)


# =========================================================================
# validate_side
# =========================================================================
class TestValidateSide:
    """Tests for order side validation."""

    def test_buy_uppercase(self):
        assert validate_side("BUY") == "BUY"

    def test_sell_lowercase_normalized(self):
        assert validate_side("sell") == "SELL"

    def test_side_with_whitespace(self):
        assert validate_side("  buy  ") == "BUY"

    def test_empty_side_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_side("")

    def test_invalid_side_raises(self):
        with pytest.raises(ValidationError, match="not a valid side"):
            validate_side("HOLD")


# =========================================================================
# validate_order_type
# =========================================================================
class TestValidateOrderType:
    """Tests for order type validation."""

    def test_market_uppercase(self):
        assert validate_order_type("MARKET") == "MARKET"

    def test_limit_lowercase_normalized(self):
        assert validate_order_type("limit") == "LIMIT"

    def test_empty_type_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_order_type("")

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError, match="not a valid order type"):
            validate_order_type("STOP_LOSS")


# =========================================================================
# validate_quantity
# =========================================================================
class TestValidateQuantity:
    """Tests for quantity validation."""

    def test_valid_quantity_string(self):
        assert validate_quantity("0.01") == 0.01

    def test_valid_quantity_float(self):
        assert validate_quantity(1.5) == 1.5

    def test_valid_quantity_integer_string(self):
        assert validate_quantity("10") == 10.0

    def test_zero_quantity_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_quantity("0")

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_quantity("-1")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity("abc")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity("")


# =========================================================================
# validate_price
# =========================================================================
class TestValidatePrice:
    """Tests for price validation."""

    def test_market_order_ignores_price(self):
        assert validate_price("12345", "MARKET") is None

    def test_market_order_none_price(self):
        assert validate_price(None, "MARKET") is None

    def test_limit_order_valid_price(self):
        assert validate_price("65000", "LIMIT") == 65000.0

    def test_limit_order_float_price(self):
        assert validate_price(4000.50, "LIMIT") == 4000.50

    def test_limit_order_missing_price_raises(self):
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_price(None, "LIMIT")

    def test_limit_order_negative_price_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_price("-100", "LIMIT")

    def test_limit_order_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="not a valid price"):
            validate_price("abc", "LIMIT")

    def test_limit_order_zero_price_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_price("0", "LIMIT")


# =========================================================================
# validate_order_params (integration of all validators)
# =========================================================================
class TestValidateOrderParams:
    """Tests for the aggregate validation function."""

    def test_valid_market_order(self):
        result = validate_order_params(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.01",
        )
        assert result == {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0.01,
            "price": None,
        }

    def test_valid_limit_order(self):
        result = validate_order_params(
            symbol="ethusdt",
            side="sell",
            order_type="limit",
            quantity="0.5",
            price="4000",
        )
        assert result == {
            "symbol": "ETHUSDT",
            "side": "SELL",
            "order_type": "LIMIT",
            "quantity": 0.5,
            "price": 4000.0,
        }

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValidationError):
            validate_order_params(
                symbol="INVALID!!",
                side="BUY",
                order_type="MARKET",
                quantity="0.01",
            )

    def test_limit_without_price_raises(self):
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_order_params(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity="0.01",
            )
