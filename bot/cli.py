"""
CLI entry point — two modes:
  1. argparse flags (non-interactive / scriptable)
  2. interactive Rich menu (default when no flags passed)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Load .env file if present (python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass  # dotenv not installed — fall back to env vars / prompt

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box
from rich.rule import Rule
from rich.columns import Columns
from rich.style import Style

from .logging_config import setup_logging
from .client import BinanceFuturesClient
from .orders import OrderManager, OrderResult

console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────

def print_banner():
    banner = Text()
    banner.append("  ₿  Binance Futures Testnet Bot  ₿  ", style="bold yellow on dark_orange")
    console.print(Panel(banner, subtitle="[dim]USDT-M · Testnet[/]", border_style="yellow", padding=(0, 4)))
    console.print()


def print_order_summary(symbol: str, side: str, order_type: str, quantity: float, price: float | None = None, stop_price: float | None = None):
    t = Table(title="[bold]Order Request[/]", box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 2))
    t.add_column("Field",  style="bold cyan",  no_wrap=True)
    t.add_column("Value",  style="white")

    side_color = "green" if side.upper() == "BUY" else "red"
    t.add_row("Symbol",     symbol)
    t.add_row("Side",       f"[{side_color} bold]{side.upper()}[/]")
    t.add_row("Order Type", order_type.upper())
    t.add_row("Quantity",   str(quantity))
    if price:
        t.add_row("Price",  f"${price:,.4f}")
    if stop_price:
        t.add_row("Stop Price", f"${stop_price:,.4f}")

    console.print(t)


def print_order_result(result: OrderResult):
    if result.success:
        console.print(Rule("[bold green]✓ Order Placed Successfully[/]", style="green"))
        t = Table(box=box.SIMPLE_HEAVY, border_style="green", show_header=False, padding=(0, 2))
        t.add_column("Field", style="bold green", no_wrap=True)
        t.add_column("Value", style="white")

        t.add_row("Order ID",      str(result.order_id))
        t.add_row("Symbol",        result.symbol)
        t.add_row("Side",          result.side)
        t.add_row("Type",          result.order_type)
        t.add_row("Status",        f"[bold]{result.status}[/]")
        t.add_row("Orig Qty",      result.orig_qty)
        t.add_row("Executed Qty",  result.executed_qty)
        t.add_row("Avg Price",     result.avg_price if result.avg_price else "N/A")

        console.print(t)
    else:
        console.print(Rule("[bold red]✗ Order Failed[/]", style="red"))
        console.print(f"[red]  Error: {result.error}[/]")

    console.print()


def ask_credentials() -> tuple[str, str]:
    console.print("[bold cyan]Enter your Binance Testnet API credentials[/]")
    console.print("[dim]Tip: add BINANCE_API_KEY and BINANCE_API_SECRET to a [bold].env[/bold] file to skip this prompt.[/]\n")

    api_key    = os.environ.get("BINANCE_API_KEY")    or Prompt.ask("[bold]API Key[/]", password=True)
    api_secret = os.environ.get("BINANCE_API_SECRET") or Prompt.ask("[bold]API Secret[/]", password=True)

    if not api_key or not api_secret:
        console.print("[red]API credentials cannot be empty.[/]")
        sys.exit(1)

    return api_key.strip(), api_secret.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Non-interactive (argparse) mode
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance USDT-M Futures Testnet — place orders from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Market BUY
  python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --qty 0.01

  # Limit SELL
  python -m bot.cli --symbol ETHUSDT --side SELL --type LIMIT --qty 0.1 --price 3500

  # Stop-Market BUY
  python -m bot.cli --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.01 --stop-price 95000

  # Interactive mode (no flags)
  python -m bot.cli
""",
    )
    parser.add_argument("--symbol",      type=str,   help="Trading symbol (e.g. BTCUSDT)")
    parser.add_argument("--side",        type=str,   choices=["BUY", "SELL", "buy", "sell"], help="BUY or SELL")
    parser.add_argument("--type",        type=str,   choices=["MARKET", "LIMIT", "STOP_MARKET"], dest="order_type", help="Order type")
    parser.add_argument("--qty",         type=float, help="Quantity to trade")
    parser.add_argument("--price",       type=float, help="Limit price (required for LIMIT orders)")
    parser.add_argument("--stop-price",  type=float, help="Stop price (required for STOP_MARKET orders)", dest="stop_price")
    parser.add_argument("--api-key",     type=str,   help="Binance API key (or set BINANCE_API_KEY env var)")
    parser.add_argument("--api-secret",  type=str,   help="Binance API secret (or set BINANCE_API_SECRET env var)")
    parser.add_argument("--log-level",   type=str,   default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")
    return parser


def run_cli_mode(args: argparse.Namespace, manager: OrderManager):
    """Execute a single order from argparse flags and exit."""
    order_type = args.order_type.upper()

    print_order_summary(
        symbol=args.symbol,
        side=args.side,
        order_type=order_type,
        quantity=args.qty,
        price=args.price,
        stop_price=args.stop_price,
    )

    if order_type == "MARKET":
        result = manager.place_market_order(args.symbol, args.side, args.qty)

    elif order_type == "LIMIT":
        if not args.price:
            console.print("[red]--price is required for LIMIT orders.[/]")
            sys.exit(1)
        result = manager.place_limit_order(args.symbol, args.side, args.qty, args.price)

    elif order_type == "STOP_MARKET":
        if not args.stop_price:
            console.print("[red]--stop-price is required for STOP_MARKET orders.[/]")
            sys.exit(1)
        result = manager.place_stop_market_order(args.symbol, args.side, args.qty, args.stop_price)

    else:
        console.print(f"[red]Unsupported order type: {order_type}[/]")
        sys.exit(1)

    print_order_result(result)
    sys.exit(0 if result.success else 1)


# ──────────────────────────────────────────────────────────────────────────────
# Interactive mode
# ──────────────────────────────────────────────────────────────────────────────

def select_order_type() -> str:
    choices = {
        "1": ("MARKET",      "Execute immediately at current market price"),
        "2": ("LIMIT",       "Execute at a specific price or better"),
        "3": ("STOP_MARKET", "Trigger a market order when price hits stop level  [bonus]"),
    }
    console.print("[bold cyan]Order Type[/]")
    for k, (name, desc) in choices.items():
        console.print(f"  [{k}] [bold]{name}[/]  [dim]{desc}[/]")

    while True:
        choice = Prompt.ask("Choice", choices=list(choices), default="1")
        return choices[choice][0]


def run_interactive_mode(manager: OrderManager):
    """Full interactive REPL loop."""
    while True:
        console.print(Rule("[bold yellow]New Order[/]", style="yellow"))

        symbol     = Prompt.ask("[bold]Symbol[/]", default="BTCUSDT").strip().upper()
        side_raw   = Prompt.ask("[bold]Side[/]", choices=["BUY", "SELL", "buy", "sell"]).strip().upper()
        order_type = select_order_type()

        try:
            qty = float(Prompt.ask("[bold]Quantity[/]"))
        except ValueError:
            console.print("[red]Quantity must be a number.[/]")
            continue

        price: float | None      = None
        stop_price: float | None = None

        if order_type == "LIMIT":
            try:
                price = float(Prompt.ask("[bold]Limit price[/]"))
            except ValueError:
                console.print("[red]Price must be a number.[/]")
                continue

        elif order_type == "STOP_MARKET":
            try:
                stop_price = float(Prompt.ask("[bold]Stop price[/]"))
            except ValueError:
                console.print("[red]Stop price must be a number.[/]")
                continue

        console.print()
        print_order_summary(symbol, side_raw, order_type, qty, price, stop_price)

        if not Confirm.ask("[bold]Confirm and place order?[/]", default=True):
            console.print("[yellow]Order cancelled.[/]\n")
        else:
            with console.status("[bold green]Sending order to Binance...[/]", spinner="dots"):
                if order_type == "MARKET":
                    result = manager.place_market_order(symbol, side_raw, qty)
                elif order_type == "LIMIT":
                    result = manager.place_limit_order(symbol, side_raw, qty, price)
                else:
                    result = manager.place_stop_market_order(symbol, side_raw, qty, stop_price)

            print_order_result(result)

        if not Confirm.ask("Place another order?", default=True):
            console.print("\n[bold yellow]Goodbye! 👋[/]\n")
            break


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser  = build_parser()
    args    = parser.parse_args()

    logger  = setup_logging(args.log_level)

    print_banner()

    # ── Resolve credentials (.env → env vars → CLI flags → prompt) ───────
    api_key    = args.api_key    or os.environ.get("BINANCE_API_KEY")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        api_key, api_secret = ask_credentials()

    # ── Initialise client & order manager ─────────────────────────────────
    try:
        client  = BinanceFuturesClient(api_key, api_secret, testnet=True)
        manager = OrderManager(client)
    except ValueError as exc:
        console.print(f"[red]Initialisation error: {exc}[/]")
        sys.exit(1)

    # ── Connectivity check ─────────────────────────────────────────────────
    with console.status("Connecting to Binance Testnet...", spinner="dots"):
        reachable = client.ping()

    if reachable:
        console.print("[green]✓ Connected to Binance Futures Testnet[/]\n")
    else:
        console.print("[red]✗ Cannot reach Binance Testnet — check your network / API key.[/]\n")

    # ── Choose mode ────────────────────────────────────────────────────────
    is_cli_mode = args.symbol and args.side and args.order_type and args.qty

    if is_cli_mode:
        run_cli_mode(args, manager)
    else:
        try:
            run_interactive_mode(manager)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Bye![/]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
