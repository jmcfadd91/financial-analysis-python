"""POST /api/backtest — strategy backtesting."""

import json

from fastapi import APIRouter, HTTPException

from api.schemas import BacktestRequest, BacktestResponse, _clean
from src.backtesting.backtester import Backtester
from src.backtesting.strategy import RSIThreshold, SMACrossover
from src.data.fetcher import DataFetcher
from src.reporting.dashboard import Dashboard

router = APIRouter()
_fetcher = DataFetcher()


def _build_strategy(name: str, params: dict):
    if name == "sma":
        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))
        return SMACrossover(fast=fast, slow=slow)
    if name == "rsi":
        period = int(params.get("period", 14))
        oversold = float(params.get("oversold", 30))
        overbought = float(params.get("overbought", 70))
        return RSIThreshold(period=period, oversold=oversold, overbought=overbought)
    raise ValueError(f"Unknown strategy '{name}'. Use 'sma' or 'rsi'.")


@router.post("/backtest", response_model=BacktestResponse)
async def backtest(req: BacktestRequest) -> BacktestResponse:
    try:
        df = _fetcher.fetch_historical_data(req.ticker, req.start, req.end)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Data fetch failed: {exc}")

    try:
        strategy = _build_strategy(req.strategy, req.params)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        bt = Backtester(df, strategy, initial_capital=req.capital)
        bt.run()

        benchmark_series = None
        benchmark_return = None
        if req.benchmark:
            try:
                bench_df = _fetcher.fetch_historical_data(req.benchmark, req.start, req.end)
                bench_equity = (bench_df['close'] / bench_df['close'].iloc[0]) * req.capital
                bench_equity = bench_equity.reindex(bt.equity_curve.index, method='ffill').dropna()
                if not bench_equity.empty:
                    benchmark_series = bench_equity
                    benchmark_return = _clean((bench_equity.iloc[-1] / req.capital - 1) * 100)
            except Exception:
                pass  # benchmark failure is non-fatal

        dash = Dashboard(ticker=req.ticker, df=df)
        chart = json.loads(dash.equity_chart(bt, benchmark_series=benchmark_series).to_json())

        summary = _clean(bt.summary())
        if benchmark_return is not None:
            summary['benchmark_return'] = benchmark_return

        trades_df = bt.trades
        if trades_df.empty:
            trades = []
        else:
            records = trades_df.copy()
            for col in ("entry_date", "exit_date"):
                if col in records.columns:
                    records[col] = records[col].astype(str)
            trades = _clean(records.to_dict(orient="records"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return BacktestResponse(chart=chart, summary=summary, trades=trades)
