"""
CLI entry point for binance-futures-bot.

Uses Typer for argument parsing and Rich for styled terminal output.
This module must not contain validation or API logic — it delegates
entirely to bot.validators, bot.client, and bot.orders.
"""

from typing import Optional

import requests
import typer
from binance.exceptions import BinanceAPIException, BinanceRequestException
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.client import get_client
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import OrderRequest

# Initialise logging before any other module-level code runs.
setup_logging()

app = typer.Typer(
    name="binance-futures-bot",
    help="Place MARKET and LIMIT orders on the Binance USDT-M Futures Testnet.",
    add_completion=False,
)

console = Console()


@app.callback()
def main() -> None:
    """Binance USDT-M Futures Testnet trading bot."""


@app.command("place-order")
def place_order_cmd(
    symbol: str = typer.Option(
        ...,
        "--symbol",
        "-s",
        help="Trading pair symbol, e.g. BTCUSDT",
    ),
    side: str = typer.Option(
        ...,
        "--side",
        help="Order side: BUY or SELL",
    ),
    order_type: str = typer.Option(
        ...,
        "--type",
        "-t",
        help="Order type: MARKET or LIMIT",
    ),
    quantity: float = typer.Option(
        ...,
        "--quantity",
        "-q",
        help="Order quantity — must be greater than zero",
    ),
    price: Optional[float] = typer.Option(
        None,
        "--price",
        "-p",
        help="Limit price — required for LIMIT orders, must be greater than zero",
    ),
) -> None:
    """Place a MARKET or LIMIT futures order on the Binance Testnet."""

    # ------------------------------------------------------------------
    # 1. Validate inputs with Pydantic.
    # ------------------------------------------------------------------
    try:
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValidationError as exc:
        error_lines = "\n".join(
            f"[bold]{e['loc'][0]}[/bold]: {e['msg']}" for e in exc.errors()
        )
        console.print(
            Panel(
                error_lines,
                title="[red]Validation Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 2. Display a confirmation panel and prompt the user.
    # ------------------------------------------------------------------
    summary = (
        f"[bold]Symbol   :[/bold]  {order.symbol}\n"
        f"[bold]Side     :[/bold]  {order.side.value}\n"
        f"[bold]Type     :[/bold]  {order.order_type.value}\n"
        f"[bold]Quantity :[/bold]  {order.quantity}\n"
        f"[bold]Price    :[/bold]  {order.price if order.price is not None else 'N/A (Market order)'}"
    )
    console.print(
        Panel(summary, title="[cyan]Order Summary[/cyan]", border_style="cyan")
    )

    confirmed: bool = typer.confirm("Confirm order placement?", default=False)
    if not confirmed:
        console.print("[yellow]Order cancelled by user.[/yellow]")
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # 3. Place the order and handle errors gracefully.
    # ------------------------------------------------------------------
    try:
        client = get_client()
        result = place_order(client, order)
    except EnvironmentError as exc:
        console.print(
            Panel(str(exc), title="[red]Configuration Error[/red]", border_style="red")
        )
        raise typer.Exit(code=1)
    except BinanceAPIException as exc:
        console.print(
            Panel(
                f"Binance API returned an error:\n{exc.message} (code {exc.code})",
                title="[red]API Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)
    except BinanceRequestException as exc:
        console.print(
            Panel(
                f"A request error occurred:\n{exc}",
                title="[red]Request Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)
    except requests.exceptions.ConnectionError:
        console.print(
            Panel(
                "Could not reach Binance Testnet. "
                "Please check your internet connection and try again.",
                title="[red]Connection Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 4. Display the result as a Rich table.
    # ------------------------------------------------------------------
    table = Table(title=":white_check_mark: Order Placed Successfully", border_style="green")
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(result.get("orderId", "N/A")))
    table.add_row("Status", str(result.get("status", "N/A")))
    table.add_row("Symbol", str(result.get("symbol", "N/A")))
    table.add_row("Side", str(result.get("side", "N/A")))
    table.add_row("Type", str(result.get("type", "N/A")))
    table.add_row("Executed Qty", str(result.get("executedQty", "N/A")))
    table.add_row("Avg Price", str(result.get("avgPrice", "N/A")))

    console.print(table)


if __name__ == "__main__":
    app()
