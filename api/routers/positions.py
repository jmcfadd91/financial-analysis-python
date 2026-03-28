"""CRUD + simulation endpoints for the real-portfolio positions tracker."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.schemas import (
    AddPositionRequest,
    GetPositionsResponse,
    Position,
    PortfolioSummary,
    PositionRow,
    SimulatePortfolioRequest,
    SimulatePortfolioResponse,
    _clean,
)
from src.analysis.simulation import MonteCarloSimulator
from src.data.fetcher import DataFetcher
from src.db import PositionModel, get_db
from src.reporting.dashboard import Dashboard

router = APIRouter()
_fetcher = DataFetcher()


# ---------------------------------------------------------------------------
# Price helpers
# ---------------------------------------------------------------------------

def _get_current_price(ticker: str) -> Optional[float]:
    """Fetch the most recent closing price, returning None on any failure."""
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        df = _fetcher.fetch_historical_data(ticker, start, end)
        return float(df["close"].iloc[-1])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _allocation_chart(rows: List[PositionRow]) -> dict:
    """Dark-theme donut pie of current_value per ticker."""
    labels, values = [], []
    for r in rows:
        if r.current_value is not None:
            labels.append(r.ticker)
            values.append(r.current_value)

    if not labels:
        fig = {
            "data": [],
            "layout": {
                "paper_bgcolor": "#0d0d1a",
                "plot_bgcolor": "#0d0d1a",
                "font": {"color": "#e0e0f0"},
                "title": "No data",
            },
        }
        return fig

    fig = {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.4,
                "textinfo": "label+percent",
                "textfont": {"color": "#e0e0f0"},
                "marker": {
                    "line": {"color": "#0d0d1a", "width": 2},
                },
            }
        ],
        "layout": {
            "paper_bgcolor": "#0d0d1a",
            "plot_bgcolor": "#0d0d1a",
            "font": {"color": "#e0e0f0"},
            "title": {"text": "Allocation by Current Value", "font": {"size": 14}},
            "margin": {"t": 40, "b": 20, "l": 20, "r": 20},
            "legend": {"font": {"color": "#e0e0f0"}},
            "showlegend": True,
        },
    }
    return fig


# ---------------------------------------------------------------------------
# Portfolio series builder (for simulation)
# ---------------------------------------------------------------------------

def _build_portfolio_series(
    positions: List[PositionModel], data: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Aggregate shares per ticker, build a combined dollar-value series.
    Returns a DataFrame with a 'close' column representing total portfolio value.
    """
    shares_map: Dict[str, float] = {}
    for pos in positions:
        shares_map[pos.ticker] = shares_map.get(pos.ticker, 0.0) + pos.shares

    value_series: Dict[str, pd.Series] = {}
    for ticker, shares in shares_map.items():
        if ticker in data:
            value_series[ticker] = data[ticker]["close"] * shares

    if not value_series:
        raise ValueError("No valid price data for any held ticker.")

    combined = pd.DataFrame(value_series).dropna()
    portfolio_value = combined.sum(axis=1)
    return pd.DataFrame({"close": portfolio_value})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/positions", response_model=GetPositionsResponse)
async def get_positions(db: Session = Depends(get_db)) -> GetPositionsResponse:
    raw = db.query(PositionModel).all()

    rows: List[PositionRow] = []
    for p in raw:
        current_price = _get_current_price(p.ticker)
        cost_basis = p.shares * p.entry_price
        current_value = p.shares * current_price if current_price is not None else None
        pnl = (current_value - cost_basis) if current_value is not None else None
        pnl_pct = (pnl / cost_basis * 100) if (pnl is not None and cost_basis != 0) else None

        rows.append(
            PositionRow(
                id=p.id,
                ticker=p.ticker,
                shares=p.shares,
                entry_price=p.entry_price,
                entry_date=p.entry_date,
                current_price=current_price,
                cost_basis=cost_basis,
                current_value=current_value,
                pnl=pnl,
                pnl_pct=pnl_pct,
            )
        )

    total_invested = sum(r.cost_basis for r in rows)
    valid_values = [r.current_value for r in rows if r.current_value is not None]
    total_value = sum(valid_values) if valid_values else None
    total_pnl = (total_value - total_invested) if total_value is not None else None
    total_return_pct = (
        (total_pnl / total_invested * 100)
        if (total_pnl is not None and total_invested != 0)
        else None
    )

    summary = PortfolioSummary(
        total_invested=total_invested,
        total_value=total_value,
        total_pnl=total_pnl,
        total_return_pct=total_return_pct,
    )

    return GetPositionsResponse(
        positions=rows,
        summary=summary,
        allocation_chart=_allocation_chart(rows),
    )


@router.post("/positions", response_model=Position, status_code=201)
async def add_position(req: AddPositionRequest, db: Session = Depends(get_db)) -> Position:
    price = _get_current_price(req.ticker.upper())
    if price is None:
        raise HTTPException(
            status_code=422, detail=f"Could not fetch data for ticker '{req.ticker}'. Check the symbol."
        )

    position = PositionModel(
        id=str(uuid.uuid4()),
        ticker=req.ticker.upper(),
        shares=req.shares,
        entry_price=req.entry_price,
        entry_date=req.entry_date,
    )
    db.add(position)
    db.commit()
    db.refresh(position)

    return Position(
        id=position.id,
        ticker=position.ticker,
        shares=position.shares,
        entry_price=position.entry_price,
        entry_date=position.entry_date,
    )


@router.delete("/positions/{position_id}", status_code=204)
async def delete_position(position_id: str, db: Session = Depends(get_db)) -> Response:
    position = db.query(PositionModel).filter(PositionModel.id == position_id).first()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found.")
    db.delete(position)
    db.commit()
    return Response(status_code=204)


@router.post("/positions/simulate", response_model=SimulatePortfolioResponse)
async def simulate_portfolio(
    req: SimulatePortfolioRequest, db: Session = Depends(get_db)
) -> SimulatePortfolioResponse:
    raw = db.query(PositionModel).all()
    if not raw:
        raise HTTPException(status_code=422, detail="No positions in portfolio.")

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=req.history_days)).strftime("%Y-%m-%d")

    unique_tickers = list({p.ticker for p in raw})

    try:
        data = _fetcher.fetch_multiple_tickers(unique_tickers, start, end)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Data fetch failed: {exc}")

    try:
        portfolio_df = _build_portfolio_series(raw, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        sim = MonteCarloSimulator(
            portfolio_df,
            n_simulations=req.n_simulations,
            horizon_days=req.horizon_days,
        )
        sim.simulate()

        dash = Dashboard(ticker="Portfolio", df=portfolio_df)
        chart = json.loads(dash.simulation_chart(sim).to_json())

        metrics = _clean(
            {
                "expected_return": sim.expected_return(),
                "prob_loss": sim.probability_of_loss(),
                "var_95": sim.value_at_risk(confidence=0.95),
                "n_simulations": req.n_simulations,
                "horizon_days": req.horizon_days,
                "n_positions": len(raw),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return SimulatePortfolioResponse(chart=chart, metrics=metrics)
