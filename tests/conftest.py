"""
Pytest configuration and fixtures for integration testing.
Provides real API fixtures using yfinance for live data testing.
"""

import pytest
import pandas as pd
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
        data = fetcher.fetch_data(
            tickers=test_tickers,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Successfully fetched data: {len(data)} rows")
        yield data
    except Exception as e:
        logger.error(f"Failed to fetch test data: {e}")
        pytest.skip(f"API unavailable: {e}")


@pytest.fixture(scope="session")
def analyzer():
    """TechnicalAnalyzer instance."""
    return TechnicalAnalyzer()


@pytest.fixture(scope="function")
def sample_dataframe():
    """
    Create a minimal valid OHLCV DataFrame for unit tests.
    Does NOT require API calls.
    """
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = {
        'open': pd.Series(range(100, 200), index=dates),
        'high': pd.Series(range(101, 201), index=dates),
        'low': pd.Series(range(99, 199), index=dates),
        'close': pd.Series(range(100, 200), index=dates),
        'volume': pd.Series([1000000] * 100, index=dates)
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
