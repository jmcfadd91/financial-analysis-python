"""
Pytest configuration and fixtures for integration testing.
Provides real API fixtures using yfinance for live data testing.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data.fetcher import DataFetcher
from src.analysis.technical import TechnicalAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@pytest.fixture(scope="session")
def test_tickers():
    """Standard test tickers for integration tests."""
    return ["AAPL", "MSFT", "GOOGL"]


@pytest.fixture(scope="session")
def test_date_range():
    """Standard date range for testing (last 180 days)."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    return start_date, end_date


@pytest.fixture(scope="session")
def fetcher():
    """DataFetcher instance for real API calls."""
    return DataFetcher()


@pytest.fixture(scope="session")
def test_data(fetcher, test_tickers, test_date_range):
    """
    Fetch real market data for test tickers.
    Scope: session (reuse across all tests to minimize API calls).
    """
    logger.info(f"Fetching real data for {test_tickers}...")
    start_date, end_date = test_date_range

    try:
        data = {}
        for ticker in test_tickers:
            data[ticker] = fetcher.fetch_historical_data(
                ticker,
                start=str(start_date),
                end=str(end_date)
            )
        logger.info(f"Successfully fetched data for {len(data)} tickers")
        yield data
    except Exception as e:
        logger.error(f"Failed to fetch test data: {e}")
        pytest.skip(f"API unavailable: {e}")


@pytest.fixture(scope="function")
def analyzer(sample_dataframe):
    """TechnicalAnalyzer instance."""
    return TechnicalAnalyzer(sample_dataframe)


@pytest.fixture(scope="function")
def sample_dataframe():
    """
    Create a minimal valid OHLCV DataFrame for unit tests.
    Does NOT require API calls.
    """
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = {
        'open': pd.Series(range(100, 200), index=dates, dtype=float),
        'high': pd.Series(range(101, 201), index=dates, dtype=float),
        'low': pd.Series(range(99, 199), index=dates, dtype=float),
        'close': pd.Series(range(100, 200), index=dates, dtype=float),
        'volume': pd.Series([1000000] * 100, index=dates, dtype=float)
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def invalid_dataframe():
    """DataFrame with missing required columns."""
    return pd.DataFrame({
        'price': [100, 101, 102],
        'vol': [1000000, 1000000, 1000000]
    })


@pytest.fixture(scope="function")
def short_dataframe():
    """DataFrame too short for technical analysis."""
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [100, 101, 102, 103, 104],
        'volume': [1000000] * 5
    }, index=dates)


@pytest.fixture(scope="function")
def monotone_increasing_df():
    """100-row DataFrame with strictly increasing close prices (100→199)."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    close = np.arange(100, 200, dtype=float)
    return pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1.0,
        'low': close - 1.0,
        'close': close,
        'volume': np.full(100, 1000000.0)
    }, index=dates)


@pytest.fixture(scope="function")
def declining_df():
    """50-row DataFrame with declining close prices (200→151)."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    close = np.linspace(200, 151, 50)
    return pd.DataFrame({
        'open': close + 0.5,
        'high': close + 1.0,
        'low': close - 1.0,
        'close': close,
        'volume': np.full(50, 1000000.0)
    }, index=dates)


@pytest.fixture(scope="function")
def risk_analyzer(sample_dataframe):
    """RiskAnalyzer instance with sample data."""
    from src.analysis.risk import RiskAnalyzer
    return RiskAnalyzer(sample_dataframe)


@pytest.fixture(scope="function")
def risk_analyzer_with_benchmark(sample_dataframe):
    """RiskAnalyzer instance with benchmark data."""
    from src.analysis.risk import RiskAnalyzer
    return RiskAnalyzer(sample_dataframe, benchmark_df=sample_dataframe)


@pytest.fixture(scope="function")
def dashboard(sample_dataframe):
    """Dashboard instance with sample data."""
    from src.reporting.dashboard import Dashboard
    return Dashboard(ticker='TEST', df=sample_dataframe)


@pytest.fixture(scope="function")
def full_dashboard(sample_dataframe):
    """Dashboard with both TechnicalAnalyzer and RiskAnalyzer attached."""
    from src.reporting.dashboard import Dashboard
    from src.analysis.risk import RiskAnalyzer
    technical = TechnicalAnalyzer(sample_dataframe)
    risk = RiskAnalyzer(sample_dataframe)
    return Dashboard(ticker='TEST', df=sample_dataframe, technical=technical, risk=risk)


@pytest.fixture
def multi_ticker_data():
    """Dict of 3 synthetic OHLCV DataFrames."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='B')

    def make_df(start_price, trend):
        prices = start_price + np.cumsum(np.random.randn(100) * 2 + trend)
        prices = np.abs(prices)
        return pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)

    return {
        'AAPL': make_df(150.0, 0.1),
        'MSFT': make_df(300.0, 0.05),
        'GOOGL': make_df(100.0, 0.08),
    }


@pytest.fixture
def portfolio_analyzer(multi_ticker_data):
    from src.analysis.portfolio import PortfolioAnalyzer
    return PortfolioAnalyzer(multi_ticker_data)


@pytest.fixture
def portfolio_analyzer_weighted(multi_ticker_data):
    from src.analysis.portfolio import PortfolioAnalyzer
    return PortfolioAnalyzer(multi_ticker_data, weights=[0.5, 0.3, 0.2])


@pytest.fixture
def simulator(sample_dataframe):
    from src.analysis.simulation import MonteCarloSimulator
    return MonteCarloSimulator(sample_dataframe, n_simulations=100, horizon_days=30)


@pytest.fixture
def sma_strategy():
    from src.backtesting.strategy import SMACrossover
    return SMACrossover(fast=5, slow=10)


@pytest.fixture
def rsi_strategy():
    from src.backtesting.strategy import RSIThreshold
    return RSIThreshold(oversold=40, overbought=60)


@pytest.fixture
def backtester(sample_dataframe, sma_strategy):
    from src.backtesting.backtester import Backtester
    return Backtester(sample_dataframe, sma_strategy)


@pytest.fixture(autouse=True)
def reset_logger(caplog):
    """Auto-reset logger state between tests."""
    caplog.set_level("DEBUG")
    yield
    caplog.clear()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no API)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (live API calls)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on test file names."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "unit" in item.nodeid or "technical" in item.nodeid:
            item.add_marker(pytest.mark.unit)
