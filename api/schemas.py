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
