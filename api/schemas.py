"""Pydantic request/response models for the Financial Analysis API."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    ticker: str
    start: str = "2024-01-01"
    end: str = "2025-01-01"
    interval: str = "1d"


class PortfolioRequest(BaseModel):
    tickers: List[str]
    weights: Optional[List[float]] = None
    start: str = "2024-01-01"
    end: str = "2025-01-01"


class SimulateRequest(BaseModel):
    ticker: str
    start: str = "2024-01-01"
    end: str = "2025-01-01"
    n_simulations: int = 1000
    horizon_days: int = 252


class BacktestRequest(BaseModel):
    ticker: str
    strategy: str = "sma"   # "sma" | "rsi"
    params: Dict[str, Any] = {}
    start: str = "2024-01-01"
    end: str = "2025-01-01"
    capital: float = 10_000.0
    benchmark: Optional[str] = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    charts: Dict[str, Any]
    metrics: Dict[str, Any]


class PortfolioResponse(BaseModel):
    charts: Dict[str, Any]
    metrics: Dict[str, Any]


class SimulateResponse(BaseModel):
    chart: Dict[str, Any]
    metrics: Dict[str, Any]


class BacktestResponse(BaseModel):
    chart: Dict[str, Any]
    summary: Dict[str, Any]
    trades: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Positions models
# ---------------------------------------------------------------------------

class Position(BaseModel):
    id: str
    ticker: str
    shares: float
    entry_price: float
    entry_date: str


class AddPositionRequest(BaseModel):
    ticker: str
    shares: float
    entry_price: float
    entry_date: str


class PositionRow(BaseModel):
    id: str
    ticker: str
    shares: float
    entry_price: float
    entry_date: str
    current_price: Optional[float]
    cost_basis: float
    current_value: Optional[float]
    pnl: Optional[float]
    pnl_pct: Optional[float]


class PortfolioSummary(BaseModel):
    total_invested: float
    total_value: Optional[float]
    total_pnl: Optional[float]
    total_return_pct: Optional[float]


class GetPositionsResponse(BaseModel):
    positions: List[PositionRow]
    summary: PortfolioSummary
    allocation_chart: Dict[str, Any]


class SimulatePortfolioRequest(BaseModel):
    n_simulations: int = 1000
    horizon_days: int = 252
    history_days: int = 365


class SimulatePortfolioResponse(BaseModel):
    chart: Dict[str, Any]
    metrics: Dict[str, Any]


# ---------------------------------------------------------------------------
# Watchlist models
# ---------------------------------------------------------------------------

class AddWatchlistRequest(BaseModel):
    ticker: str


class WatchlistItem(BaseModel):
    ticker: str
    current_price: Optional[float]
    day_change_pct: Optional[float]
    rsi: Optional[float]
    prices: List[float]


class GetWatchlistResponse(BaseModel):
    items: List[WatchlistItem]


# ---------------------------------------------------------------------------
# Notification models
# ---------------------------------------------------------------------------

class NotificationConfigRequest(BaseModel):
    bot_token: str
    chat_id: str


class NotificationConfigResponse(BaseModel):
    bot_token_set: bool
    bot_token_masked: str   # e.g. "123456:A***xyz"
    chat_id: str


# ---------------------------------------------------------------------------
# JSON serialization helper
# ---------------------------------------------------------------------------

def _clean(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(obj, np.ndarray):
        return [_clean(v) for v in obj.tolist()]
    if isinstance(obj, (pd.Timestamp,)):
        return str(obj.date())
    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else obj
    return obj
