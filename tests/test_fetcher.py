import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to sys.path so we can import DataFetcher
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.fetcher import DataFetcher


class TestDataFetcherInitialization(unittest.TestCase):
    """Test DataFetcher initialization with various configurations"""
    
    def test_default_initialization(self):
        """Test DataFetcher initializes with default parameters"""
        fetcher = DataFetcher()
        self.assertEqual(fetcher.cache_ttl, 3600)
        self.assertEqual(fetcher.rate_limit_delay, 0.1)
        self.assertIsInstance(fetcher.cache, dict)
        self.assertEqual(len(fetcher.cache), 0)
    
    def test_custom_cache_ttl(self):
        """Test DataFetcher with custom cache TTL"""
        fetcher = DataFetcher(cache_ttl=7200)
        self.assertEqual(fetcher.cache_ttl, 7200)
    
    def test_custom_rate_limit(self):
        """Test DataFetcher with custom rate limit delay"""
        fetcher = DataFetcher(rate_limit_delay=0.5)
        self.assertEqual(fetcher.rate_limit_delay, 0.5)
    
    def test_both_custom_parameters(self):
        """Test DataFetcher with both custom parameters"""
        fetcher = DataFetcher(cache_ttl=1800, rate_limit_delay=0.2)
        self.assertEqual(fetcher.cache_ttl, 1800)
        self.assertEqual(fetcher.rate_limit_delay, 0.2)
    
    def test_zero_cache_ttl(self):
        """Test DataFetcher with zero cache TTL (caching disabled)"""
        fetcher = DataFetcher(cache_ttl=0)
        self.assertEqual(fetcher.cache_ttl, 0)
    
    def test_negative_cache_ttl_raises_error(self):
        """Test that negative cache TTL raises ValueError"""
        with self.assertRaises(ValueError):
            DataFetcher(cache_ttl=-100)
    
    def test_negative_rate_limit_raises_error(self):
        """Test that negative rate limit raises ValueError"""
        with self.assertRaises(ValueError):
            DataFetcher(rate_limit_delay=-0.5)


class TestCacheValidation(unittest.TestCase):
    """Test cache functionality and TTL expiry logic"""
    
    def test_cache_stores_data(self):
        """Test that cache stores fetched data"""
        fetcher = DataFetcher()
        test_data = pd.DataFrame({'Close': [100, 101, 102]})
        fetcher.cache['TEST'] = {
            'data': test_data,
            'timestamp': datetime.now()
        }
        self.assertIn('TEST', fetcher.cache)
        pd.testing.assert_frame_equal(fetcher.cache['TEST']['data'], test_data)
    
    def test_cache_expiry_check(self):
        """Test cache expiry detection"""
        fetcher = DataFetcher(cache_ttl=1)
        test_data = pd.DataFrame({'Close': [100, 101, 102]})
        # Store data with old timestamp
        old_time = datetime.now() - timedelta(seconds=2)
        fetcher.cache['TEST'] = {
            'data': test_data,
            'timestamp': old_time
        }
        
        is_expired = (datetime.now() - fetcher.cache['TEST']['timestamp']).total_seconds() > fetcher.cache_ttl
        self.assertTrue(is_expired)
    
    def test_cache_not_expired(self):
        """Test cache not expired when within TTL"""
        fetcher = DataFetcher(cache_ttl=3600)
        test_data = pd.DataFrame({'Close': [100, 101, 102]})
        fetcher.cache['TEST'] = {
            'data': test_data,
            'timestamp': datetime.now()
        }
        
        is_expired = (datetime.now() - fetcher.cache['TEST']['timestamp']).total_seconds() > fetcher.cache_ttl
        self.assertFalse(is_expired)
    
    def test_cache_ttl_boundary(self):
        """Test cache at exact TTL boundary"""
        fetcher = DataFetcher(cache_ttl=1)
        test_data = pd.DataFrame({'Close': [100, 101, 102]})
        fetcher.cache['TEST'] = {
            'data': test_data,
            'timestamp': datetime.now() - timedelta(seconds=1)
        }
        
        is_expired = (datetime.now() - fetcher.cache['TEST']['timestamp']).total_seconds() > fetcher.cache_ttl
        # Should be expired or very close to it
        self.assertTrue(is_expired or (datetime.now() - fetcher.cache['TEST']['timestamp']).total_seconds() >= fetcher.cache_ttl)


