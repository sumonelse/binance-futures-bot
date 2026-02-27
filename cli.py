"""
CLI entry point for binance-futures-bot.

Uses Typer for argument parsing and Rich for styled terminal output.
This module must not contain validation or API logic — it delegates
entirely to bot.validators, bot.client, and bot.orders.
"""

from datetime import datetime
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
        error_messages = []
        for e in exc.errors():
            field = e['loc'][0]
            msg = e['msg']
            error_messages.append(f"  [bold red]✗[/bold red] [bold]{field}[/bold]: {msg}")
        
        error_text = "\n".join(error_messages)
        error_text += "\n\n[dim]💡 Tip: Use --help to see all available options and requirements[/dim]"
        
        console.print(
            Panel(
                error_text,
                title="[red]❌ Validation Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 2. Display a confirmation panel and prompt the user.
    # ------------------------------------------------------------------
    side_emoji = "🟢" if order.side.value == "BUY" else "🔴"
    type_emoji = "⚡" if order.order_type.value == "MARKET" else "📊"
    
    summary = (
        f"{side_emoji} [bold]Side     :[/bold]  {order.side.value}\n"
        f"{type_emoji} [bold]Type     :[/bold]  {order.order_type.value}\n"
        f"💰 [bold]Symbol   :[/bold]  {order.symbol}\n"
        f"📦 [bold]Quantity :[/bold]  {order.quantity}\n"
    )
    
    if order.price is not None:
        summary += f"💵 [bold]Price    :[/bold]  {order.price}\n"
        estimated_value = order.price * order.quantity
        summary += f"💎 [bold]Est. Value:[/bold]  {estimated_value:.2f} USDT"
    else:
        summary += f"💵 [bold]Price    :[/bold]  Market Price"
    
    console.print(
        Panel(summary, title="[bold cyan]📋 Order Summary[/bold cyan]", border_style="cyan")
    )

    confirmed: bool = typer.confirm("Confirm order placement?", default=False)
    if not confirmed:
        console.print("[yellow]Order cancelled by user.[/yellow]")
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # 3. Place the order and handle errors gracefully.
    # ------------------------------------------------------------------
    try:
        with console.status("[bold cyan]Placing order...", spinner="dots"):
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
    table = Table(title="✅ Order Placed Successfully", border_style="green", title_style="bold green")
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table.add_row("Timestamp", f"[dim]{timestamp}[/dim]")
    
    table.add_row("Order ID", str(result.get("orderId", "N/A")))
    table.add_row("Status", f"[bold green]{result.get('status', 'N/A')}[/bold green]")
    table.add_row("Symbol", str(result.get("symbol", "N/A")))
    
    side_value = str(result.get("side", "N/A"))
    side_color = "green" if side_value == "BUY" else "red"
    table.add_row("Side", f"[bold {side_color}]{side_value}[/bold {side_color}]")
    
    table.add_row("Type", str(result.get("type", "N/A")))
    
    # Format executed quantity with proper decimals
    executed_qty = result.get("executedQty", "0")
    try:
        executed_qty_float = float(executed_qty)
        formatted_qty = f"{executed_qty_float:.8f}".rstrip('0').rstrip('.')
        table.add_row("Executed Qty", formatted_qty)
    except (ValueError, TypeError):
        table.add_row("Executed Qty", str(executed_qty))
    
    # Format average price with proper decimals
    avg_price = result.get("avgPrice", "0")
    try:
        avg_price_float = float(avg_price)
        if avg_price_float > 0:
            formatted_price = f"{avg_price_float:.4f}".rstrip('0').rstrip('.')
            table.add_row("Avg Price", f"{formatted_price} USDT")
        else:
            table.add_row("Avg Price", "N/A")
    except (ValueError, TypeError):
        table.add_row("Avg Price", str(avg_price))
    
    # Calculate and display total order value
    try:
        qty = float(executed_qty)
        price = float(avg_price)
        if qty > 0 and price > 0:
            total_value = qty * price
            table.add_row("Total Value", f"[bold]{total_value:.2f}[/bold] USDT")
    except (ValueError, TypeError):
        pass

    console.print(table)


if __name__ == "__main__":
    app()
