"""
Pydantic v2 validation models for order requests.

Defines enumerations and the OrderRequest model that enforces all
business rules before any API call is made.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class OrderSide(str, Enum):
    """Valid order sides for Binance Futures."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Supported order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderRequest(BaseModel):
    """Validated order request for Binance Futures Testnet.

    Attributes:
        symbol:     Trading pair in uppercase, e.g. ``BTCUSDT``.
        side:       ``BUY`` or ``SELL``.
        order_type: ``MARKET`` or ``LIMIT``.
        quantity:   Order quantity; must be greater than zero.
        price:      Limit price; required when ``order_type`` is ``LIMIT``,
                    must be greater than zero.
    """

    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol, e.g. BTCUSDT",
    )
    side: OrderSide = Field(
        ...,
        description="Order side: BUY or SELL",
    )
    order_type: OrderType = Field(
        ...,
        description="Order type: MARKET or LIMIT",
    )
    quantity: float = Field(
        ...,
        gt=0,
        description="Order quantity — must be greater than zero",
    )
    price: Optional[float] = Field(
        None,
        gt=0,
        description="Limit price — required for LIMIT orders, must be greater than zero",
    )

    @model_validator(mode="after")
    def price_required_for_limit(self) -> "OrderRequest":
        """Ensure that a price is provided when order_type is LIMIT."""
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError(
                "price is required when order_type is LIMIT — provide --price <value>"
            )
        return self

    def model_post_init(self, __context: object) -> None:
        """Normalise symbol to uppercase after initialisation."""
        self.symbol = self.symbol.upper()
