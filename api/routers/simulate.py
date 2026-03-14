"""POST /api/simulate — Monte Carlo price simulation."""

import json

from fastapi import APIRouter, HTTPException

from api.schemas import SimulateRequest, SimulateResponse, _clean
from src.analysis.simulation import MonteCarloSimulator
from src.data.fetcher import DataFetcher
from src.reporting.dashboard import Dashboard

router = APIRouter()
_fetcher = DataFetcher()


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: SimulateRequest) -> SimulateResponse:
    try:
        df = _fetcher.fetch_historical_data(req.ticker, req.start, req.end)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Data fetch failed: {exc}")

    try:
        sim = MonteCarloSimulator(
            df,
            n_simulations=req.n_simulations,
            horizon_days=req.horizon_days,
        )
        sim.simulate(seed=42)

        dash = Dashboard(ticker=req.ticker, df=df)
        chart = json.loads(dash.simulation_chart(sim).to_json())

        metrics = _clean({
            "expected_return": sim.expected_return(),
            "prob_loss": sim.probability_of_loss(),
            "var_95": sim.value_at_risk(confidence=0.95),
            "n_simulations": req.n_simulations,
            "horizon_days": req.horizon_days,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return SimulateResponse(chart=chart, metrics=metrics)
