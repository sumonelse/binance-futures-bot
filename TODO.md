# TODO

## In Progress

_(none)_

## Completed

- [x] Scaffold full project structure (bot/, cli.py, .env.example, .gitignore, README.md, TODO.md)
- [x] Implement `bot/logging_config.py` — Loguru file + console sinks
- [x] Implement `bot/validators.py` — Pydantic v2 `OrderRequest` model with `model_validator`
- [x] Implement `bot/client.py` — Binance Futures Testnet client wrapper with `.env` credentials
- [x] Implement `bot/orders.py` — `place_order` function for MARKET and LIMIT orders
- [x] Implement `cli.py` — Typer CLI with Rich Panel confirmation and Rich Table result output
- [x] Create `README.md` with full usage documentation and sample output
- [x] Create `.env.example` with placeholder credentials
- [x] Generate `requirements.txt` with pinned package versions
- [x] Improve CLI UX with order-placement spinner feedback
- [x] Enhance order summary UI with emojis and estimated value display
- [x] Improve validation error UX with clearer field messages and tips
- [x] Improve result table formatting for quantities and prices
- [x] Add timestamp and total order value to success output

## Backlog

- [ ] Add `--dry-run` flag to preview order without submitting
- [ ] Add support for additional `timeInForce` values (IOC, FOK)
- [ ] Add `cancel-order` command to cancel an open order by ID
- [ ] Add `list-orders` command to display open futures positions
- [ ] Add input validation for symbol existence against exchange info
