# binance-futures-bot

A production-grade CLI trading bot that places **MARKET** and **LIMIT** orders on the
**Binance USDT-M Futures Testnet**. Built with `python-binance`, `typer`, `rich`,
`loguru`, and `pydantic` v2 — emphasising clean code structure, validated inputs,
comprehensive logging, and a polished terminal UX.

---

## Prerequisites

| Requirement             | Notes                                                |
| ----------------------- | ---------------------------------------------------- |
| Python ≥ 3.11           | Tested on 3.11.x                                     |
| Binance Testnet account | Register at <https://testnet.binancefuture.com>      |
| Testnet API keys        | Generate a key pair in your testnet account settings |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/sumonelse/binance-futures-bot.git
cd binance-futures-bot

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your .env file
copy .env.example .env   # Windows
cp .env.example .env     # macOS / Linux
# Then open .env and fill in your Testnet API key and secret
```

---

## Usage

All commands are run via `cli.py`. Use `--help` to see all options:

```bash
python cli.py place-order --help
python cli.py cancel-order --help
python cli.py list-orders --help
```

### Place a MARKET order

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01
```

### Place a LIMIT order

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 95000
```

### Place a LIMIT order with custom time-in-force (IOC)

```bash
python cli.py place-order \
  --symbol ETHUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 1.0 \
  --price 3500 \
  --time-in-force IOC
```

Supported time-in-force values: `GTC` (Good Till Cancelled, default), `IOC` (Immediate Or Cancel), `FOK` (Fill Or Kill).

### Preview an order with dry-run (no submission)

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01 \
  --dry-run
```

The `--dry-run` flag validates the order and checks the symbol against live exchange info, but does **not** submit the order.

### Cancel an open order

```bash
python cli.py cancel-order \
  --symbol BTCUSDT \
  --order-id 3951920742
```

### List all open orders

```bash
python cli.py list-orders
```

Filter by symbol:

```bash
python cli.py list-orders --symbol BTCUSDT
```

---

## Sample Output

**Place Order - Pre-confirmation panel:**

```
╭─────────────────── 📋 Order Summary ─────────────────╮
│ 🟢 Side          :  BUY                              │
│ ⚡ Type          :  MARKET                            │
│ 💰 Symbol        :  BTCUSDT                           │
│ 📦 Quantity      :  0.01                              │
│ 💵 Price         :  Market Price                      │
╰──────────────────────────────────────────────────────╯
Confirm order placement? [y/N]: y
```

**Order Placed Successfully:**

```
                ✅ Order Placed Successfully
┌──────────────────┬───────────────────────┐
│ Field            │ Value                 │
├──────────────────┼───────────────────────┤
│ Timestamp        │ 2026-02-28 14:37:45   │
│ Order ID         │ 3951920742            │
│ Status           │ FILLED                │
│ Symbol           │ BTCUSDT               │
│ Side             │ BUY                   │
│ Type             │ MARKET                │
│ Executed Qty     │ 0.01                  │
│ Avg Price        │ 94823.5 USDT          │
│ Total Value      │ 948.24 USDT           │
└──────────────────┴───────────────────────┘
```

**List Open Orders:**

```
              📋 Open Orders — All Symbols
┌─────────┬──────────┬─────┬───────┬──────┬────┬──────────┬─────────┬───────────────────┐
│ Order   │ Symbol   │     │       │      │    │          │         │                   │
│ ID      │          │ Side│ Type  │ TIF  │Qty │ Price    │ Status  │ Placed At         │
├─────────┼──────────┼─────┼───────┼──────┼────┼──────────┼─────────┼───────────────────┤
│ 123456  │ BTCUSDT  │ BUY │ LIMIT │ GTC  │0.5 │ 45000 US │ NEW     │ 2026-02-28 14:25  │
│ 123457  │ ETHUSDT  │SELL │ LIMIT │ IOC  │2.0 │ 2800 USD │ NEW     │ 2026-02-28 14:30  │
└─────────┴──────────┴─────┴───────┴──────┴────┴──────────┴─────────┴───────────────────┘
2 open order(s) found.
```

---

## Project Structure

```
binance-futures-bot/
├── bot/
│   ├── __init__.py            # Package marker
│   ├── client.py              # Binance API client wrapper + symbol validation
│   ├── orders.py              # Order placement, cancellation, and listing logic
│   ├── validators.py          # Pydantic v2 OrderRequest and TimeInForce enums
│   └── logging_config.py      # Loguru sink configuration (file + console)
├── cli.py                     # Typer CLI entry point (3 commands)
├── logs/                      # Rotating log directory (created at runtime)
│   └── trading_bot.log        # Debug-level log file (10 MB rotation, 5 retained)
├── .env.example               # Template for BINANCE_API_KEY and BINANCE_API_SECRET
├── .gitignore                 # Excludes .env, logs/, __pycache__, .venv
├── README.md                  # This file
├── requirements.txt           # Pinned dependency versions
└── TODO.md                    # Completed and backlog tasks
```

---

## Features

- ✅ **MARKET and LIMIT orders** — both order types fully supported.
- ✅ **Configurable time-in-force (GTC/IOC/FOK)** — choose how your LIMIT orders behave.
- ✅ **Dry-run mode** — validate and preview orders without submitting to the exchange.
- ✅ **Symbol validation** — automatically checks if your trading pair exists on the testnet.
- ✅ **Order cancellation** — cancel any open order by symbol and order ID.
- ✅ **Order listing** — view all open orders, optionally filtered by symbol.
- ✅ **Input validation** — pydantic v2 enforces strict validation before any API call.
- ✅ **Comprehensive logging** — rotating file logs (`logs/trading_bot.log`) + styled console output.
- ✅ **Rich terminal UI** — styled panels, tables, and spinners for a professional experience.
- ✅ **Clean architecture** — strict layer separation (CLI → validators → client → API).

---

## Assumptions

- **Testnet only** — hard-coded to target `https://testnet.binancefuture.com`. No live exchange support.
- **LIMIT orders default to GTC** — use `--time-in-force IOC` or `FOK` to override.
- **Quantity precision is caller's responsibility** — Binance rejects orders violating `LOT_SIZE` filter.
- **Synchronous execution** — suitable for manual CLI use, not high-frequency trading.
- **Credentials in `.env` file** — no command-line API key flags to avoid shell history leakage.
- **Symbol validation is best-effort** — if the testnet is unreachable, validation is skipped with a warning.
