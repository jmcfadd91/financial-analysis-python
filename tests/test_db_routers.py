"""Integration tests for positions, watchlist, and notifications routers using SQLite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.session import get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    # Bind the session to a single connection so the in-memory tables created
    # by db_engine remain visible — each new engine connection gets its own
    # empty in-memory database, so we must reuse the same connection.
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    # Import app after fixtures so init_db isn't called at import time
    from api.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_position(client, ticker="FAKE", shares=10.0, entry_price=100.0, entry_date="2024-01-01"):
    return client.post(
        "/api/positions",
        json={"ticker": ticker, "shares": shares, "entry_price": entry_price, "entry_date": entry_date},
    )


# ---------------------------------------------------------------------------
# Positions tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_positions_empty(client):
    resp = client.get("/api/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["positions"] == []
    assert data["summary"]["total_invested"] == 0.0


@pytest.mark.unit
def test_add_position_invalid_ticker(client, monkeypatch):
    import api.routers.positions as pos_router

    monkeypatch.setattr(pos_router, "_get_current_price", lambda t: None)
    resp = _add_position(client, ticker="INVALID")
    assert resp.status_code == 422


@pytest.mark.unit
def test_add_and_get_position(client, monkeypatch):
    import api.routers.positions as pos_router

    monkeypatch.setattr(pos_router, "_get_current_price", lambda t: 150.0)
    resp = _add_position(client, ticker="AAPL", shares=5.0, entry_price=120.0)
    assert resp.status_code == 201
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["shares"] == 5.0

    resp2 = client.get("/api/positions")
    assert resp2.status_code == 200
    positions = resp2.json()["positions"]
    assert len(positions) == 1
    assert positions[0]["ticker"] == "AAPL"


@pytest.mark.unit
def test_delete_position(client, monkeypatch):
    import api.routers.positions as pos_router

    monkeypatch.setattr(pos_router, "_get_current_price", lambda t: 200.0)
    add_resp = _add_position(client, ticker="MSFT", shares=2.0, entry_price=300.0)
    assert add_resp.status_code == 201
    pos_id = add_resp.json()["id"]

    del_resp = client.delete(f"/api/positions/{pos_id}")
    assert del_resp.status_code == 204

    get_resp = client.get("/api/positions")
    ids = [p["id"] for p in get_resp.json()["positions"]]
    assert pos_id not in ids


@pytest.mark.unit
def test_delete_position_not_found(client):
    resp = client.delete("/api/positions/nonexistent-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Watchlist tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_watchlist_empty(client):
    resp = client.get("/api/watchlist")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.unit
def test_add_and_get_watchlist(client, monkeypatch):
    import api.routers.watchlist as wl_router

    def fake_enrich(ticker):
        from api.schemas import WatchlistItem
        return WatchlistItem(ticker=ticker, current_price=100.0, day_change_pct=1.5, rsi=55.0, prices=[])

    monkeypatch.setattr(wl_router, "_enrich", fake_enrich)

    resp = client.post("/api/watchlist", json={"ticker": "GOOG"})
    assert resp.status_code == 201
    assert resp.json()["ticker"] == "GOOG"

    resp2 = client.get("/api/watchlist")
    tickers = [i["ticker"] for i in resp2.json()["items"]]
    assert "GOOG" in tickers


@pytest.mark.unit
def test_add_watchlist_duplicate(client, monkeypatch):
    import api.routers.watchlist as wl_router

    def fake_enrich(ticker):
        from api.schemas import WatchlistItem
        return WatchlistItem(ticker=ticker, current_price=50.0, day_change_pct=0.5, rsi=40.0, prices=[])

    monkeypatch.setattr(wl_router, "_enrich", fake_enrich)

    client.post("/api/watchlist", json={"ticker": "AMZN"})
    resp2 = client.post("/api/watchlist", json={"ticker": "AMZN"})
    assert resp2.status_code == 422


@pytest.mark.unit
def test_remove_from_watchlist(client, monkeypatch):
    import api.routers.watchlist as wl_router

    def fake_enrich(ticker):
        from api.schemas import WatchlistItem
        return WatchlistItem(ticker=ticker, current_price=75.0, day_change_pct=-0.5, rsi=45.0, prices=[])

    monkeypatch.setattr(wl_router, "_enrich", fake_enrich)

    client.post("/api/watchlist", json={"ticker": "TSLA"})
    resp = client.delete("/api/watchlist/TSLA")
    assert resp.status_code == 204

    resp2 = client.get("/api/watchlist")
    tickers = [i["ticker"] for i in resp2.json()["items"]]
    assert "TSLA" not in tickers


@pytest.mark.unit
def test_remove_watchlist_not_found(client):
    resp = client.delete("/api/watchlist/NOTEXIST")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Notifications tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_notification_config_default(client):
    resp = client.get("/api/notifications/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bot_token_set"] is False
    assert data["chat_id"] == ""


@pytest.mark.unit
def test_save_and_get_notification_config(client):
    resp = client.post(
        "/api/notifications/config",
        json={"bot_token": "12345:ABCDE", "chat_id": "99999"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bot_token_set"] is True
    assert data["bot_token_masked"].startswith("1234")
    assert data["chat_id"] == "99999"

    get_resp = client.get("/api/notifications/config")
    assert get_resp.json()["bot_token_set"] is True


@pytest.mark.unit
def test_test_notification_missing_config(client):
    # Use a fresh client with a clean DB session to ensure no config row
    resp = client.post("/api/notifications/test")
    # Either 422 (no config) or 502 (bad token) is acceptable
    assert resp.status_code in (422, 502)