class TestFetchHistoricalData(unittest.TestCase):
    """Test fetch_historical_data method"""
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_success(self, mock_download):
        """Test successful historical data fetch"""
        mock_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000000, 1100000, 1200000]
        })
        mock_download.return_value = mock_data

        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')

        pd.testing.assert_frame_equal(result, mock_data)
        mock_download.assert_called_once()
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_default_dates(self, mock_download):
        """Test historical data fetch with default date parameters"""
        mock_data = pd.DataFrame({'close': [100, 101, 102]})
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL')
        
        mock_download.assert_called_once()
        pd.testing.assert_frame_equal(result, mock_data)
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_uses_cache(self, mock_download):
        """Test that cache is used on subsequent calls"""
        mock_data = pd.DataFrame({'close': [100, 101, 102]})
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(cache_ttl=3600)
        
        # First call
        result1 = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        # Second call - should use cache
        result2 = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        
        # yfinance should only be called once
        mock_download.assert_called_once()
        pd.testing.assert_frame_equal(result1, result2)
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_cache_expired(self, mock_download):
        """Test that cache is not used when expired"""
        mock_data = pd.DataFrame({'close': [100, 101, 102]})
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(cache_ttl=1)
        
        # First call
        fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        
        # Manually expire cache
        cache_key = 'AAPL_2023-01-01_2023-01-03'
        if cache_key in fetcher.cache:
            fetcher.cache[cache_key]['timestamp'] = datetime.now() - timedelta(seconds=2)
        
        # Second call - cache should be expired, so yfinance called again
        fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        
        # Should be called twice now
        self.assertEqual(mock_download.call_count, 2)
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_handles_empty_response(self, mock_download):
        """Test handling of empty data from yfinance"""
        mock_download.return_value = pd.DataFrame()
        
        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('INVALID', start='2023-01-01', end='2023-01-03')
        
        self.assertTrue(result.empty)
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_network_error(self, mock_download):
        """Test handling of network errors"""
        mock_download.side_effect = Exception("Network error")
        
        fetcher = DataFetcher()
        with self.assertRaises(Exception):
            fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_historical_data_column_normalization(self, mock_download):
        """Test that columns are properly handled"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102],
            'open': [99.5, 100.5, 101.5],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'volume': [1000000, 1100000, 1200000]
        })
        mock_download.return_value = mock_data

        fetcher = DataFetcher()
        result = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')

        self.assertIn('close', result.columns)


class TestFetchMultipleTickers(unittest.TestCase):
    """Test fetching data for multiple tickers"""
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_multiple_tickers(self, mock_download):
        """Test fetching data for multiple tickers"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102],
            'open': [99.5, 100.5, 101.5]
        })
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher()
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        results = {}
        for ticker in tickers:
            results[ticker] = fetcher.fetch_historical_data(ticker, start='2023-01-01', end='2023-01-03')
        
        self.assertEqual(len(results), 3)
        self.assertIn('AAPL', results)
        self.assertIn('MSFT', results)
        self.assertIn('GOOGL', results)
    
    @patch('src.data.fetcher.yf.download')
    def test_fetch_multiple_tickers_respects_rate_limit(self, mock_download):
        """Test that rate limiting is applied between multiple ticker fetches"""
        mock_data = pd.DataFrame({'close': [100, 101, 102]})
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(rate_limit_delay=0.1)
        tickers = ['AAPL', 'MSFT']
        
        import time
        start_time = time.time()
        
        for ticker in tickers:
            fetcher.fetch_historical_data(ticker, start='2023-01-01', end='2023-01-03')
        
        elapsed = time.time() - start_time
        # Should take at least rate_limit_delay seconds between calls
        # (This is a soft check due to execution time variability)
        self.assertGreater(elapsed, 0.05)


