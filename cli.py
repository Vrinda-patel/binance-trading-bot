"""
CLI entry point for the Binance Futures Testnet Trading Bot.

Supports two modes:
    1. Argument mode (required):
       python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    2. Interactive mode (bonus):
       python cli.py --interactive

The CLI layer is responsible ONLY for:
    - Parsing user input (argparse / interactive prompts)
    - Delegating to validators and order orchestration
    - Displaying the banner and confirmation prompts

It does NOT contain business logic, API calls, or formatting.
"""

import argparse
import sys
import logging
from typing import Optional

from colorama import Fore, Style

from bot.config import load_settings, PROJECT_ROOT
from bot.logging_config import setup_logging
from bot.validators import validate_order_params
from bot.client import BinanceClient
from bot.orders import place_order
from bot.exceptions import ConfigurationError, ValidationError, TradingBotError
from bot.utils import (
    print_banner,
    print_error_response,
    success,
    error,
    info,
    warning,
    highlight,
    SEPARATOR,
    THIN_SEPARATOR,
)


logger: Optional[logging.Logger] = None


# ---------------------------------------------------------------------------
# Argparse Setup
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ArgumentParser with all required and optional arguments.
    """
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=(
            "Binance Futures Testnet Trading Bot — "
            "Place Market and Limit orders via CLI."
        ),
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 4000\n"
            "  python cli.py --interactive\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--symbol", type=str, help="Trading pair symbol (e.g., BTCUSDT)"
    )
    parser.add_argument(
        "--side", type=str, help="Order side: BUY or SELL"
    )
    parser.add_argument(
        "--type", type=str, dest="order_type", help="Order type: MARKET or LIMIT"
    )
    parser.add_argument(
        "--quantity", type=str, help="Order quantity (e.g., 0.01)"
    )
    parser.add_argument(
        "--price", type=str, default=None,
        help="Order price — required for LIMIT orders (e.g., 65000)"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Launch interactive menu mode"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip order confirmation prompt"
    )

    return parser


# ---------------------------------------------------------------------------
# Order Confirmation
# ---------------------------------------------------------------------------
def confirm_order(params: dict, skip: bool = False) -> bool:
    """Ask the user to confirm before submitting the order.

    Args:
        params: Validated order parameters.
        skip:   If True, auto-confirm (--yes flag).

    Returns:
        True if the user confirms, False otherwise.
    """
    if skip:
        return True

    print(warning("\n  ⚠  Are you sure you want to place this order?"))
    response = input(f"  {highlight('Confirm [y/N]: ')}").strip().lower()
    return response in ("y", "yes")


# ---------------------------------------------------------------------------
# Argument Mode
# ---------------------------------------------------------------------------
def run_argument_mode(args: argparse.Namespace, client: BinanceClient) -> None:
    """Execute an order from CLI arguments.

    Args:
        args:   Parsed argparse namespace.
        client: Authenticated BinanceClient instance.
    """
    # Check that all required args are present
    missing = []
    if not args.symbol:
        missing.append("--symbol")
    if not args.side:
        missing.append("--side")
    if not args.order_type:
        missing.append("--type")
    if not args.quantity:
        missing.append("--quantity")

    if missing:
        print_error_response(
            f"Missing required arguments: {', '.join(missing)}\n"
            "  Run 'python cli.py --help' for usage."
        )
        sys.exit(1)

    try:
        validated = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        print_error_response(exc.message)
        sys.exit(1)

    if not confirm_order(validated, skip=args.yes):
        print(warning("\n  Order cancelled by user.\n"))
        sys.exit(0)

    place_order(client, validated, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Interactive Mode
# ---------------------------------------------------------------------------
def run_interactive_mode(client: BinanceClient) -> None:
    """Launch the interactive menu for order placement.

    Provides a guided menu loop for placing orders without
    memorizing CLI arguments.

    Args:
        client: Authenticated BinanceClient instance.
    """
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{THIN_SEPARATOR}")
        print(f"{'Select an Option':^56}")
        print(f"{THIN_SEPARATOR}{Style.RESET_ALL}")
        print(f"  {highlight('1.')} Place Market Order")
        print(f"  {highlight('2.')} Place Limit Order")
        print(f"  {highlight('3.')} Exit")
        print(f"{Fore.CYAN}{THIN_SEPARATOR}{Style.RESET_ALL}")

        choice = input(f"\n  {info('Enter choice [1-3]: ')}").strip()

        if choice == "3":
            print(success("\n  Goodbye! Happy trading. 🚀\n"))
            break

        if choice not in ("1", "2"):
            print(error("  Invalid choice. Please enter 1, 2, or 3."))
            continue

        order_type = "MARKET" if choice == "1" else "LIMIT"

        try:
            symbol = input(f"  {info('Symbol')} (e.g., BTCUSDT): ").strip()
            side = input(f"  {info('Side')} (BUY/SELL): ").strip()
            quantity = input(f"  {info('Quantity')} (e.g., 0.01): ").strip()

            price = None
            if order_type == "LIMIT":
                price = input(f"  {info('Price')} (e.g., 65000): ").strip()

            validated = validate_order_params(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
            )

        except ValidationError as exc:
            logger.warning("Validation failed: %s", exc.message)
            print_error_response(exc.message)
            continue

        if not confirm_order(validated):
            print(warning("\n  Order cancelled.\n"))
            continue

        place_order(client, validated, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    """Application entry point — bootstraps config, logging, and routing."""
    global logger

    print_banner()

    # 1. Load configuration (fail fast on bad config)
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        print_error_response(exc.message)
        sys.exit(1)

    # 2. Initialize logging
    logger = setup_logging(settings.log_dir, settings.log_level)
    logger.info("Trading Bot started")

    # 3. Initialize Binance client
    client = BinanceClient(settings)

    # 4. Parse CLI arguments and route
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.interactive:
            run_interactive_mode(client)
        elif any([args.symbol, args.side, args.order_type, args.quantity]):
            run_argument_mode(args, client)
        else:
            # No arguments provided — show help
            parser.print_help()
            print(info(
                "\n  Tip: Use --interactive for guided mode, "
                "or provide arguments directly.\n"
            ))

    except KeyboardInterrupt:
        print(warning("\n\n  Interrupted by user. Exiting...\n"))
        logger.info("Application interrupted by user (Ctrl+C)")
        sys.exit(0)

    except TradingBotError as exc:
        logger.error("Fatal error: %s", exc.message)
        print_error_response(exc.message)
        sys.exit(1)

    except Exception as exc:
        logger.exception("Unhandled exception: %s", exc)
        print_error_response(f"An unexpected error occurred: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
