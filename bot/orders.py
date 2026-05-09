"""
Order placement logic — sits between the CLI and the API client.
Validates inputs, builds request payloads, and returns normalised results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .client import BinanceFuturesClient, BinanceClientError
from .validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderResult:
    """Normalised view of a Binance order response."""
    success: bool
    order_id: int | None        = None
    symbol: str                 = ""
    side: str                   = ""
    order_type: str             = ""
    status: str                 = ""
    orig_qty: str               = ""
    executed_qty: str           = ""
    avg_price: str              = ""
    price: str                  = ""
    raw: dict                   = field(default_factory=dict)
    error: str                  = ""

    @classmethod
    def from_response(cls, data: dict) -> "OrderResult":
        return cls(
            success      = True,
            order_id     = data.get("orderId"),
            symbol       = data.get("symbol", ""),
            side         = data.get("side", ""),
            order_type   = data.get("type", ""),
            status       = data.get("status", ""),
            orig_qty     = data.get("origQty", ""),
            executed_qty = data.get("executedQty", ""),
            avg_price    = data.get("avgPrice", data.get("price", "N/A")),
            price        = data.get("price", ""),
            raw          = data,
        )

    @classmethod
    def from_error(cls, error: str) -> "OrderResult":
        return cls(success=False, error=error)


class OrderManager:
    """
    High-level order manager.
    Validates all inputs, delegates to BinanceFuturesClient, and returns OrderResult.
    """

    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    # ──────────────────────────────────────────────────────────────────────
    # Public helpers
    # ──────────────────────────────────────────────────────────────────────

    def place_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        """Place a MARKET order (no price required)."""
        try:
            symbol   = validate_symbol(symbol)
            side     = validate_side(side)
            quantity = validate_quantity(quantity)
        except ValueError as exc:
            logger.warning("Validation failed for MARKET order: %s", exc)
            return OrderResult.from_error(str(exc))

        logger.info("MARKET %s | %s | qty=%s", side, symbol, quantity)

        return self._execute(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )

    def place_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> OrderResult:
        """Place a LIMIT order with GTC time-in-force."""
        try:
            symbol   = validate_symbol(symbol)
            side     = validate_side(side)
            quantity = validate_quantity(quantity)
            price    = validate_price(price)
        except ValueError as exc:
            logger.warning("Validation failed for LIMIT order: %s", exc)
            return OrderResult.from_error(str(exc))

        logger.info("LIMIT %s | %s | qty=%s | price=%s", side, symbol, quantity, price)

        return self._execute(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce="GTC",
        )

    def place_stop_market_order(
        self, symbol: str, side: str, quantity: float, stop_price: float
    ) -> OrderResult:
        """Place a STOP_MARKET order (bonus order type)."""
        try:
            symbol     = validate_symbol(symbol)
            side       = validate_side(side)
            quantity   = validate_quantity(quantity)
            stop_price = validate_price(stop_price)
        except ValueError as exc:
            logger.warning("Validation failed for STOP_MARKET order: %s", exc)
            return OrderResult.from_error(str(exc))

        logger.info("STOP_MARKET %s | %s | qty=%s | stopPrice=%s", side, symbol, quantity, stop_price)

        return self._execute(
            symbol=symbol,
            side=side,
            type="STOP_MARKET",
            quantity=quantity,
            stopPrice=stop_price,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────

    def _execute(self, **kwargs) -> OrderResult:
        try:
            data = self.client.create_order(**kwargs)
            return OrderResult.from_response(data)
        except BinanceClientError as exc:
            logger.error("Binance API error | code=%s | msg=%s", exc.code, exc.message)
            return OrderResult.from_error(f"[{exc.code}] {exc.message}")
        except ConnectionError as exc:
            logger.error("Connection error: %s", exc)
            return OrderResult.from_error(f"Network error: {exc}")
        except TimeoutError as exc:
            logger.error("Timeout: %s", exc)
            return OrderResult.from_error(f"Timeout: {exc}")
        except Exception as exc:
            logger.exception("Unexpected error placing order")
            return OrderResult.from_error(f"Unexpected error: {exc}")
