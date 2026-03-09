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

    def __init__(self, cache_dir: str = "./data/cache", cache_ttl: int = 3600):
        """
        Initialize DataFetcher
        
        Args:
            cache_dir: Directory to cache downloaded data
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.data_cache = {}
        self.cache_timestamps = {}  # Track cache entry timestamps
        self.cache_ttl = cache_ttl
        self.rate_limit_delay = 0.5  # 500ms delay between API calls

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is still valid based on TTL
        
        Args:
            cache_key: Cache key to check
        
        Returns:
            True if cache is valid, False if expired
        """
        if cache_key not in self.cache_timestamps:
            return False
        
        elapsed = time.time() - self.cache_timestamps[cache_key]
        return elapsed < self.cache_ttl

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a single asset
        
        Args:
            ticker: Asset ticker (e.g., 'AAPL', 'BTC-USD')
            start_date: Start date (YYYY-MM-DD), default: 1 year ago
            end_date: End date (YYYY-MM-DD), default: today
            interval: '1d', '1wk', '1mo', '1h', '5m', etc.
        
        Returns:
            DataFrame with OHLCV data
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"{ticker}_{start_date}_{end_date}_{interval}"

        # Check cache with TTL validation
        if cache_key in self.data_cache and self._is_cache_valid(cache_key):
            logger.info(f"Loading {ticker} from cache (valid)")
            return self.data_cache[cache_key]

        try:
            logger.info(f"Fetching {ticker} from {start_date} to {end_date}")
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )

            # Ensure proper column names
            data.columns = [col.lower() for col in data.columns]

            # Cache the data with timestamp
            self.data_cache[cache_key] = data
            self.cache_timestamps[cache_key] = time.time()

            logger.info(f"✓ Successfully fetched {len(data)} records for {ticker}")
            
            # Rate limiting - prevent API throttling
            time.sleep(self.rate_limit_delay)
            
            return data

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers with rate limiting
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Time interval
        
        Returns:
            Dictionary with ticker as key, DataFrame as value
        """
        results = {}
        for i, ticker in enumerate(tickers):
            results[ticker] = self.fetch_historical_data(
                ticker, start_date, end_date, interval
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
            Dictionary with company info
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            return {
                "ticker": ticker,
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "current_price": info.get("currentPrice", "N/A"),
                "error": False
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "error": True,
                "error_message": str(e)
            }

    def calculate_returns(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate daily returns from OHLCV data
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            Series of daily returns
        """
        if "close" not in data.columns:
            logger.error("DataFrame must contain 'close' column")
            return pd.Series()

        returns = data["close"].pct_change()
        return returns

    def calculate_log_returns(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate log returns from OHLCV data
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            Series of log returns
        """
        if "close" not in data.columns:
            logger.error("DataFrame must contain 'close' column")
            return pd.Series()

        log_returns = np.log(data["close"] / data["close"].shift(1))
        return log_returns

    def get_correlation_matrix(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between multiple assets
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date
        
        Returns:
            Correlation matrix DataFrame
        """
        data_dict = self.fetch_multiple_tickers(tickers, start_date, end_date)
        
        # Extract closing prices
        closes = pd.DataFrame()
        for ticker, data in data_dict.items():
            if not data.empty:
                closes[ticker] = data["close"]

        # Calculate returns correlation - improved NaN handling
        returns = closes.pct_change().dropna(how='any')  # Remove rows with ANY NaN
        
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
            cleared = len(self.data_cache)
            self.data_cache.clear()
            self.cache_timestamps.clear()
            logger.info(f"Cleared {cleared} cache entries")
            return cleared
        
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        keys_to_remove = [
            key for key, timestamp in self.cache_timestamps.items()
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self.data_cache[key]
            del self.cache_timestamps[key]
        
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
