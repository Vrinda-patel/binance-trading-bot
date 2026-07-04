"""
Order placement logic and orchestration.

This module sits between the CLI layer and the API client.
It transforms validated user input into Binance API parameters,
delegates execution to the client, and handles result formatting.

Responsibilities:
    - Build API-ready parameter dictionaries
    - Measure execution time
    - Coordinate logging, display output, and order history
    - Catch and translate exceptions into user-friendly messages

This module does NOT:
    - Validate input (handled by validators.py)
    - Make HTTP requests (handled by client.py)
    - Format output (handled by utils.py)
"""

import logging
import time
from pathlib import Path
from typing import Any

from bot.client import BinanceClient
from bot.exceptions import NetworkError, OrderError, TradingBotError
from bot.utils import (
    print_order_summary,
    print_order_response,
    print_error_response,
    save_order_to_history,
    show_submitting,
)


logger = logging.getLogger("trading_bot")


def _build_order_params(validated: dict[str, Any]) -> dict[str, Any]:
    """Convert validated parameters into Binance API format.

    Binance expects specific parameter names (e.g., 'type' not 'order_type',
    'timeInForce' for LIMIT orders). This function handles that translation.

    Args:
        validated: Dictionary from validate_order_params():
                   {symbol, side, order_type, quantity, price}

    Returns:
        API-ready parameter dictionary.
    """
    params: dict[str, Any] = {
        "symbol": validated["symbol"],
        "side": validated["side"],
        "type": validated["order_type"],
        "quantity": validated["quantity"],
    }

    if validated["order_type"] == "LIMIT":
        params["price"] = validated["price"]
        params["timeInForce"] = "GTC"  # Good Till Cancelled

    return params


def place_order(
    client: BinanceClient,
    validated_params: dict[str, Any],
    project_root: Path,
) -> dict[str, Any] | None:
    """Orchestrate the full order placement workflow.

    Steps:
        1. Display order summary
        2. Build API parameters
        3. Submit to Binance via client
        4. Display response
        5. Log details
        6. Save to order history

    Args:
        client:           Authenticated BinanceClient instance.
        validated_params:  Validated order parameters from validators.
        project_root:      Project root path for order history file.

    Returns:
        Parsed API response dictionary on success, or None on failure.
    """
    # 1. Display order summary
    print_order_summary(validated_params)

    # 2. Build API-ready parameters
    api_params = _build_order_params(validated_params)

    # 3. Submit order with timing
    show_submitting()
    start_time = time.perf_counter()

    try:
        response = client.place_order(api_params)
        execution_time = time.perf_counter() - start_time

        # 4. Display success response
        print_order_response(response, execution_time)

        # 5. Log order details
        logger.info(
            "Order successful | ID: %s | Symbol: %s | Side: %s | Type: %s | "
            "Status: %s | Executed Qty: %s | Avg Price: %s | Time: %.3fs",
            response.get("orderId"),
            response.get("symbol"),
            response.get("side"),
            response.get("type"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice", "N/A"),
            execution_time,
        )

        # 6. Save to local order history
        save_order_to_history(
            params=validated_params,
            response=response,
            execution_time=execution_time,
            project_root=project_root,
        )

        return response

    except OrderError as exc:
        execution_time = time.perf_counter() - start_time
        logger.error(
            "Order failed | %s | Time: %.3fs", exc.message, execution_time
        )
        print_error_response(exc.message)
        return None

    except NetworkError as exc:
        execution_time = time.perf_counter() - start_time
        logger.error(
            "Network failure | %s | Time: %.3fs", exc.message, execution_time
        )
        print_error_response(exc.message)
        return None

    except TradingBotError as exc:
        execution_time = time.perf_counter() - start_time
        logger.error(
            "Unexpected error | %s | Time: %.3fs", exc.message, execution_time
        )
        print_error_response(exc.message)
        return None