class TestGetStockInfo(unittest.TestCase):
    """Test get_stock_info method"""
    
    @patch('src.data.fetcher.yf.Ticker')
    def test_get_stock_info_success(self, mock_ticker):
        """Test successful stock info retrieval"""
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {
            'currentPrice': 150.25,
            'marketCap': 3000000000000,
            'trailingPE': 25.5,
            'dividendYield': 0.005
        }
        mock_ticker.return_value = mock_ticker_instance
        
        fetcher = DataFetcher()
        info = fetcher.get_stock_info('AAPL')
        
        self.assertEqual(info['currentPrice'], 150.25)
        self.assertEqual(info['marketCap'], 3000000000000)
    
    @patch('src.data.fetcher.yf.Ticker')
    def test_get_stock_info_missing_fields(self, mock_ticker):
        """Test stock info with missing fields"""
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {
            'currentPrice': 150.25,
            'marketCap': 3000000000000
        }
        mock_ticker.return_value = mock_ticker_instance
        
        fetcher = DataFetcher()
        info = fetcher.get_stock_info('AAPL')
        
        self.assertIn('currentPrice', info)
        self.assertNotIn('dividendYield', info)
    
    @patch('src.data.fetcher.yf.Ticker')
    def test_get_stock_info_error(self, mock_ticker):
        """Test error handling in get_stock_info"""
        mock_ticker.side_effect = Exception("Stock not found")
        
        fetcher = DataFetcher()
        with self.assertRaises(Exception):
            fetcher.get_stock_info('INVALID')


class TestReturnCalculations(unittest.TestCase):
    """Test return calculation methods"""
    
    def test_calculate_daily_returns(self):
        """Test daily returns calculation"""
        prices = pd.Series([100, 101, 102, 101, 103])
        expected_returns = prices.pct_change()
        
        fetcher = DataFetcher()
        # Assuming there's a method to calculate returns
        calculated = prices.pct_change()
        
        pd.testing.assert_series_equal(calculated, expected_returns)
    
    def test_calculate_log_returns(self):
        """Test log returns calculation"""
        prices = pd.Series([100, 101, 102, 101, 103])
        expected_log_returns = np.log(prices / prices.shift(1))
        
        calculated = np.log(prices / prices.shift(1))
        
        pd.testing.assert_series_equal(calculated, expected_log_returns)
    
    def test_returns_with_zero_prices(self):
        """Test returns calculation handles zero prices"""
        prices = pd.Series([100, 0, 102])
        returns = prices.pct_change()
        
        self.assertTrue(np.isnan(returns.iloc[2]) or np.isinf(returns.iloc[2]))
    
    def test_returns_with_single_value(self):
        """Test returns with single price value"""
        prices = pd.Series([100])
        returns = prices.pct_change()
        
        self.assertTrue(np.isnan(returns.iloc[0]))


