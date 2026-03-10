"""
Data Fetcher Module - Retrieve financial data from multiple sources
Bloomberg-style financial analysis project
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
import logging
import time

# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Unified data fetcher for stocks, ETFs, and cryptocurrencies
    Supports multiple timeframes and data sources
    """

    def __init__(self, cache_ttl: int = 3600, rate_limit_delay: float = 0.1):
        """
        Initialize DataFetcher

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            rate_limit_delay: Delay between API calls in seconds (default: 0.1)
        """
        if cache_ttl < 0:
            raise ValueError("cache_ttl must be non-negative")
        if rate_limit_delay < 0:
            raise ValueError("rate_limit_delay must be non-negative")

        self.cache = {}
        self.cache_ttl = cache_ttl
        self.rate_limit_delay = rate_limit_delay

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is still valid based on TTL

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache is valid, False if expired
        """
        if cache_key not in self.cache:
            return False

        elapsed = (datetime.now() - self.cache[cache_key]['timestamp']).total_seconds()
        return elapsed < self.cache_ttl

    def fetch_historical_data(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a single asset

        Args:
            ticker: Asset ticker (e.g., 'AAPL', 'BTC-USD')
            start: Start date (YYYY-MM-DD), default: 1 year ago
            end: End date (YYYY-MM-DD), default: today
            interval: '1d', '1wk', '1mo', '1h', '5m', etc.

        Returns:
            DataFrame with OHLCV data
        """
        if start is None:
            start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"{ticker}_{start}_{end}"

        # Check cache with TTL validation
        if cache_key in self.cache and self._is_cache_valid(cache_key):
            logger.info(f"Loading {ticker} from cache (valid)")
            return self.cache[cache_key]['data']

        logger.info(f"Fetching {ticker} from {start} to {end}")
        data = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False
        )

        # Cache the data with timestamp
        self.cache[cache_key] = {'data': data, 'timestamp': datetime.now()}

        logger.info(f"Successfully fetched {len(data)} records for {ticker}")

        # Rate limiting - prevent API throttling
        time.sleep(self.rate_limit_delay)

        return data

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers with rate limiting

        Args:
            tickers: List of ticker symbols
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            interval: Time interval

        Returns:
            Dictionary with ticker as key, DataFrame as value
        """
        results = {}
        for i, ticker in enumerate(tickers):
            results[ticker] = self.fetch_historical_data(
                ticker, start, end, interval
            )
            # Add delay between requests (except for cached data)
            if i < len(tickers) - 1:
                time.sleep(self.rate_limit_delay)

        return results

    def get_stock_info(self, ticker: str) -> Dict:
        """
        Get company info and current metrics

        Args:
            ticker: Stock ticker

        Returns:
            Dictionary with company info from yfinance
        """
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.info

    def calculate_returns(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate daily returns from OHLCV data

        Args:
            data: DataFrame with 'close' or 'Close' column

        Returns:
            Series of daily returns
        """
        close_col = 'close' if 'close' in data.columns else 'Close'
        if close_col not in data.columns:
            logger.error("DataFrame must contain 'close' or 'Close' column")
            return pd.Series()

        return data[close_col].pct_change()

    def calculate_log_returns(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate log returns from OHLCV data

        Args:
            data: DataFrame with 'close' or 'Close' column

        Returns:
            Series of log returns
        """
        close_col = 'close' if 'close' in data.columns else 'Close'
        if close_col not in data.columns:
            logger.error("DataFrame must contain 'close' or 'Close' column")
            return pd.Series()

        return np.log(data[close_col] / data[close_col].shift(1))

    def get_correlation_matrix(
        self,
        tickers: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between multiple assets

        Args:
            tickers: List of ticker symbols
            start: Start date
            end: End date

        Returns:
            Correlation matrix DataFrame
        """
        data_dict = self.fetch_multiple_tickers(tickers, start, end)

        # Extract closing prices
        closes = pd.DataFrame()
        for ticker, data in data_dict.items():
            if not data.empty:
                close_col = 'close' if 'close' in data.columns else 'Close'
                closes[ticker] = data[close_col]

        # Calculate returns correlation - improved NaN handling
        returns = closes.pct_change().dropna(how='any')

        if returns.empty:
            logger.warning("Insufficient data for correlation calculation")
            return pd.DataFrame()

        correlation = returns.corr()

        logger.info(f"Correlation matrix calculated for {len(tickers)} assets")
        return correlation

    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate downloaded data quality

        Args:
            data: DataFrame to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if data.empty:
            return False, "DataFrame is empty"

        required_columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in data.columns]

        if missing:
            return False, f"Missing columns: {missing}"

        # Check for NaN values
        nan_count = data.isnull().sum().sum()
        if nan_count > 0:
            logger.warning(f"Found {nan_count} NaN values in data")

        return True, "Data validation passed"

    def clear_cache(self, older_than_hours: Optional[int] = None) -> int:
        """
        Clear cache entries, optionally only older than specified hours

        Args:
            older_than_hours: Remove cache entries older than N hours (None = clear all)

        Returns:
            Number of entries cleared
        """
        if older_than_hours is None:
            cleared = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared {cleared} cache entries")
            return cleared

        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        keys_to_remove = [
            key for key, value in self.cache.items()
            if value['timestamp'] < cutoff
        ]

        for key in keys_to_remove:
            del self.cache[key]

        logger.info(f"Cleared {len(keys_to_remove)} cache entries older than {older_than_hours} hours")
        return len(keys_to_remove)


if __name__ == "__main__":
    # Example usage
    fetcher = DataFetcher()

    # Fetch single ticker
    aapl = fetcher.fetch_historical_data("AAPL", interval="1d")
    print(f"\nAAPL Data:\n{aapl.head()}")

    # Get stock info
    info = fetcher.get_stock_info("AAPL")
    print(f"\nAAPL Info:\n{info}")

    # Calculate returns
    returns = fetcher.calculate_returns(aapl)
    print(f"\nReturns Stats:\n{returns.describe()}")

    # Correlation matrix
    tickers = ["AAPL", "MSFT", "GOOGL"]
    corr = fetcher.get_correlation_matrix(tickers)
    print(f"\nCorrelation Matrix:\n{corr}")
