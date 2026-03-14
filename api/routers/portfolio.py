"""POST /api/portfolio — portfolio analysis, efficient frontier, correlation."""

import json

import plotly.graph_objects as go
from fastapi import APIRouter, HTTPException

from api.schemas import PortfolioRequest, PortfolioResponse, _clean
from src.analysis.portfolio import PortfolioAnalyzer
from src.data.fetcher import DataFetcher

router = APIRouter()
_fetcher = DataFetcher()


def _frontier_chart(pa: PortfolioAnalyzer) -> dict:
    frontier = pa.efficient_frontier(n_portfolios=500)
    fig = go.Figure(go.Scatter(
        x=frontier["volatility"],
        y=frontier["return"],
        mode="markers",
        marker=dict(
            color=frontier["sharpe"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Sharpe"),
            size=5,
        ),
        text=[f"Sharpe: {s:.2f}" for s in frontier["sharpe"]],
        name="Portfolios",
    ))
    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Volatility (ann.)",
        yaxis_title="Return (ann.)",
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#ffffff"),
    )
    return json.loads(fig.to_json())


def _correlation_chart(pa: PortfolioAnalyzer) -> dict:
    corr = pa.correlation_matrix()
    fig = go.Figure(go.Heatmap(
        z=corr.values.tolist(),
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}",
    ))
    fig.update_layout(
        title="Correlation Matrix",
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#ffffff"),
    )
    return json.loads(fig.to_json())


@router.post("/portfolio", response_model=PortfolioResponse)
async def portfolio(req: PortfolioRequest) -> PortfolioResponse:
    if len(req.tickers) < 2:
        raise HTTPException(status_code=422, detail="At least 2 tickers required.")

    try:
        data = _fetcher.fetch_multiple_tickers(req.tickers, req.start, req.end)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Data fetch failed: {exc}")

    try:
        pa = PortfolioAnalyzer(data, weights=req.weights)
        charts = {
            "frontier": _frontier_chart(pa),
            "correlation": _correlation_chart(pa),
        }
        metrics = _clean(pa.get_all_metrics())
        metrics["tickers"] = req.tickers
        metrics["weights"] = _clean(pa.weights.tolist())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return PortfolioResponse(charts=charts, metrics=metrics)