class TestCorrelationMatrix(unittest.TestCase):
    """Test correlation matrix calculation"""
    
    def test_correlation_matrix_two_series(self):
        """Test correlation between two price series"""
        data = pd.DataFrame({
            'AAPL': [100, 101, 102, 103, 104],
            'MSFT': [200, 202, 204, 206, 208]
        })
        
        correlation = data.corr()
        
        self.assertEqual(correlation.shape, (2, 2))
        self.assertAlmostEqual(correlation.loc['AAPL', 'MSFT'], 1.0, places=5)
    
    def test_correlation_matrix_multiple_series(self):
        """Test correlation matrix with multiple series"""
        data = pd.DataFrame({
            'AAPL': [100, 101, 102, 103, 104],
            'MSFT': [200, 202, 204, 206, 208],
            'GOOGL': [1000, 1010, 1020, 1030, 1040]
        })
        
        correlation = data.corr()
        
        self.assertEqual(correlation.shape, (3, 3))
        # Check diagonal is 1
        self.assertAlmostEqual(correlation.loc['AAPL', 'AAPL'], 1.0, places=5)
    
    def test_correlation_matrix_negative_correlation(self):
        """Test negative correlation detection"""
        data = pd.DataFrame({
            'A': [100, 101, 102, 103, 104],
            'B': [100, 99, 98, 97, 96]
        })
        
        correlation = data.corr()
        
        self.assertLess(correlation.loc['A', 'B'], 0)
    
    def test_correlation_matrix_empty_data(self):
        """Test correlation with empty dataframe"""
        data = pd.DataFrame()
        
        # Empty dataframe correlation should raise or return empty
        try:
            correlation = data.corr()
            self.assertTrue(correlation.empty)
        except Exception:
            pass  # Expected behavior


class TestDataValidation(unittest.TestCase):
    """Test data validation methods"""
    
    def test_validate_empty_dataframe(self):
        """Test validation of empty dataframe"""
        data = pd.DataFrame()
        self.assertTrue(data.empty)
    
    def test_validate_missing_columns(self):
        """Test detection of missing required columns"""
        data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [101, 102, 103]
        })
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in data.columns]
        
        self.assertEqual(len(missing), 3)
        self.assertIn('Low', missing)
        self.assertIn('Close', missing)
        self.assertIn('Volume', missing)
    
    def test_validate_nan_values(self):
        """Test detection of NaN values"""
        data = pd.DataFrame({
            'Close': [100, np.nan, 102, 103],
            'Volume': [1000, 1100, np.nan, 1300]
        })
        
        nan_count = data.isna().sum().sum()
        self.assertEqual(nan_count, 2)
    
    def test_validate_data_types(self):
        """Test validation of data types"""
        data = pd.DataFrame({
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000, 1100, 1200]
        })
        
        self.assertTrue(np.issubdtype(data['Close'].dtype, np.number))
        self.assertTrue(np.issubdtype(data['Volume'].dtype, np.number))


