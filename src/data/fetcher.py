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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Unified data fetcher for stocks, ETFs, and cryptocurrencies
    Supports multiple timeframes and data sources
    """

    def __init__(self, cache_dir: str = "./data/cache"):
        """
        Initialize DataFetcher
        
        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = cache_dir
        self.data_cache = {}

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

        # Check cache
        if cache_key in self.data_cache:
            logger.info(f"Loading {ticker} from cache")
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

            # Cache the data
            self.data_cache[cache_key] = data

            logger.info(f"✓ Successfully fetched {len(data)} records for {ticker}")
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
        Fetch data for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Time interval
        
        Returns:
            Dictionary with ticker as key, DataFrame as value
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_historical_data(
                ticker, start_date, end_date, interval
            )
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
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "current_price": info.get("currentPrice", "N/A"),
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {str(e)}")
            return {}

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

        # Calculate returns correlation
        returns = closes.pct_change().dropna()
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
