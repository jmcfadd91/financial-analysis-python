"""GET/POST/DELETE /api/watchlist — watchlist management."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response

from api.schemas import AddWatchlistRequest, GetWatchlistResponse, WatchlistItem, _clean
from src.data.fetcher import DataFetcher

router = APIRouter()
_fetcher = DataFetcher()

_WATCHLIST_PATH = Path("data/watchlist.json")


def _load_tickers() -> list[str]:
    if not _WATCHLIST_PATH.exists():
        return []
    return json.loads(_WATCHLIST_PATH.read_text()).get("tickers", [])


def _save_tickers(tickers: list[str]) -> None:
    _WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _WATCHLIST_PATH.write_text(json.dumps({"tickers": tickers}))


def _compute_rsi(close_series) -> float:
    delta = close_series.diff()
    gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    return float((100 - 100 / (1 + gain / loss)).iloc[-1])


def _enrich(ticker: str) -> WatchlistItem:
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        df = _fetcher.fetch_historical_data(ticker, start=start, end=end)
        if df is None or df.empty or len(df) < 2:
            raise ValueError("insufficient data")
        current_price = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        day_change_pct = (current_price - prev_close) / prev_close * 100
        rsi = _compute_rsi(df["close"])
        prices = _clean(df["close"].tail(30).tolist())
        return WatchlistItem(
            ticker=ticker,
            current_price=current_price,
            day_change_pct=day_change_pct,
            rsi=rsi,
            prices=prices,
        )
    except Exception:
        return WatchlistItem(
            ticker=ticker,
            current_price=None,
            day_change_pct=None,
            rsi=None,
            prices=[],
        )


@router.get("/watchlist", response_model=GetWatchlistResponse)
async def get_watchlist() -> GetWatchlistResponse:
    tickers = _load_tickers()
    items = [_enrich(t) for t in tickers]
    return GetWatchlistResponse(items=items)


@router.post("/watchlist", response_model=WatchlistItem, status_code=201)
async def add_to_watchlist(req: AddWatchlistRequest) -> WatchlistItem:
    ticker = req.ticker.upper().strip()
    tickers = _load_tickers()
    if ticker in tickers:
        raise HTTPException(status_code=422, detail=f"{ticker} is already in watchlist")

    # Validate ticker exists
    item = _enrich(ticker)
    if item.current_price is None:
        raise HTTPException(status_code=422, detail=f"Could not fetch data for {ticker}")

    tickers.append(ticker)
    _save_tickers(tickers)
    return item


@router.delete("/watchlist/{ticker}", status_code=204)
async def remove_from_watchlist(ticker: str) -> Response:
    ticker = ticker.upper().strip()
    tickers = _load_tickers()
    if ticker not in tickers:
        raise HTTPException(status_code=404, detail=f"{ticker} not found in watchlist")
    tickers.remove(ticker)
    _save_tickers(tickers)
    return Response(status_code=204)