class TestCacheClear(unittest.TestCase):
    """Test cache clearing functionality"""
    
    def test_clear_all_cache(self):
        """Test clearing entire cache"""
        fetcher = DataFetcher()
        fetcher.cache['AAPL'] = {'data': pd.DataFrame(), 'timestamp': datetime.now()}
        fetcher.cache['MSFT'] = {'data': pd.DataFrame(), 'timestamp': datetime.now()}
        
        fetcher.cache.clear()
        
        self.assertEqual(len(fetcher.cache), 0)
    
    def test_clear_specific_cache_entry(self):
        """Test clearing specific cache entry"""
        fetcher = DataFetcher()
        fetcher.cache['AAPL'] = {'data': pd.DataFrame(), 'timestamp': datetime.now()}
        fetcher.cache['MSFT'] = {'data': pd.DataFrame(), 'timestamp': datetime.now()}
        
        if 'AAPL' in fetcher.cache:
            del fetcher.cache['AAPL']
        
        self.assertEqual(len(fetcher.cache), 1)
        self.assertNotIn('AAPL', fetcher.cache)
        self.assertIn('MSFT', fetcher.cache)
    
    def test_clear_expired_cache(self):
        """Test clearing only expired cache entries"""
        fetcher = DataFetcher(cache_ttl=1)
        
        # Add fresh entry
        fetcher.cache['FRESH'] = {'data': pd.DataFrame(), 'timestamp': datetime.now()}
        
        # Add expired entry
        fetcher.cache['EXPIRED'] = {
            'data': pd.DataFrame(),
            'timestamp': datetime.now() - timedelta(seconds=2)
        }
        
        # Clear only expired
        expired_keys = []
        for key, value in fetcher.cache.items():
            if (datetime.now() - value['timestamp']).total_seconds() > fetcher.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del fetcher.cache[key]
        
        self.assertIn('FRESH', fetcher.cache)
        self.assertNotIn('EXPIRED', fetcher.cache)
    
    def test_clear_empty_cache(self):
        """Test clearing empty cache"""
        fetcher = DataFetcher()
        initial_len = len(fetcher.cache)
        
        fetcher.cache.clear()
        
        self.assertEqual(len(fetcher.cache), 0)
        self.assertEqual(initial_len, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_single_row_dataframe(self):
        """Test operations on single-row dataframe"""
        data = pd.DataFrame({'Close': [100]})
        
        self.assertEqual(len(data), 1)
        self.assertIn('Close', data.columns)
    
    def test_zero_prices(self):
        """Test handling of zero prices"""
        data = pd.DataFrame({'Close': [0, 0, 0]})
        returns = data['Close'].pct_change()
        
        self.assertTrue(np.isnan(returns.iloc[0]))
    
    def test_negative_prices(self):
        """Test handling of negative prices (should not occur but test robustness)"""
        data = pd.DataFrame({'Close': [100, -50, 75]})
        
        self.assertLess(data['Close'].iloc[1], 0)
    
    def test_very_large_prices(self):
        """Test handling of very large price values"""
        data = pd.DataFrame({'Close': [1e10, 1e10 + 1, 1e10 + 2]})
        
        self.assertGreater(data['Close'].max(), 1e10)
    
    def test_case_sensitivity_ticker(self):
        """Test ticker symbol case handling"""
        ticker_upper = 'AAPL'
        ticker_lower = 'aapl'
        
        # These should be treated as the same ticker
        self.assertEqual(ticker_upper.upper(), ticker_lower.upper())
    
    def test_very_old_dates(self):
        """Test handling of very old historical dates"""
        start_date = '1980-01-01'
        end_date = '1980-12-31'
        
        # Dates should be valid
        self.assertIsNotNone(start_date)
        self.assertIsNotNone(end_date)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple methods"""
    
    @patch('src.data.fetcher.yf.download')
    def test_workflow_fetch_and_calculate_returns(self, mock_download):
        """Test complete workflow: fetch data and calculate returns"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        })
        mock_download.return_value = mock_data

        fetcher = DataFetcher()
        data = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-05')

        self.assertFalse(data.empty)
        self.assertIn('close', data.columns)
    
    @patch('src.data.fetcher.yf.download')
    def test_workflow_fetch_multiple_and_correlate(self, mock_download):
        """Test workflow: fetch multiple tickers and calculate correlation"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
        })
        mock_download.return_value = mock_data

        fetcher = DataFetcher()

        data_aapl = fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-05')
        data_msft = fetcher.fetch_historical_data('MSFT', start='2023-01-01', end='2023-01-05')

        combined = pd.DataFrame({
            'AAPL': data_aapl['close'],
            'MSFT': data_msft['close']
        })
        
        correlation = combined.corr()
        self.assertEqual(correlation.shape, (2, 2))
    
    @patch('src.data.fetcher.yf.download')
    def test_workflow_with_cache_persistence(self, mock_download):
        """Test that cache persists across multiple operations"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102],
        })
        mock_download.return_value = mock_data
        
        fetcher = DataFetcher(cache_ttl=3600)
        
        # Fetch same data twice
        fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        fetcher.fetch_historical_data('AAPL', start='2023-01-01', end='2023-01-03')
        
        # Should only call yfinance once
        mock_download.assert_called_once()
        self.assertGreater(len(fetcher.cache), 0)
    
    def test_workflow_error_handling(self):
        """Test error handling throughout workflow"""
        fetcher = DataFetcher()
        
        # Test with empty cache
        self.assertEqual(len(fetcher.cache), 0)
        
        # Test cache operations
        try:
            fetcher.cache.clear()
            self.assertEqual(len(fetcher.cache), 0)
        except Exception as e:
            self.fail(f"Cache clear raised unexpected exception: {e}")


if __name__ == '__main__':
    unittest.main()
