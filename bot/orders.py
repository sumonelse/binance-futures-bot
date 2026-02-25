"""
Order placement logic for Binance Futures Testnet.

Constructs and submits MARKET and LIMIT futures orders via the
authenticated client wrapper.  This module must not make direct API
calls — all network traffic goes through ``bot.client``.
"""

from typing import Any, Dict

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from loguru import logger

from bot.validators import OrderRequest, OrderType


def place_order(client: Client, order: OrderRequest) -> Dict[str, Any]:
    """Place a futures order on the Binance Testnet.

    Supports MARKET and LIMIT order types.  LIMIT orders use
    ``timeInForce=GTC`` (Good Till Cancelled).

    Args:
        client: Authenticated Binance client (from ``bot.client.get_client``).
        order:  Validated ``OrderRequest`` instance.

    Returns:
        Dict containing the raw Binance API response, including at minimum:
        ``orderId``, ``status``, ``executedQty``, ``avgPrice``.

    Raises:
        BinanceAPIException:    On API-level rejection from Binance.
        BinanceRequestException: On network / serialisation errors.
    """
    logger.info(
        "Placing order | symbol={} side={} type={} quantity={} price={}".format(
            order.symbol,
            order.side.value,
            order.order_type.value,
            order.quantity,
            order.price if order.price is not None else "N/A",
        )
    )

    try:
        if order.order_type == OrderType.MARKET:
            response: Dict[str, Any] = client.futures_create_order(
                symbol=order.symbol,
                side=order.side.value,
                type=order.order_type.value,
                quantity=order.quantity,
            )
        else:  # LIMIT
            response = client.futures_create_order(
                symbol=order.symbol,
                side=order.side.value,
                type=order.order_type.value,
                quantity=order.quantity,
                price=str(order.price),
                timeInForce="GTC",
            )
    except BinanceAPIException as exc:
        logger.error(
            f"Binance API error while placing order: {exc.message} "
            f"(code={exc.code})",
            exc_info=True,
        )
        raise
    except BinanceRequestException as exc:
        logger.error(
            f"Binance request error while placing order: {exc}",
            exc_info=True,
        )
        raise

    logger.info(
        "Order placed successfully | orderId={} status={} executedQty={}".format(
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
        )
    )

    return response
