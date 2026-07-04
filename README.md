#  Binance Futures Testnet Trading Bot

A professional, modular Python trading bot for placing **Market** and **Limit** orders on the **Binance Futures Testnet (USDT-M)**.

Built with clean architecture, comprehensive error handling, structured logging, and a polished CLI experience.

---

##  Features

- **Market & Limit Orders** — Place BUY/SELL orders on Binance Futures Testnet
- **Dual CLI Modes** — Argument mode for scripting + Interactive menu for guided use
- **Input Validation** — Rejects invalid symbols, sides, quantities, and prices with clear messages
- **HMAC-SHA256 Signing** — Direct REST API authentication (no wrapper library dependency)
- **Retry Mechanism** — Exponential backoff on network failures (configurable retries)
- **Structured Logging** — Dual output: detailed file logs + clean console logs
- **Colored Output** — Beautiful, formatted terminal output with status indicators
- **Order History** — Local JSON persistence of all placed orders
- **Order Confirmation** — Safety prompt before submitting (skippable with `--yes`)
- **Custom Exceptions** — Typed exception hierarchy for precise error handling

---

##  Architecture

```
┌─────────────────────────────────────────────────┐
│                    CLI Layer                     │
│              (cli.py — argparse)                 │
│         Parses input, routes to modes            │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Validation Layer                    │
│           (bot/validators.py)                    │
│    Pure functions — no I/O, no side effects      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            Orchestration Layer                   │
│             (bot/orders.py)                      │
│   Coordinates: validate → submit → log → save   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│               API Client Layer                   │
│             (bot/client.py)                      │
│    HMAC signing, HTTP requests, retry logic      │
└─────────────────────────────────────────────────┘
```

Each layer has a single responsibility and communicates only with its adjacent layers.

---

## Folder Structure

```
trading_bot/
│
├── bot/
│   ├── __init__.py          # Package init with module documentation
│   ├── client.py            # Binance REST API client (HMAC, retry, sessions)
│   ├── orders.py            # Order placement orchestration
│   ├── validators.py        # Input validation (pure functions)
│   ├── logging_config.py    # Dual-handler logging setup
│   ├── config.py            # Environment variable management
│   ├── exceptions.py        # Custom exception hierarchy
│   └── utils.py             # Formatting, colors, order history
│
├── logs/                    # Generated log files (gitignored)
├── screenshots/             # CLI output screenshots
├── tests/
│   ├── __init__.py
│   └── test_validators.py   # Unit tests for validation
│
├── cli.py                   # CLI entry point
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

---

##  Installation

### Prerequisites

- Python 3.10+
- Binance Futures Testnet account ([Register here](https://testnet.binancefuture.com))

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/trading_bot.git
cd trading_bot

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API credentials
cp .env.example .env
# Edit .env with your Binance Testnet API Key and Secret
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BINANCE_TESTNET_API_KEY` | ✅ | — | Your Binance Futures Testnet API key |
| `BINANCE_TESTNET_API_SECRET` | ✅ | — | Your Binance Futures Testnet API secret |
| `BINANCE_TESTNET_BASE_URL` | ❌ | `https://testnet.binancefuture.com` | API base URL |
| `REQUEST_TIMEOUT` | ❌ | `10` | HTTP timeout in seconds |
| `MAX_RETRIES` | ❌ | `3` | Max retry attempts for network errors |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

---

## How to Run

### Argument Mode (Required CLI)

```bash
# Market Order — BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Market Order — SELL
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.5

# Limit Order — BUY
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 50000

# Limit Order — SELL (skip confirmation)
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 4000 --yes
```

### Interactive Mode (Bonus)

```bash
python cli.py --interactive
```

### Help

```bash
python cli.py --help
```

---

##  CLI Examples

### Market Order

```bash
$ python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --yes
```

```
========================================================
                      Trading Bot
========================================================

                    Order Summary
--------------------------------------------------------
  Symbol               BTCUSDT
  Side                 BUY
  Type                 MARKET
  Quantity             0.01
--------------------------------------------------------

--------------------------------------------------------
  ⏳ Submitting Order...
--------------------------------------------------------

✓ SUCCESS
--------------------------------------------------------
  Order ID             1234567890
  Status               FILLED
  Executed Qty         0.01
  Average Price        64532.10
  Execution Time       0.342s

========================================================
```

### Limit Order

```bash
$ python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 4000 --yes
```

```
========================================================
                      Trading Bot
========================================================

                    Order Summary
--------------------------------------------------------
  Symbol               ETHUSDT
  Side                 SELL
  Type                 LIMIT
  Quantity             0.5
  Price                4000.0
--------------------------------------------------------

--------------------------------------------------------
  ⏳ Submitting Order...
--------------------------------------------------------

✓ SUCCESS
--------------------------------------------------------
  Order ID             9876543210
  Status               NEW
  Executed Qty         0
  Average Price        0
  Execution Time       0.287s

========================================================
```

