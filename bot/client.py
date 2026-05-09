"""
Binance Futures Testnet client wrapper.
Handles authentication, session management, and raw API communication.
All methods raise descriptive exceptions; the orders layer handles them.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
import hmac
import hashlib
from urllib.parse import urlencode

logger = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
LIVE_BASE_URL    = "https://fapi.binance.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceFuturesClient:
    """
    Thin, dependency-light wrapper around the Binance USDT-M Futures REST API.
    Uses `requests` directly — no third-party SDK — for full transparency.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        timeout: int = 10,
        recv_window: int = 5000,
    ):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self.api_key    = api_key
        self.api_secret = api_secret
        self.base_url   = TESTNET_BASE_URL if testnet else LIVE_BASE_URL
        self.testnet    = testnet
        self.timeout    = timeout
        self.recv_window = recv_window

        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self.api_key})

        logger.info(
            "BinanceFuturesClient initialised | testnet=%s | base_url=%s",
            testnet,
            self.base_url,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_params(self, extra: dict) -> dict:
        params = {**extra, "timestamp": self._timestamp(), "recvWindow": self.recv_window}
        params["signature"] = self._sign(params)
        return params

    def _request(self, method: str, endpoint: str, params: dict | None = None, signed: bool = True) -> Any:
        url = f"{self.base_url}{endpoint}"
        request_params = self._signed_params(params or {}) if signed else (params or {})

        logger.debug("→ %s %s | params=%s", method.upper(), url, {k: v for k, v in request_params.items() if k != "signature"})

        try:
            response = self._session.request(
                method,
                url,
                params=request_params,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise ConnectionError(f"Cannot reach Binance API: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out after %ss", self.timeout)
            raise TimeoutError(f"Request timed out ({self.timeout}s).") from exc

        logger.debug("← %s | body=%s", response.status_code, response.text[:500])

        data = response.json()

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            # Binance error envelope: {"code": -1121, "msg": "Invalid symbol."}
            raise BinanceClientError(code=data["code"], message=data.get("msg", "Unknown error"))

        return data

    # ──────────────────────────────────────────────────────────────────────
    # Public API methods
    # ──────────────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Return True if the exchange is reachable."""
        try:
            self._request("GET", "/fapi/v1/ping", signed=False)
            logger.info("Ping successful.")
            return True
        except Exception as exc:
            logger.warning("Ping failed: %s", exc)
            return False

    def get_exchange_info(self, symbol: str) -> dict:
        """Fetch symbol metadata (tick size, lot size, etc.)."""
        data = self._request("GET", "/fapi/v1/exchangeInfo", signed=False)
        for s in data.get("symbols", []):
            if s["symbol"] == symbol:
                return s
        raise ValueError(f"Symbol '{symbol}' not found on Binance Futures.")

    def get_account_balance(self) -> list[dict]:
        """Return list of asset balances."""
        return self._request("GET", "/fapi/v2/balance")

    def create_order(self, **kwargs) -> dict:
        """
        Place a futures order.
        Accepts all parameters supported by POST /fapi/v1/order.
        """
        logger.info("Creating order | %s", kwargs)
        result = self._request("POST", "/fapi/v1/order", params=kwargs)
        logger.info("Order created | orderId=%s | status=%s", result.get("orderId"), result.get("status"))
        return result
