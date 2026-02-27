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

All commands are run via `cli.py`:

```bash
python cli.py place-order --help
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

---

## Sample Output

```
╭──────────────── Order Summary ─────────────────╮
│ Symbol   :  BTCUSDT                             │
│ Side     :  BUY                                 │
│ Type     :  MARKET                              │
│ Quantity :  0.01                                │
│ Price    :  N/A (Market order)                  │
╰─────────────────────────────────────────────────╯
Confirm order placement? [y/N]: y

           ✅ Order Placed Successfully
┌──────────────┬──────────────────────┐
│ Field        │ Value                │
├──────────────┼──────────────────────┤
│ Order ID     │ 3951920742           │
│ Status       │ FILLED               │
│ Symbol       │ BTCUSDT              │
│ Side         │ BUY                  │
│ Type         │ MARKET               │
│ Executed Qty │ 0.010                │
│ Avg Price    │ 94823.50             │
└──────────────┴──────────────────────┘
```

---

## Project Structure

```
binance-futures-bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance API client wrapper (auth + testnet URL)
│   ├── orders.py            # Order placement logic
│   ├── validators.py        # Pydantic v2 OrderRequest model
│   └── logging_config.py   # Loguru sink configuration
├── cli.py                   # Typer CLI entry point
├── .env.example             # Template for API credentials
├── .gitignore
├── README.md
├── requirements.txt
└── TODO.md
```

---

## Assumptions

1. **Testnet only** — this bot is hard-coded to target `https://testnet.binancefuture.com`.
   It will not place orders on the live exchange.
2. **LIMIT orders use GTC** (`timeInForce=GTC`). Other time-in-force values are not
   exposed via the CLI at this time.
3. **Quantity precision** is the caller's responsibility — the bot passes the value
   directly to the API. Binance will reject orders that violate the symbol's
   `LOT_SIZE` filter.
4. **Synchronous** — no async/threading. Suitable for manual CLI use, not
   high-frequency automated trading.
5. **Credentials** are loaded exclusively from a `.env` file; no command-line flags
   for API keys are provided to avoid accidental exposure in shell history.
