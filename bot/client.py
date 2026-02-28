"""
Binance Futures Testnet API client wrapper.

Responsible for authentication and producing a ready-to-use
``binance.client.Client`` instance pointed at the USDT-M Futures Testnet.
No business logic lives here — only connection setup.
"""

import os
from typing import Optional, Set

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException  # noqa: F401 — re-exported for callers
from dotenv import load_dotenv
from loguru import logger

# The public base URL for the Binance USDT-M Futures Testnet.
TESTNET_FUTURES_BASE_URL: str = "https://testnet.binancefuture.com"


def get_client() -> Client:
    """Create and return an authenticated Binance Futures Testnet client.

    Credentials are read from the environment (or a ``.env`` file loaded
    via ``python-dotenv``).  The returned client is pre-configured to call
    the Futures Testnet endpoint.

    Returns:
        Client: Authenticated ``python-binance`` client for the testnet.

    Raises:
        EnvironmentError: If ``BINANCE_API_KEY`` or ``BINANCE_API_SECRET``
            are absent from the environment.
        BinanceAPIException: Propagated from ``python-binance`` on auth
            failures or invalid key formats.
    """
    load_dotenv()

    api_key: Optional[str] = os.getenv("BINANCE_API_KEY")  # type: ignore[assignment]
    api_secret: Optional[str] = os.getenv("BINANCE_API_SECRET")  # type: ignore[assignment]

    if not api_key or not api_secret:
        raise EnvironmentError(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be defined in your .env file. "
            "Copy .env.example to .env and fill in your Testnet credentials."
        )

    logger.debug("Initialising Binance Futures Testnet client")

    client = Client(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True,
    )

    # Explicitly override the futures base URL to guarantee the testnet
    # endpoint is used regardless of python-binance version defaults.
    client.FUTURES_URL = TESTNET_FUTURES_BASE_URL + "/fapi"

    logger.debug(f"Binance client ready | futures_url={client.FUTURES_URL}")

    return client


def get_futures_symbols(client: Client) -> Set[str]:
    """Return the set of active USDT-M Futures symbols from exchange info.

    Fetches the exchange info endpoint and extracts every symbol whose
    status is ``"TRADING"``.  Used for pre-flight validation before an
    order is submitted.

    Args:
        client: Authenticated Binance client (from ``get_client``).

    Returns:
        A set of uppercase trading symbol strings, e.g. ``{"BTCUSDT", "ETHUSDT", ...}``.

    Raises:
        BinanceAPIException:     On API-level rejection.
        BinanceRequestException: On network / serialisation errors.
    """
    logger.debug("Fetching futures exchange info for symbol validation")
    info = client.futures_exchange_info()
    symbols: Set[str] = {
        s["symbol"]
        for s in info.get("symbols", [])
        if s.get("status") == "TRADING"
    }
    logger.debug(f"Fetched {len(symbols)} active futures symbols from exchange info")
    return symbols
