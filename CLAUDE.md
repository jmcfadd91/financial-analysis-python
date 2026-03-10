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
```

Note: TA-Lib requires a native C library installed separately (`brew install ta-lib` on macOS) before `pip install TA-Lib`.

## Architecture

This is a Bloomberg-style financial analysis toolkit built around three core layers:

**Data Layer (`src/data/`)**
- `fetcher.py` — `DataFetcher` class: fetches OHLCV data via `yfinance`, supports single/multi-ticker, in-memory TTL caching, rate limiting (500ms delay), and data validation. Returns DataFrames with lowercase column names (`open`, `high`, `low`, `close`, `volume`).

**Analysis Layer (`src/analysis/`)**
- `technical.py` — `TechnicalAnalyzer` class: wraps TA-Lib to compute SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, and generate composite buy/sell signals. Initialized with an OHLCV DataFrame and caches computed indicators in `self.indicators`.

**Utilities (`src/utils/`)**
- `logger.py` — `setup_logger()` factory used throughout the codebase instead of `logging.basicConfig`.

**Tests (`tests/`)**
- `conftest.py` provides session-scoped fixtures for real API data and function-scoped fixtures for synthetic DataFrames. Use `sample_dataframe` fixture for unit tests that don't need API calls. Tests are marked `unit`, `integration`, or `slow` via pytest markers.
- `test_fetcher.py` at the project root tests a `src/data_fetcher.py` path (legacy location); the canonical implementation is `src/data/fetcher.py`.

**Key data contract:** All OHLCV DataFrames use lowercase column names. `DataFetcher.fetch_historical_data()` lowercases columns on download. `TechnicalAnalyzer` requires `['open', 'high', 'low', 'close', 'volume']`.
