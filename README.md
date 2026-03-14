# Financial Analysis Toolkit

A Bloomberg-style financial analysis toolkit with a Python library core and a FastAPI + React web application for interactive dashboards.

## Features

- **Technical Analysis** — SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, buy/sell signal generation
- **Risk Metrics** — Sharpe ratio, Sortino ratio, VaR (historical & parametric), CVaR, Max Drawdown, Beta
- **Portfolio Analysis** — Correlation/covariance matrices, efficient frontier, portfolio Sharpe
- **Monte Carlo Simulation** — GBM price paths, percentile fan charts, probability of loss, VaR
- **Backtesting** — SMA Crossover and RSI Threshold strategies with equity curves and trade logs
- **Interactive Dashboards** — Plotly.js charts served via FastAPI, rendered in a React frontend

---

## Quick Start

### Prerequisites

- Python 3.9+
- TA-Lib native library: `brew install ta-lib` (macOS) or build from source (Linux)
- Node.js 18+ (for the frontend)

### Install

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Run (two terminals)

```bash
# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload
# API docs: http://localhost:8000/docs

# Terminal 2 — React frontend
cd frontend && npm run dev
# App: http://localhost:5173
```

### Run with Docker Compose

```bash
docker compose up
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Technical indicators + risk metrics for a ticker |
| `POST` | `/api/portfolio` | Portfolio analysis for multiple tickers |
| `POST` | `/api/simulate` | Monte Carlo price simulation |
| `POST` | `/api/backtest` | Strategy backtest (SMA Crossover or RSI Threshold) |

Interactive API documentation is available at `http://localhost:8000/docs` when the server is running.

### Example

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "start": "2024-01-01", "end": "2025-01-01"}'
```

```bash
curl -X POST http://localhost:8000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "strategy": "sma", "params": {"fast": 20, "slow": 50}, "start": "2024-01-01", "end": "2025-01-01", "capital": 10000}'
```

---

## Project Structure

```
financial-analysis-python/
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point, CORS, router mounts
│   ├── schemas.py              # Pydantic request/response models
│   └── routers/
│       ├── analyze.py          # POST /api/analyze
│       ├── portfolio.py        # POST /api/portfolio
│       ├── simulate.py         # POST /api/simulate
│       └── backtest.py         # POST /api/backtest
├── frontend/                   # React app (Vite + TypeScript)
│   └── src/
│       ├── App.tsx             # Layout, tabs, shared context
│       ├── api/client.ts       # Typed API client (axios)
│       └── components/
│           ├── Sidebar.tsx
│           ├── TechChart.tsx
│           ├── RiskDashboard.tsx
│           ├── PortfolioView.tsx
│           ├── SimulationChart.tsx
│           └── BacktestView.tsx
├── src/                        # Core Python library (unchanged)
│   ├── data/fetcher.py
│   ├── analysis/
│   │   ├── technical.py
│   │   ├── risk.py
│   │   ├── portfolio.py
│   │   └── simulation.py
│   ├── backtesting/
│   │   ├── strategy.py
│   │   └── backtester.py
│   └── reporting/dashboard.py
├── tests/                      # 229 unit tests
├── docker-compose.yml
├── Dockerfile.api
├── requirements.txt
└── starter.py                  # CLI demo script
```

---

## Running Tests

```bash
# Unit tests only (no network, fast)
pytest tests/ -m unit -q

# All tests including integration (requires live market data)
pytest tests/
```

---

## Architecture Notes

- The `src/` core library is framework-agnostic — used directly from CLI scripts or imported by the FastAPI routers.
- All OHLCV DataFrames use **lowercase column names** (`open`, `high`, `low`, `close`, `volume`).
- Charts are generated server-side as Plotly JSON (`fig.to_json()`) and rendered client-side by `react-plotly.js` — no chart logic in the frontend.
- The Vite dev server proxies `/api/*` to `http://localhost:8000`, so no CORS issues in development.
