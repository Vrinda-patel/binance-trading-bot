"""
Binance Futures Testnet Trading Bot Package.

This package provides a modular, production-inspired trading bot
for placing Market and Limit orders on Binance Futures Testnet (USDT-M).

Modules:
    client          - Binance REST API client with HMAC-SHA256 authentication
    orders          - Order placement logic and response formatting
    validators      - Input validation with meaningful error messages
    config          - Centralized configuration via environment variables
    logging_config  - Structured logging setup
    exceptions      - Custom exception hierarchy
    utils           - Shared utility functions
"""

__version__ = "1.0.0"
__author__ = "Trading Bot"
