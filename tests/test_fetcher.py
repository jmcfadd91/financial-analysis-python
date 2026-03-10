"""
Unit tests for DataFetcher class
Tests cover initialization, data fetching, caching, calculations, and error handling
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import sys
import os

# Add src to path so we can import DataFetcher
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.fetcher import DataFetcher


class TestDataFetcherInitialization:
    """Test DataFetcher initialization and setup"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        fetcher = DataFetcher()
        assert fetcher.cache_dir == "./data/cache"
        assert fetcher.cache_ttl == 3600
        assert fetcher.rate_limit_delay == 0.5
        assert fetcher.data_cache == {}
        assert fetcher.cache_timestamps == {}

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        fetcher = DataFetcher(cache_dir="/custom/path", cache_ttl=7200)
        assert fetcher.cache_dir == "/custom/path"
        assert fetcher.cache_ttl == 7200
        assert fetcher.data_cache == {}


class TestCacheValidation:
    """Test cache validation and TTL logic"""

    def test_is_cache_valid_when_not_exists(self):
        """Test that non-existent cache key returns False"""
        fetcher = DataFetcher()
        assert fetcher._is_cache_valid("nonexistent_key") is False

    def test_is_cache_valid_when_fresh(self):
        """Test that fresh cache returns True"""
        fetcher = DataFetcher(cache_ttl=3600)
        cache_key = "test_key"
        fetcher.cache_timestamps[cache_key] = time.time()
        
        assert fetcher._is_cache_valid(cache_key) is True

    def test_is_cache_valid_when_expired(self):
        """Test that expired cache returns False"""
        fetcher = DataFetcher(cache_ttl=1)  # 1 second TTL
        cache_key = "test_key"
        fetcher.cache_timestamps[cache_key] = time.time() - 10  # 10 seconds ago
        
        assert fetcher._is_cache_valid(cache_key) is False

    def test_is_cache_valid_at_ttl_boundary(self):
        """Test cache validity at TTL boundary"""
        fetcher = DataFetcher(cache_ttl=2)
        cache_key = "test_key"
        fetcher.cache_timestamps[cache_key] = time.time() - 1.5  # 1.5 seconds ago
        
        assert fetcher._is_cache_valid(cache_key) is True


class TestFetchHistoricalData:
    """Test fetching historical data"""

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_success(self, mock_download):
        """Test successful fetch of historical data"""
        # Create mock data
        dates = pd.date_range(start='2023-01-01', periods=10)
        mock_data = pd.DataFrame({
            'Open': np.random.rand(10) * 100,
            'High': np.random.rand(10) * 100,
            'Low': np.random.rand(10) * 100,
            'Close': np.random.rand(10) * 100,
            'Volume': np.random.randint(1000000, 10000000, 10)
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-10')
        
        assert not result.empty
        assert len(result) == 10
        assert 'close' in result.columns
        mock_download.assert_called_once()

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_with_defaults(self, mock_download):
        """Test fetch with default dates (should be 1 year ago)"""
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000000] * 5
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL')
        
        assert not result.empty
        # Verify yf.download was called with date parameters
        mock_download.assert_called_once()

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_caching(self, mock_download):
        """Test that fetched data is cached"""
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000000] * 5
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        
        # First fetch
        result1 = fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-05')
        # Second fetch (should use cache)
        result2 = fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-05')
        
        # yf.download should only be called once (second call uses cache)
        assert mock_download.call_count == 1
        assert result1.equals(result2)

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_cache_expiry(self, mock_download):
        """Test that cache expires after TTL"""
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000000] * 5
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(cache_ttl=1)  # 1 second TTL
        
        # First fetch
        fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-05')
        
        # Manually expire cache
        cache_key = 'AAPL_2023-01-01_2023-01-05_1d'
        fetcher.cache_timestamps[cache_key] = time.time() - 10
        
        # Second fetch (should bypass cache due to expiry)
        fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-05')
        
        # yf.download should be called twice
        assert mock_download.call_count == 2

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_error_handling(self, mock_download):
        """Test error handling when fetch fails"""
        mock_download.side_effect = Exception("API Error")
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('INVALID_TICKER')
        
        assert result.empty
        assert isinstance(result, pd.DataFrame)

    @patch('data.fetcher.yf.download')
    def test_fetch_historical_data_column_normalization(self, mock_download):
        """Test that column names are normalized to lowercase"""
        dates = pd.date_range(start='2023-01-01', periods=3)
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [102, 103, 104],
            'Low': [99, 100, 101],
            'Close': [101, 102, 103],
            'Volume': [1000000, 1100000, 1200000]
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL')
        
        # Check that columns are lowercase
        assert 'close' in result.columns
        assert 'open' in result.columns
        assert 'volume' in result.columns


