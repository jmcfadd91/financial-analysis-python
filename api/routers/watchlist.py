"""GET/POST/DELETE /api/watchlist — watchlist management."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from api.schemas import AddWatchlistRequest, GetWatchlistResponse, WatchlistItem, _clean
from src.analysis.technical import compute_rsi_ewm
from src.data.fetcher import DataFetcher
from src.db import WatchlistModel, get_db

router = APIRouter()
_fetcher = DataFetcher()
logger = logging.getLogger(__name__)


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
        rsi = float(compute_rsi_ewm(df["close"]).iloc[-1])
        prices = _clean(df["close"].tail(30).tolist())
        return WatchlistItem(
            ticker=ticker,
            current_price=current_price,
            day_change_pct=day_change_pct,
            rsi=rsi,
            prices=prices,
        )
    except Exception as exc:
        logger.warning("Could not enrich watchlist ticker %s: %s", ticker, exc)
        return WatchlistItem(
            ticker=ticker,
            current_price=None,
            day_change_pct=None,
            rsi=None,
            prices=[],
        )


@router.get("/watchlist", response_model=GetWatchlistResponse)
async def get_watchlist(db: Session = Depends(get_db)) -> GetWatchlistResponse:
    rows = db.query(WatchlistModel).all()
    items = [_enrich(r.ticker) for r in rows]
    return GetWatchlistResponse(items=items)


@router.post("/watchlist", response_model=WatchlistItem, status_code=201)
async def add_to_watchlist(req: AddWatchlistRequest, db: Session = Depends(get_db)) -> WatchlistItem:
    ticker = req.ticker.upper().strip()

    existing = db.query(WatchlistModel).filter(WatchlistModel.ticker == ticker).first()
    if existing:
        raise HTTPException(status_code=422, detail=f"{ticker} is already in watchlist")

    item = _enrich(ticker)
    if item.current_price is None:
        raise HTTPException(status_code=422, detail=f"Could not fetch data for {ticker}")

    db.add(WatchlistModel(ticker=ticker))
    db.commit()
    return item


@router.delete("/watchlist/{ticker}", status_code=204)
async def remove_from_watchlist(ticker: str, db: Session = Depends(get_db)) -> Response:
    ticker = ticker.upper().strip()
    row = db.query(WatchlistModel).filter(WatchlistModel.ticker == ticker).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{ticker} not found in watchlist")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
