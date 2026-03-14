"""POST /api/analyze — technical analysis + risk metrics."""

import json

from fastapi import APIRouter, HTTPException

from api.schemas import AnalyzeRequest, AnalyzeResponse, _clean
from src.analysis.risk import RiskAnalyzer
from src.analysis.technical import TechnicalAnalyzer
from src.data.fetcher import DataFetcher
from src.reporting.dashboard import Dashboard

router = APIRouter()
_fetcher = DataFetcher()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        df = _fetcher.fetch_historical_data(
            req.ticker, req.start, req.end, req.interval
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Data fetch failed: {exc}")

    try:
        ta = TechnicalAnalyzer(df)
        ta.sma(20)
        ta.sma(50)
        ta.ema(20)
        ta.rsi()
        ta.macd()
        ta.bollinger_bands()

        ra = RiskAnalyzer(df)

        dash = Dashboard(ticker=req.ticker, df=df, technical=ta, risk=ra)

        charts = {
            "price": json.loads(dash.price_chart().to_json()),
            "technical": json.loads(dash.technical_chart().to_json()),
            "risk": json.loads(dash.risk_dashboard().to_json()),
        }
        metrics = _clean(ra.get_all_metrics())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return AnalyzeResponse(charts=charts, metrics=metrics)