class TestFetchMultipleTickers:
    """Test fetching data for multiple tickers"""

    @patch('data.fetcher.yf.download')
    def test_fetch_multiple_tickers(self, mock_download):
        """Test fetching data for multiple tickers"""
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000000] * 5
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        results = fetcher.fetch_multiple_tickers(tickers)
        
        assert len(results) == 3
        assert 'AAPL' in results
        assert 'MSFT' in results
        assert 'GOOGL' in results
        # Should be called 3 times (one per ticker)
        assert mock_download.call_count == 3

    @patch('data.fetcher.yf.download')
    def test_fetch_multiple_tickers_with_rate_limiting(self, mock_download):
        """Test that rate limiting is applied between requests"""
        dates = pd.date_range(start='2023-01-01', periods=5)
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000000] * 5
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(cache_ttl=0)  # Disable cache to force fetches
        tickers = ['AAPL', 'MSFT']
        
        start_time = time.time()
        results = fetcher.fetch_multiple_tickers(tickers)
        elapsed = time.time() - start_time
        
        # Should have delay between requests (at least rate_limit_delay)
        assert elapsed >= fetcher.rate_limit_delay


class TestGetStockInfo:
    """Test getting stock information"""

    @patch('data.fetcher.yf.Ticker')
    def test_get_stock_info_success(self, mock_ticker):
        """Test successful retrieval of stock info"""
        mock_info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 2800000000000,
            'trailingPE': 25.5,
            'dividendYield': 0.005,
            'fiftyTwoWeekHigh': 195.0,
            'fiftyTwoWeekLow': 145.0,
            'currentPrice': 180.0
        }
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance
        
        fetcher = DataFetcher()
        info = fetcher.get_stock_info('AAPL')
        
        assert info['ticker'] == 'AAPL'
        assert info['name'] == 'Apple Inc.'
        assert info['sector'] == 'Technology'
        assert info['error'] is False
        assert info['market_cap'] == 2800000000000

    @patch('data.fetcher.yf.Ticker')
    def test_get_stock_info_error_handling(self, mock_ticker):
        """Test error handling when stock info fetch fails"""
        mock_ticker.side_effect = Exception("Ticker not found")
        
        fetcher = DataFetcher()
        info = fetcher.get_stock_info('INVALID')
        
        assert info['error'] is True
        assert 'error_message' in info
        assert info['ticker'] == 'INVALID'


class TestReturnCalculations:
    """Test return calculation methods"""

    def test_calculate_returns_basic(self):
        """Test basic daily return calculation"""
        data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]
        })
        
        fetcher = DataFetcher()
        returns = fetcher.calculate_returns(data)
        
        assert len(returns) == 5
        assert returns.iloc[0] != returns.iloc[0]  # First value is NaN
        assert np.isclose(returns.iloc[1], 0.01, atol=0.0001)  # 101/100 - 1 ≈ 0.01

    def test_calculate_returns_missing_column(self):
        """Test error handling for missing close column"""
        data = pd.DataFrame({
            'price': [100, 101, 102]
        })
        
        fetcher = DataFetcher()
        returns = fetcher.calculate_returns(data)
        
        assert returns.empty

    def test_calculate_log_returns_basic(self):
        """Test basic log return calculation"""
        data = pd.DataFrame({
            'close': [100.0, 101.0, 102.0, 103.0]
        })
        
        fetcher = DataFetcher()
        log_returns = fetcher.calculate_log_returns(data)
        
        assert len(log_returns) == 4
        assert log_returns.iloc[0] != log_returns.iloc[0]  # First value is NaN

    def test_calculate_log_returns_missing_column(self):
        """Test error handling for missing close column in log returns"""
        data = pd.DataFrame({
            'price': [100, 101, 102]
        })
        
        fetcher = DataFetcher()
        log_returns = fetcher.calculate_log_returns(data)
        
        assert log_returns.empty


