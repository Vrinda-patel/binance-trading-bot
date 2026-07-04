"""
Shared utility functions for the Trading Bot.

Contains formatting helpers, order history persistence,
and display utilities used across the CLI and order layers.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from colorama import Fore, Style, init as colorama_init

# Initialize colorama for cross-platform colored output
colorama_init(autoreset=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEPARATOR = "=" * 56
THIN_SEPARATOR = "-" * 56
ORDER_HISTORY_FILE = "order_history.json"


# ---------------------------------------------------------------------------
# Color Helpers
# ---------------------------------------------------------------------------
def success(text: str) -> str:
    """Wrap text in green for success messages."""
    return f"{Fore.GREEN}{Style.BRIGHT}{text}{Style.RESET_ALL}"


def error(text: str) -> str:
    """Wrap text in red for error messages."""
    return f"{Fore.RED}{Style.BRIGHT}{text}{Style.RESET_ALL}"


def warning(text: str) -> str:
    """Wrap text in yellow for warning messages."""
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def info(text: str) -> str:
    """Wrap text in cyan for informational messages."""
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"


def highlight(text: str) -> str:
    """Wrap text in bright white for emphasis."""
    return f"{Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}"


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------
def print_banner() -> None:
    """Print the application banner."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{SEPARATOR}")
    print(f"{'Trading Bot':^56}")
    print(f"{SEPARATOR}{Style.RESET_ALL}\n")


def print_order_summary(params: dict) -> None:
    """Display a formatted order request summary before submission.

    Args:
        params: Validated order parameters dictionary.
    """
    print(info(f"\n{'Order Summary':^56}"))
    print(info(THIN_SEPARATOR))
    print(f"  {'Symbol':<20} {highlight(params['symbol'])}")
    print(f"  {'Side':<20} {highlight(params['side'])}")
    print(f"  {'Type':<20} {highlight(params['order_type'])}")
    print(f"  {'Quantity':<20} {highlight(str(params['quantity']))}")

    if params.get("price") is not None:
        print(f"  {'Price':<20} {highlight(str(params['price']))}")

    print(info(THIN_SEPARATOR))


def print_order_response(response: dict, execution_time: float) -> None:
    """Display a formatted order response after submission.

    Args:
        response:       Parsed API response dictionary.
        execution_time: Time taken for the API call in seconds.
    """
    status = response.get("status", "UNKNOWN")
    order_id = response.get("orderId", "N/A")
    executed_qty = response.get("executedQty", "0")
    avg_price = response.get("avgPrice", "0")

    print(f"\n{success('✓ SUCCESS')}")
    print(info(THIN_SEPARATOR))
    print(f"  {'Order ID':<20} {highlight(str(order_id))}")
    print(f"  {'Status':<20} {highlight(status)}")
    print(f"  {'Executed Qty':<20} {highlight(executed_qty)}")
    print(f"  {'Average Price':<20} {highlight(avg_price)}")
    print(f"  {'Execution Time':<20} {highlight(f'{execution_time:.3f}s')}")
    print(f"\n{Fore.CYAN}{SEPARATOR}{Style.RESET_ALL}\n")


def print_error_response(message: str) -> None:
    """Display a formatted error message.

    Args:
        message: Error description to display.
    """
    print(f"\n{error('✗ FAILED')}")
    print(info(THIN_SEPARATOR))
    print(f"  {error(message)}")
    print(f"\n{Fore.CYAN}{SEPARATOR}{Style.RESET_ALL}\n")


# ---------------------------------------------------------------------------
# Progress Indicator
# ---------------------------------------------------------------------------
def show_submitting() -> None:
    """Display a submission indicator line."""
    print(info(f"\n{THIN_SEPARATOR}"))
    print(info("  ⏳ Submitting Order..."))
    print(info(THIN_SEPARATOR))


# ---------------------------------------------------------------------------
# Order History (JSON Persistence)
# ---------------------------------------------------------------------------
def save_order_to_history(
    params: dict,
    response: dict,
    execution_time: float,
    project_root: Path,
) -> None:
    """Append an order record to the local JSON order history file.

    Creates the file if it doesn't exist. Each entry includes the
    request parameters, API response, and metadata.

    Args:
        params:         Validated order parameters.
        response:       Parsed API response.
        execution_time: API call duration in seconds.
        project_root:   Project root directory for file placement.
    """
    history_file = project_root / ORDER_HISTORY_FILE

    # Load existing history or start fresh
    orders: list[dict[str, Any]] = []
    if history_file.exists():
        try:
            orders = json.loads(history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            orders = []

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": params,
        "response": {
            "orderId": response.get("orderId"),
            "status": response.get("status"),
            "executedQty": response.get("executedQty"),
            "avgPrice": response.get("avgPrice"),
        },
        "execution_time_seconds": round(execution_time, 3),
    }

    orders.append(record)
    history_file.write_text(
        json.dumps(orders, indent=2, default=str), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Timing Utility
# ---------------------------------------------------------------------------
def get_timestamp_ms() -> int:
    """Return the current UTC timestamp in milliseconds.

    Used for Binance API request signing.

    Returns:
        Current time as Unix timestamp in milliseconds.
    """
    return int(time.time() * 1000)