---

##  Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage (if pytest-cov installed)
pytest tests/ -v --cov=bot
```

### Expected Test Output

```
tests/test_validators.py::TestValidateSymbol::test_valid_symbol_uppercase      PASSED
tests/test_validators.py::TestValidateSymbol::test_valid_symbol_lowercase      PASSED
tests/test_validators.py::TestValidateSide::test_buy_uppercase                 PASSED
tests/test_validators.py::TestValidateQuantity::test_negative_quantity_raises   PASSED
tests/test_validators.py::TestValidatePrice::test_limit_order_missing_raises   PASSED
tests/test_validators.py::TestValidateOrderParams::test_valid_market_order     PASSED
...
35 passed in 0.12s
```

---

## Sample Log Output

### `logs/trading_bot.log`

```
2025-07-04 10:30:00 | INFO     | trading_bot | setup_logging:58 | Logging initialized — file: logs/trading_bot.log | level: INFO
2025-07-04 10:30:00 | INFO     | trading_bot | main:198 | Trading Bot started
2025-07-04 10:30:01 | INFO     | trading_bot.bot.client | place_order:195 | Placing order: BTCUSDT BUY MARKET qty=0.01 price=MARKET
2025-07-04 10:30:01 | INFO     | trading_bot.bot.orders | place_order:89 | Order successful | ID: 1234567890 | Symbol: BTCUSDT | Side: BUY | Type: MARKET | Status: FILLED | Executed Qty: 0.01 | Avg Price: 64532.10 | Time: 0.342s
```

---

## Common Errors & Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Configuration error: BINANCE_TESTNET_API_KEY is missing` | No `.env` file or empty API key | Copy `.env.example` to `.env` and add credentials |
| `Validation error on 'symbol': not a valid symbol` | Symbol contains invalid characters | Use uppercase letters/digits only (e.g., `BTCUSDT`) |
| `Validation error on 'price': required for LIMIT` | LIMIT order without `--price` | Add `--price <value>` argument |
| `Binance API error [HTTP 400] [Code -1121]` | Invalid symbol on Binance | Check available symbols on testnet |
| `Network error: Request failed after 3 attempts` | Testnet unreachable | Check internet connection, try again |
| `Binance API error [HTTP 400] [Code -2019]` | Insufficient margin | Add funds in testnet dashboard |

---

##  Design Decisions

### Why Direct REST API Instead of python-binance?

- **Transparency**: Every API interaction is visible — no hidden abstractions
- **Learning**: Demonstrates understanding of HMAC-SHA256 signing and REST APIs
- **Control**: Custom retry logic, timeout handling, and error translation
- **Fewer Dependencies**: Smaller attack surface, fewer transitive dependencies

### Why Frozen Dataclass for Settings?

- **Immutability**: Configuration cannot be accidentally modified at runtime
- **Type Safety**: Each setting has a declared type
- **Single Source of Truth**: All config access goes through one validated object

### Why Custom Exception Hierarchy?

- **Granular Handling**: Catch `OrderError` specifically, or `TradingBotError` broadly
- **Context Preservation**: Each exception carries structured attributes (field, status_code, error_code)
- **Clean Separation**: No string-parsing error messages in catch blocks

### Why Separate Orchestration Layer (orders.py)?

- **Single Responsibility**: `client.py` handles HTTP only; `orders.py` coordinates the workflow
- **Testability**: Business logic can be tested by mocking just the client
- **Extensibility**: Adding pre/post-trade logic (e.g., risk checks) requires changes in one file

---

##  Assumptions

1. **Testnet Only** — This bot is designed exclusively for Binance Futures Testnet. Do not use with real funds.
2. **USDT-M Futures** — All orders are placed on the USDT-margined futures market.
3. **Symbol Validity** — The bot validates symbol format but does not verify if a symbol exists on the exchange (Binance API returns the appropriate error).
4. **Time Sync** — The bot uses the local system clock for timestamps. Significant clock drift may cause signature errors.
5. **Single Order** — Each CLI invocation places one order. Batch ordering is not supported in this version.

---

##  Future Improvements

- **WebSocket Integration** — Real-time price streaming for informed order decisions
- **Order Book Display** — Show current bid/ask before placing orders
- **Position Management** — View open positions and P&L
- **Risk Management** — Pre-trade checks (max position size, daily loss limits)
- **AI Agent Integration** — Modular architecture enables plugging in AI-driven signal generators
- **Database Storage** — Replace JSON order history with SQLite for querying
- **Docker Support** — Containerized deployment for consistent environments
- **CI/CD Pipeline** — Automated testing and linting on every push

---

##  License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