class TestCorrelationMatrix:
    """Test correlation matrix calculation"""

    @patch('data.fetcher.yf.download')
    def test_get_correlation_matrix(self, mock_download):
        """Test correlation matrix calculation for multiple assets"""
        dates = pd.date_range(start='2023-01-01', periods=20)
        
        # Create data with known correlation
        mock_data = pd.DataFrame({
            'Close': np.arange(100, 120),
            'Volume': [1000000] * 20
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        corr_matrix = fetcher.get_correlation_matrix(tickers)
        
        assert not corr_matrix.empty
        assert len(corr_matrix) == 3
        assert corr_matrix.shape == (3, 3)

    @patch('data.fetcher.yf.download')
    def test_get_correlation_matrix_empty_data(self, mock_download):
        """Test correlation matrix with empty data"""
        mock_download.return_value = pd.DataFrame()
        
        fetcher = DataFetcher()
        corr_matrix = fetcher.get_correlation_matrix(['INVALID1', 'INVALID2'])
        
        assert corr_matrix.empty


class TestDataValidation:
    """Test data validation"""

    def test_validate_data_empty_dataframe(self):
        """Test validation of empty DataFrame"""
        fetcher = DataFetcher()
        data = pd.DataFrame()
        
        is_valid, message = fetcher.validate_data(data)
        
        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_data_missing_columns(self):
        """Test validation with missing required columns"""
        fetcher = DataFetcher()
        data = pd.DataFrame({
            'close': [100, 101, 102]
        })
        
        is_valid, message = fetcher.validate_data(data)
        
        assert is_valid is False
        assert "missing columns" in message.lower()

    def test_validate_data_success(self):
        """Test successful validation of valid data"""
        fetcher = DataFetcher()
        data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000000, 1100000, 1200000]
        })
        
        is_valid, message = fetcher.validate_data(data)
        
        assert is_valid is True
        assert "passed" in message.lower()

    def test_validate_data_with_nan_values(self):
        """Test validation with NaN values (should warn but pass)"""
        fetcher = DataFetcher()
        data = pd.DataFrame({
            'open': [100, 101, np.nan],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000000, 1100000, 1200000]
        })
        
        is_valid, message = fetcher.validate_data(data)
        
        assert is_valid is True


class TestCacheManagement:
    """Test cache clearing and management"""

    def test_clear_cache_all(self):
        """Test clearing entire cache"""
        fetcher = DataFetcher()
        fetcher.data_cache['key1'] = pd.DataFrame({'data': [1, 2, 3]})
        fetcher.data_cache['key2'] = pd.DataFrame({'data': [4, 5, 6]})
        fetcher.cache_timestamps['key1'] = time.time()
        fetcher.cache_timestamps['key2'] = time.time()
        
        cleared = fetcher.clear_cache()
        
        assert cleared == 2
        assert len(fetcher.data_cache) == 0
        assert len(fetcher.cache_timestamps) == 0

    def test_clear_cache_older_than(self):
        """Test clearing cache entries older than specified hours"""
        fetcher = DataFetcher()
        
        # Add fresh entry
        fetcher.data_cache['fresh'] = pd.DataFrame({'data': [1, 2, 3]})
        fetcher.cache_timestamps['fresh'] = time.time()
        
        # Add old entry
        fetcher.data_cache['old'] = pd.DataFrame({'data': [4, 5, 6]})
        fetcher.cache_timestamps['old'] = time.time() - (3 * 3600)  # 3 hours ago
        
        cleared = fetcher.clear_cache(older_than_hours=1)
        
        assert cleared == 1
        assert 'fresh' in fetcher.data_cache
        assert 'old' not in fetcher.data_cache

    def test_clear_cache_empty(self):
        """Test clearing empty cache"""
        fetcher = DataFetcher()
        
        cleared = fetcher.clear_cache()
        
        assert cleared == 0


class TestIntegration:
    """Integration tests combining multiple features"""

    @patch('data.fetcher.yf.download')
    def test_full_workflow(self, mock_download):
        """Test complete workflow from fetch to analysis"""
        dates = pd.date_range(start='2023-01-01', periods=30)
        prices = np.linspace(100, 120, 30)
        
        mock_data = pd.DataFrame({
            'Open': prices + np.random.rand(30),
            'High': prices + 2,
            'Low': prices - 1,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 30)
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        
        # Fetch data
        data = fetcher.fetch_historical_data('AAPL', '2023-01-01', '2023-01-30')
        
        # Validate data
        is_valid, msg = fetcher.validate_data(data)
        assert is_valid
        
        # Calculate returns
        returns = fetcher.calculate_returns(data)
        assert len(returns) == len(data)
        
        # Check statistics
        assert returns.std() > 0
        assert not returns.isna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
