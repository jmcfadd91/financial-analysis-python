"""Telegram notification support for financial reports."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_RSI_OVERSOLD = 30
_RSI_OVERBOUGHT = 70
_DAY_CHANGE_ALERT = 3.0  # percent


class TelegramNotifier:
    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._url = self.BASE_URL.format(token=bot_token)

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_message(self, text: str) -> bool:
        """POST text to Telegram with Markdown parse mode. Returns True on success."""
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            resp = requests.post(self._url, json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if not result.get("ok"):
                logger.error("Telegram API error: %s", result)
                return False
            return True
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Report building
    # ------------------------------------------------------------------

    def build_report(
        self,
        watchlist_items: list[dict],
        positions: list[dict],
        summary: Optional[dict] = None,
    ) -> str:
        """Assemble the Markdown report string."""
        date_str = datetime.now().strftime("%a %b %d %Y")
        lines: list[str] = [f"📊 *Financial Report — {date_str}*", ""]

        # ── Watchlist ──────────────────────────────────────────────────
        if watchlist_items:
            lines.append("*Watchlist*")
            alerts: list[str] = []
            for item in watchlist_items:
                ticker = item.get("ticker", "?")
                price = item.get("current_price")
                change = item.get("day_change_pct")
                rsi = item.get("rsi")

                price_str = f"${price:,.2f}" if price is not None else "N/A"
                if change is not None:
                    sign = "+" if change >= 0 else "−"
                    change_str = f"{sign}{abs(change):.2f}%"
                else:
                    change_str = "N/A"
                rsi_str = f"RSI: {rsi:.1f}" if rsi is not None else ""

                # RSI signal emoji
                rsi_flag = ""
                if rsi is not None:
                    if rsi < _RSI_OVERSOLD:
                        rsi_flag = " 🟢"
                        alerts.append(f"🟢 {ticker} RSI {rsi:.1f} — oversold")
                    elif rsi > _RSI_OVERBOUGHT:
                        rsi_flag = " 🔴"
                        alerts.append(f"🔴 {ticker} RSI {rsi:.1f} — overbought")

                # Large day-change alert
                if change is not None and abs(change) > _DAY_CHANGE_ALERT:
                    direction = "up" if change > 0 else "down"
                    alerts.append(f"⚡ {ticker} {direction} {abs(change):.2f}% today")

                row = f"{ticker:<6} {price_str:<10} {change_str:<9} {rsi_str}{rsi_flag}"
                lines.append(row)
            lines.append("")

            if alerts:
                lines.append("*Alerts*")
                lines.extend(alerts)
                lines.append("")
        else:
            lines.append("_No watchlist items_")
            lines.append("")

        # ── Portfolio summary ──────────────────────────────────────────
        if summary:
            invested = summary.get("total_invested", 0)
            value = summary.get("total_value")
            pnl = summary.get("total_pnl")
            pnl_pct = summary.get("total_return_pct")

            invested_str = f"${invested:,.0f}"
            value_str = f"${value:,.0f}" if value is not None else "N/A"
            if pnl is not None and pnl_pct is not None:
                sign = "+" if pnl >= 0 else "−"
                pnl_str = f"{sign}${abs(pnl):,.0f} ({sign}{abs(pnl_pct):.2f}%)"
            else:
                pnl_str = "N/A"

            lines.append("*Portfolio*")
            lines.append(f"Invested: {invested_str} | Value: {value_str} | P&L: {pnl_str}")
            lines.append("")

        # ── Positions ──────────────────────────────────────────────────
        if positions:
            lines.append("*Positions*")
            for pos in positions:
                ticker = pos.get("ticker", "?")
                shares = pos.get("shares", 0)
                price = pos.get("current_price")
                pnl = pos.get("pnl")
                pnl_pct = pos.get("pnl_pct")

                price_str = f"${price:,.2f}" if price is not None else "N/A"
                if pnl is not None and pnl_pct is not None:
                    sign = "+" if pnl >= 0 else "−"
                    pnl_str = f"P&L: {sign}${abs(pnl):,.0f} ({sign}{abs(pnl_pct):.1f}%)"
                else:
                    pnl_str = "P&L: N/A"

                lines.append(f"{ticker} ×{shares:.0f}   {price_str}   {pnl_str}")
            lines.append("")

        # ── AI recommendations stub ────────────────────────────────────
        # TODO: call AI agent here when integrated
        lines.append("💡 _AI recommendations — coming soon_")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Full report: load data → build → send
    # ------------------------------------------------------------------

    def send_report(self) -> bool:
        """Load watchlist + positions from disk, build report, send. Returns success bool."""
        # Lazy imports to avoid pulling FastAPI deps when used as a script
        from src.data.fetcher import DataFetcher

        fetcher = DataFetcher()

        # ── Watchlist ──────────────────────────────────────────────────
        watchlist_path = Path("data/watchlist.json")
        tickers: list[str] = []
        if watchlist_path.exists():
            try:
                tickers = json.loads(watchlist_path.read_text()).get("tickers", [])
            except Exception as exc:
                logger.warning("Could not read watchlist.json: %s", exc)

        watchlist_items: list[dict] = []
        for ticker in tickers:
            try:
                end = datetime.now().strftime("%Y-%m-%d")
                start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                df = fetcher.fetch_historical_data(ticker, start=start, end=end)
                if df is None or df.empty or len(df) < 2:
                    raise ValueError("insufficient data")
                price = float(df["close"].iloc[-1])
                prev = float(df["close"].iloc[-2])
                change = (price - prev) / prev * 100

                # Simple RSI (EWM)
                delta = df["close"].diff()
                gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
                loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
                rsi = float((100 - 100 / (1 + gain / loss)).iloc[-1])

                watchlist_items.append({
                    "ticker": ticker,
                    "current_price": price,
                    "day_change_pct": change,
                    "rsi": rsi,
                })
            except Exception as exc:
                logger.warning("Could not enrich %s: %s", ticker, exc)
                watchlist_items.append({"ticker": ticker, "current_price": None, "day_change_pct": None, "rsi": None})

        # ── Positions ──────────────────────────────────────────────────
        portfolio_path = Path("data/portfolio.json")
        raw_positions: list[dict] = []
        if portfolio_path.exists():
            try:
                raw_positions = json.loads(portfolio_path.read_text()).get("positions", [])
            except Exception as exc:
                logger.warning("Could not read portfolio.json: %s", exc)

        enriched_positions: list[dict] = []
        total_invested = 0.0
        total_value = 0.0
        has_prices = False

        for pos in raw_positions:
            ticker = pos["ticker"]
            shares = pos["shares"]
            entry_price = pos["entry_price"]
            cost_basis = shares * entry_price
            total_invested += cost_basis

            try:
                end = datetime.now().strftime("%Y-%m-%d")
                start = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
                df = fetcher.fetch_historical_data(ticker, start=start, end=end)
                current_price = float(df["close"].iloc[-1])
                current_value = shares * current_price
                pnl = current_value - cost_basis
                pnl_pct = pnl / cost_basis * 100 if cost_basis else None
                total_value += current_value
                has_prices = True
                enriched_positions.append({
                    "ticker": ticker,
                    "shares": shares,
                    "current_price": current_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                })
            except Exception as exc:
                logger.warning("Could not get price for %s: %s", ticker, exc)
                enriched_positions.append({
                    "ticker": ticker,
                    "shares": shares,
                    "current_price": None,
                    "pnl": None,
                    "pnl_pct": None,
                })

        summary: Optional[dict] = None
        if raw_positions:
            total_pnl = (total_value - total_invested) if has_prices else None
            total_return_pct = (total_pnl / total_invested * 100) if (total_pnl is not None and total_invested) else None
            summary = {
                "total_invested": total_invested,
                "total_value": total_value if has_prices else None,
                "total_pnl": total_pnl,
                "total_return_pct": total_return_pct,
            }

        report = self.build_report(watchlist_items, enriched_positions, summary)
        return self.send_message(report)
