# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_fetcher.py

# Run a single test
pytest tests/test_fetcher.py::TestDataFetcherInitialization::test_default_initialization

# Run only unit tests (no API calls)
pytest tests/ -m unit

# Run integration tests (requires live API)
pytest tests/ -m integration

# Run a module directly
python src/data/fetcher.py
python starter.py

# Start the FastAPI backend
uvicorn api.main:app --reload
# API docs available at http://localhost:8000/docs

# Start the React frontend (separate terminal)
cd frontend && npm run dev
# App available at http://localhost:5173

# Run both with Docker Compose
docker compose up
```

Note: TA-Lib requires a native C library installed separately (`brew install ta-lib` on macOS) before `pip install TA-Lib`.

## Architecture

This is a Bloomberg-style financial analysis toolkit with a CLI/library core and a FastAPI + React web app layer on top.

### Core Library (`src/`) — do not modify when working on the web layer

**Data Layer (`src/data/`)**
- `fetcher.py` — `DataFetcher` class: fetches OHLCV data via `yfinance`, supports single/multi-ticker, in-memory TTL caching, rate limiting (500ms delay), and data validation. Returns DataFrames with lowercase column names (`open`, `high`, `low`, `close`, `volume`).

**Analysis Layer (`src/analysis/`)**
- `technical.py` — `TechnicalAnalyzer` class: wraps TA-Lib to compute SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, and generate composite buy/sell signals. Initialized with an OHLCV DataFrame and caches computed indicators in `self.indicators`.
- `risk.py` — `RiskAnalyzer` class: Sharpe, Sortino, VaR (historical & parametric), CVaR, Max Drawdown, Beta.
- `portfolio.py` — `PortfolioAnalyzer` class: correlation/covariance matrices, portfolio return/volatility/Sharpe, efficient frontier (random portfolios).
- `simulation.py` — `MonteCarloSimulator` class: GBM price paths, percentile paths, probability of loss, VaR.

**Backtesting Layer (`src/backtesting/`)**
- `strategy.py` — `Strategy` ABC + `SMACrossover(fast, slow)` + `RSIThreshold(period, oversold, overbought)`.
- `backtester.py` — `Backtester` class: runs a strategy on OHLCV data, produces equity curve, trades DataFrame, and summary stats.

**Reporting (`src/reporting/`)**
- `dashboard.py` — `Dashboard` class: Plotly dark-theme charts — `price_chart()`, `technical_chart()`, `risk_dashboard()`, `simulation_chart()`, `equity_chart()`. All return `go.Figure`; serialise with `fig.to_json()`.

**Utilities (`src/utils/`)**
- `logger.py` — `setup_logger()` factory. Always use this instead of `logging.basicConfig`.

### Web App Layer

**FastAPI Backend (`api/`)**
- `main.py` — app entry point, CORS for `http://localhost:5173`, all routers mounted under `/api`.
- `schemas.py` — Pydantic request/response models + `_clean()` helper (converts numpy/pandas types to JSON-safe Python).
- `routers/analyze.py` — `POST /api/analyze` — technical + risk analysis for a single ticker.
- `routers/portfolio.py` — `POST /api/portfolio` — multi-ticker portfolio analysis.
- `routers/simulate.py` — `POST /api/simulate` — Monte Carlo simulation.
- `routers/backtest.py` — `POST /api/backtest` — SMA or RSI strategy backtest.

**React Frontend (`frontend/`)**
- Vite + React + TypeScript; Plotly.js via `react-plotly.js`.
- `src/api/client.ts` — typed axios wrappers for all 4 endpoints.
- `src/App.tsx` — layout + `AppContext` (shared ticker, date range, runSignal).
- `src/components/` — `Sidebar`, `TechChart`, `RiskDashboard`, `PortfolioView`, `SimulationChart`, `BacktestView`, `PlotlyChart`, `MetricCards`.
- Vite dev proxy: `/api` → `http://localhost:8000`.

### Tests (`tests/`)
- `conftest.py` provides session-scoped fixtures for real API data and function-scoped fixtures for synthetic DataFrames. Use `sample_dataframe` fixture for unit tests that don't need API calls. Tests are marked `unit`, `integration`, or `slow` via pytest markers.
- `test_fetcher.py` at the project root tests a `src/data_fetcher.py` path (legacy location); the canonical implementation is `src/data/fetcher.py`.

**Key data contract:** All OHLCV DataFrames use lowercase column names. `DataFetcher.fetch_historical_data()` lowercases columns on download. `TechnicalAnalyzer` requires `['open', 'high', 'low', 'close', 'volume']`.
