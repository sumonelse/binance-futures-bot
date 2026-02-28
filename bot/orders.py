"""
Order placement logic for Binance Futures Testnet.

Constructs and submits MARKET and LIMIT futures orders via the
authenticated client wrapper.  This module must not make direct API
calls — all network traffic goes through ``bot.client``.
"""

from typing import Any, Dict, List, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from loguru import logger

from bot.validators import OrderRequest, OrderType


def place_order(client: Client, order: OrderRequest) -> Dict[str, Any]:
    """Place a futures order on the Binance Testnet.

    Supports MARKET and LIMIT order types.  LIMIT orders use the
    ``time_in_force`` value from the ``OrderRequest`` (GTC, IOC, or FOK).

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
        "Placing order | symbol={} side={} type={} quantity={} price={} tif={}".format(
            order.symbol,
            order.side.value,
            order.order_type.value,
            order.quantity,
            order.price if order.price is not None else "N/A",
            order.time_in_force.value if order.order_type == OrderType.LIMIT else "N/A",
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
                timeInForce=order.time_in_force.value,
            )
    except BinanceAPIException as exc:
        logger.opt(exception=True).error(
            f"Binance API error while placing order: {exc.message} (code={exc.code})"
        )
        raise
    except BinanceRequestException as exc:
        logger.opt(exception=True).error(
            f"Binance request error while placing order: {exc}"
        )
        raise

    logger.info(
        "Order placed successfully | orderId={} status={} executedQty={} avgPrice={}".format(
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice", "N/A"),
        )
    )

    return response


def cancel_order(client: Client, symbol: str, order_id: int) -> Dict[str, Any]:
    """Cancel an open futures order by symbol and order ID.

    Args:
        client:   Authenticated Binance client.
        symbol:   Trading pair symbol, e.g. ``BTCUSDT``.
        order_id: The numeric ID of the order to cancel.

    Returns:
        Dict containing the raw Binance API response with the cancelled
        order details, including ``orderId``, ``status``, ``symbol``, etc.

    Raises:
        BinanceAPIException:     If the order cannot be found or cancelled.
        BinanceRequestException: On network / serialisation errors.
    """
    logger.info(f"Cancelling order | symbol={symbol} orderId={order_id}")

    try:
        response: Dict[str, Any] = client.futures_cancel_order(
            symbol=symbol,
            orderId=order_id,
        )
    except BinanceAPIException as exc:
        logger.opt(exception=True).error(
            f"Binance API error while cancelling order {order_id}: {exc.message} (code={exc.code})"
        )
        raise
    except BinanceRequestException as exc:
        logger.opt(exception=True).error(
            f"Binance request error while cancelling order {order_id}: {exc}"
        )
        raise

    logger.info(
        "Order cancelled successfully | orderId={} status={}".format(
            response.get("orderId"),
            response.get("status"),
        )
    )

    return response


def get_open_orders(
    client: Client,
    symbol: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all open futures orders, optionally filtered by symbol.

    Args:
        client: Authenticated Binance client.
        symbol: Optional trading pair to filter results, e.g. ``BTCUSDT``.
                If ``None``, open orders for all symbols are returned.

    Returns:
        List of dicts, each representing an open order with fields such as
        ``orderId``, ``symbol``, ``side``, ``type``, ``origQty``, ``price``,
        ``status``, and ``time``.

    Raises:
        BinanceAPIException:     On API-level rejection.
        BinanceRequestException: On network / serialisation errors.
    """
    log_symbol = symbol if symbol is not None else "ALL"
    logger.info(f"Fetching open orders | symbol={log_symbol}")

    try:
        kwargs: Dict[str, Any] = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        orders: List[Dict[str, Any]] = client.futures_get_open_orders(**kwargs)  # type: ignore[assignment]
    except BinanceAPIException as exc:
        logger.opt(exception=True).error(
            f"Binance API error while fetching open orders: {exc.message} (code={exc.code})"
        )
        raise
    except BinanceRequestException as exc:
        logger.opt(exception=True).error(
            f"Binance request error while fetching open orders: {exc}"
        )
        raise

    logger.info(f"Fetched {len(orders)} open order(s) | symbol={log_symbol}")
    return orders
