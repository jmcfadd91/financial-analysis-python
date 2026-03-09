"""
Pytest configuration and shared fixtures for test suite.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    close_prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    
    data = pd.DataFrame({
        'date': dates,
        'open': close_prices + np.random.randn(len(dates)),
        'high': close_prices + abs(np.random.randn(len(dates)) * 2),
        'low': close_prices - abs(np.random.randn(len(dates)) * 2),
        'close': close_prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    data.set_index('date', inplace=True)
    return data


@pytest.fixture
def small_ohlcv_data():
    """Generate small OHLCV dataset (50 days)."""
    dates = pd.date_range(start='2023-11-01', end='2023-12-20', freq='D')
    np.random.seed(123)
    
    close_prices = 150 + np.cumsum(np.random.randn(len(dates)) * 1.5)
    
    data = pd.DataFrame({
        'date': dates,
        'open': close_prices + np.random.randn(len(dates)),
        'high': close_prices + abs(np.random.randn(len(dates)) * 1.5),
        'low': close_prices - abs(np.random.randn(len(dates)) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(500000, 5000000, len(dates))
    })
    
    data.set_index('date', inplace=True)
    return data


@pytest.fixture
def test_tickers():
    """Test ticker symbols."""
    return ['AAPL', 'MSFT', 'GOOGL']


@pytest.fixture
def date_range():
    """Standard date range for testing."""
    return {
        'start': '2023-01-01',
        'end': '2023-12-31'
    }


@pytest.fixture
def invalid_tickers():
    """Invalid ticker symbols for error testing."""
    return ['INVALID', 'NOTREAL', 'FAKESTOCK']


@pytest.fixture
def technical_params():
    """Standard technical analysis parameters."""
    return {
        'sma_period': 20,
        'ema_period': 12,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bb_period': 20,
        'bb_std': 2,
        'atr_period': 14
    }
