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

from bot.client import get_client, get_futures_symbols
from bot.logging_config import setup_logging
from bot.orders import cancel_order, get_open_orders, place_order
from bot.validators import OrderRequest, TimeInForce

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
    time_in_force: TimeInForce = typer.Option(
        TimeInForce.GTC,
        "--time-in-force",
        "-f",
        help="Time-in-force for LIMIT orders: GTC (default), IOC, or FOK",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and preview the order without submitting it to the exchange",
        is_flag=True,
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
            time_in_force=time_in_force,
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
    # 2. Display a confirmation / preview panel.
    # ------------------------------------------------------------------
    side_emoji = "🟢" if order.side.value == "BUY" else "🔴"
    type_emoji = "⚡" if order.order_type.value == "MARKET" else "📊"

    summary = (
        f"{side_emoji} [bold]Side          :[/bold]  {order.side.value}\n"
        f"{type_emoji} [bold]Type          :[/bold]  {order.order_type.value}\n"
        f"💰 [bold]Symbol        :[/bold]  {order.symbol}\n"
        f"📦 [bold]Quantity      :[/bold]  {order.quantity}\n"
    )

    if order.price is not None:
        summary += f"💵 [bold]Price         :[/bold]  {order.price}\n"
        summary += f"⏱  [bold]Time-in-Force :[/bold]  {order.time_in_force.value}\n"
        estimated_value = order.price * order.quantity
        summary += f"💎 [bold]Est. Value    :[/bold]  {estimated_value:.2f} USDT"
    else:
        summary += f"💵 [bold]Price         :[/bold]  Market Price"

    panel_title = (
        "[bold yellow]🔍 Dry Run — Order Preview[/bold yellow]"
        if dry_run
        else "[bold cyan]📋 Order Summary[/bold cyan]"
    )
    border = "yellow" if dry_run else "cyan"
    console.print(Panel(summary, title=panel_title, border_style=border))

    # ------------------------------------------------------------------
    # 3. Dry-run: exit without submitting (no network calls required).
    # ------------------------------------------------------------------
    if dry_run:
        console.print(
            Panel(
                "✅ [bold green]All validations passed.[/bold green]\n\n"
                "[dim]This was a dry run — no order was submitted to the exchange.\n"
                "Remove [bold]--dry-run[/bold] to place the order for real.[/dim]",
                title="[yellow]Dry Run Complete[/yellow]",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # 4. Obtain an authenticated client and validate the symbol.
    # ------------------------------------------------------------------
    try:
        with console.status("[bold cyan]Connecting to Binance Testnet...", spinner="dots"):
            client = get_client()
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

    # Validate symbol against live exchange info (best-effort).
    try:
        with console.status(
            f"[bold cyan]Validating symbol [bold]{order.symbol}[/bold]...",
            spinner="dots",
        ):
            valid_symbols = get_futures_symbols(client)
    except (BinanceAPIException, BinanceRequestException, requests.exceptions.ConnectionError):
        console.print(
            "[yellow]⚠ Could not fetch exchange info — skipping symbol validation.[/yellow]"
        )
        valid_symbols = None

    if valid_symbols is not None and order.symbol not in valid_symbols:
        console.print(
            Panel(
                f"[bold]{order.symbol}[/bold] is not a recognised active USDT-M Futures "
                f"symbol on the Binance Testnet.\n\n"
                "[dim]💡 Tip: Check spelling and ensure the pair is listed on the "
                "Binance Futures Testnet.[/dim]",
                title="[red]❌ Unknown Symbol[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 5. Ask for explicit confirmation.
    # ------------------------------------------------------------------
    confirmed: bool = typer.confirm("Confirm order placement?", default=False)
    if not confirmed:
        console.print("[yellow]Order cancelled by user.[/yellow]")
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # 6. Place the order and handle errors gracefully.
    # ------------------------------------------------------------------
    try:
        with console.status("[bold cyan]Placing order...", spinner="dots"):
            result = place_order(client, order)
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

    # ------------------------------------------------------------------
    # 7. Display the result as a Rich table.
    # ------------------------------------------------------------------
    table = Table(
        title="✅ Order Placed Successfully",
        border_style="green",
        title_style="bold green",
    )
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table.add_row("Timestamp", f"[dim]{timestamp}[/dim]")
    table.add_row("Order ID", str(result.get("orderId", "N/A")))
    table.add_row("Status", f"[bold green]{result.get('status', 'N/A')}[/bold green]")
    table.add_row("Symbol", str(result.get("symbol", "N/A")))

    side_value = str(result.get("side", "N/A"))
    side_color = "green" if side_value == "BUY" else "red"
    table.add_row("Side", f"[bold {side_color}]{side_value}[/bold {side_color}]")
    table.add_row("Type", str(result.get("type", "N/A")))

    tif_value = result.get("timeInForce", "N/A")
    if tif_value != "N/A":
        table.add_row("Time-in-Force", str(tif_value))

    executed_qty = result.get("executedQty", "0")
    try:
        executed_qty_float = float(executed_qty)
        formatted_qty = f"{executed_qty_float:.8f}".rstrip("0").rstrip(".")
        table.add_row("Executed Qty", formatted_qty)
    except (ValueError, TypeError):
        table.add_row("Executed Qty", str(executed_qty))

    avg_price = result.get("avgPrice", "0")
    try:
        avg_price_float = float(avg_price)
        if avg_price_float > 0:
            formatted_price = f"{avg_price_float:.4f}".rstrip("0").rstrip(".")
            table.add_row("Avg Price", f"{formatted_price} USDT")
        else:
            table.add_row("Avg Price", "N/A")
    except (ValueError, TypeError):
        table.add_row("Avg Price", str(avg_price))

    try:
        qty = float(executed_qty)
        price_val = float(avg_price)
        if qty > 0 and price_val > 0:
            total_value = qty * price_val
            table.add_row("Total Value", f"[bold]{total_value:.2f}[/bold] USDT")
    except (ValueError, TypeError):
        pass

    console.print(table)


@app.command("cancel-order")
def cancel_order_cmd(
    symbol: str = typer.Option(
        ...,
        "--symbol",
        "-s",
        help="Trading pair symbol of the order to cancel, e.g. BTCUSDT",
    ),
    order_id: int = typer.Option(
        ...,
        "--order-id",
        "-i",
        help="Numeric order ID to cancel",
    ),
) -> None:
    """Cancel an open futures order by symbol and order ID."""

    symbol = symbol.upper()

    # ------------------------------------------------------------------
    # Confirmation prompt.
    # ------------------------------------------------------------------
    console.print(
        Panel(
            f"🗑  [bold]Symbol  :[/bold]  {symbol}\n"
            f"🔢 [bold]Order ID:[/bold]  {order_id}",
            title="[bold red]⚠ Cancel Order[/bold red]",
            border_style="red",
        )
    )

    confirmed: bool = typer.confirm("Confirm cancellation?", default=False)
    if not confirmed:
        console.print("[yellow]Cancellation aborted by user.[/yellow]")
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # Execute cancellation.
    # ------------------------------------------------------------------
    try:
        with console.status("[bold red]Cancelling order...", spinner="dots"):
            client = get_client()
            result = cancel_order(client, symbol, order_id)
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
            Panel(f"A request error occurred:\n{exc}", title="[red]Request Error[/red]", border_style="red")
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Display result.
    # ------------------------------------------------------------------
    table = Table(
        title="✅ Order Cancelled Successfully",
        border_style="green",
        title_style="bold green",
    )
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(result.get("orderId", "N/A")))
    table.add_row("Status", f"[bold]{result.get('status', 'N/A')}[/bold]")
    table.add_row("Symbol", str(result.get("symbol", "N/A")))

    side_value = str(result.get("side", "N/A"))
    side_color = "green" if side_value == "BUY" else "red"
    table.add_row("Side", f"[bold {side_color}]{side_value}[/bold {side_color}]")

    table.add_row("Type", str(result.get("type", "N/A")))

    orig_qty = result.get("origQty", "N/A")
    try:
        formatted_orig = f"{float(orig_qty):.8f}".rstrip("0").rstrip(".")
        table.add_row("Orig Qty", formatted_orig)
    except (ValueError, TypeError):
        table.add_row("Orig Qty", str(orig_qty))

    cancel_price = result.get("price", "0")
    try:
        cancel_price_float = float(cancel_price)
        if cancel_price_float > 0:
            table.add_row("Price", f"{cancel_price_float:.4f}".rstrip("0").rstrip(".") + " USDT")
        else:
            table.add_row("Price", "Market")
    except (ValueError, TypeError):
        table.add_row("Price", str(cancel_price))

    console.print(table)


@app.command("list-orders")
def list_orders_cmd(
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol",
        "-s",
        help="Filter open orders by trading pair symbol, e.g. BTCUSDT",
    ),
) -> None:
    """List all open futures orders, optionally filtered by symbol."""

    filter_symbol = symbol.upper() if symbol else None

    # ------------------------------------------------------------------
    # Fetch open orders.
    # ------------------------------------------------------------------
    try:
        with console.status(
            "[bold cyan]Fetching open orders...",
            spinner="dots",
        ):
            client = get_client()
            orders = get_open_orders(client, filter_symbol)
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
            Panel(f"A request error occurred:\n{exc}", title="[red]Request Error[/red]", border_style="red")
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Display results.
    # ------------------------------------------------------------------
    if not orders:
        scope = f"[bold]{filter_symbol}[/bold]" if filter_symbol else "all symbols"
        console.print(
            Panel(
                f"No open orders found for {scope}.",
                title="[cyan]Open Orders[/cyan]",
                border_style="cyan",
            )
        )
        raise typer.Exit(code=0)

    scope_label = filter_symbol if filter_symbol else "All Symbols"
    table = Table(
        title=f"📋 Open Orders — {scope_label}",
        border_style="cyan",
        title_style="bold cyan",
    )
    table.add_column("Order ID", style="bold", no_wrap=True)
    table.add_column("Symbol", no_wrap=True)
    table.add_column("Side", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("TIF", no_wrap=True)
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Status", no_wrap=True)
    table.add_column("Placed At")

    for o in orders:
        side_val = str(o.get("side", "N/A"))
        side_color = "green" if side_val == "BUY" else "red"
        side_cell = f"[bold {side_color}]{side_val}[/bold {side_color}]"

        raw_price = o.get("price", "0")
        try:
            price_float = float(raw_price)
            price_cell = (
                f"{price_float:.4f}".rstrip("0").rstrip(".") + " USDT"
                if price_float > 0
                else "Market"
            )
        except (ValueError, TypeError):
            price_cell = str(raw_price)

        raw_qty = o.get("origQty", "0")
        try:
            qty_cell = f"{float(raw_qty):.8f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            qty_cell = str(raw_qty)

        raw_time = o.get("time", 0)
        try:
            placed_at = datetime.fromtimestamp(int(raw_time) / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            placed_at = str(raw_time)

        table.add_row(
            str(o.get("orderId", "N/A")),
            str(o.get("symbol", "N/A")),
            side_cell,
            str(o.get("type", "N/A")),
            str(o.get("timeInForce", "N/A")),
            qty_cell,
            price_cell,
            str(o.get("status", "N/A")),
            placed_at,
        )

    console.print(table)
    console.print(f"[dim]{len(orders)} open order(s) found.[/dim]")


if __name__ == "__main__":
    app()
