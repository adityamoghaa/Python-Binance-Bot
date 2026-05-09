"""
Input validation for trading parameters.
All validators raise ValueError with human-friendly messages on bad input.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

# Minimum notional / quantity guardrails (conservative; actual limits come from exchange)
MIN_QUANTITY = 0.001
MAX_QUANTITY = 1_000_000


def validate_symbol(symbol: str) -> str:
    """Ensure symbol is a non-empty uppercase string (e.g. BTCUSDT)."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' contains invalid characters. Use alphanumeric only (e.g. BTCUSDT).")
    return symbol


def validate_side(side: str) -> str:
    """Return normalised side string: 'BUY' or 'SELL'."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")
    return side


def validate_order_type(order_type: str) -> str:
    """Return normalised order type."""
    order_type = order_type.strip().upper().replace("-", "_")
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'."
        )
    return order_type


def validate_quantity(quantity: float | str) -> float:
    """Ensure quantity is a positive finite number within sane bounds."""
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(f"Quantity must be a numeric value, got '{quantity}'.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0, got {qty}.")
    if qty < MIN_QUANTITY:
        raise ValueError(f"Quantity {qty} is below minimum allowed ({MIN_QUANTITY}).")
    if qty > MAX_QUANTITY:
        raise ValueError(f"Quantity {qty} exceeds maximum allowed ({MAX_QUANTITY}).")
    return qty


def validate_price(price: float | str) -> float:
    """Ensure price is a positive finite number (used for LIMIT & stop price)."""
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValueError(f"Price must be a numeric value, got '{price}'.")
    if p <= 0:
        raise ValueError(f"Price must be greater than 0, got {p}.")
    return p
