"""
Data Fetcher Module - Bloomberg Style Financial Data Collection
Handles stock, ETF, and crypto data from multiple sources
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Union, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Professional data fetcher for financial assets.
    Supports stocks, ETFs, crypto with caching and error handling.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """Initialize fetcher with optional caching."""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def fetch_price_history(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a ticker.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL', 'BTC-USD')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD, default: today)
            interval: '1d', '1h', '5m', etc.
            
        Returns:
            DataFrame with OHLCV columns + Adj Close
        """
        try:
            logger.info(f"Fetching {ticker} from {start_date} to {end_date or 'today'}")
            
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            
            if data.empty:
                logger.error(f"No data found for {ticker}")
                return pd.DataFrame()
            
            # Ensure proper column names
            data.index.name = 'Date'
            logger.info(f"✓ Fetched {len(data)} rows for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_multiple(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers.
        
        Args:
            tickers: List of symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary {ticker: DataFrame}
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_price_history(ticker, start_date, end_date)
        return results
    
    def fetch_info(self, ticker: str) -> Dict:
        """
        Fetch company/asset information.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary with info (sector, industry, PE, etc.)
        """
        try:
            asset = yf.Ticker(ticker)
            info = asset.info
            
            # Extract key metrics
            key_info = {
                'symbol': ticker,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            logger.info(f"✓ Fetched info for {ticker}")
            return key_info
            
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {str(e)}")
            return {}
    
    def fetch_dividends(self, ticker: str, start_date: str = None) -> pd.Series:
        """
        Fetch dividend history.
        
        Args:
            ticker: Stock symbol
            start_date: Optional start date
            
        Returns:
            Series with dividend dates and amounts
        """
        try:
            asset = yf.Ticker(ticker)
            dividends = asset.dividends
            
            if start_date:
                dividends = dividends[dividends.index >= start_date]
            
            logger.info(f"✓ Fetched {len(dividends)} dividend records for {ticker}")
            return dividends
            
        except Exception as e:
            logger.error(f"Error fetching dividends for {ticker}: {str(e)}")
            return pd.Series()
    
    def fetch_splits(self, ticker: str) -> pd.Series:
        """
        Fetch stock split history.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Series with split dates and ratios
        """
        try:
            asset = yf.Ticker(ticker)
            splits = asset.splits
            logger.info(f"✓ Fetched {len(splits)} split records for {ticker}")
            return splits
            
        except Exception as e:
            logger.error(f"Error fetching splits for {ticker}: {str(e)}")
            return pd.Series()
    
    def get_benchmark_data(
        self,
        benchmark: str = "^GSPC",  # S&P 500
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Fetch benchmark index data (S&P 500, Nasdaq, etc.).
        
        Args:
            benchmark: Index symbol (^GSPC, ^IXIC, ^FTSE)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with index data
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        return self.fetch_price_history(benchmark, start_date, end_date)


# Example usage
if __name__ == "__main__":
    fetcher = DataFetcher()
    
    # Single ticker
    print("\n📊 Fetching Apple stock...")
    aapl = fetcher.fetch_price_history("AAPL", "2023-01-01", "2024-01-31")
    print(aapl.head())
    
    # Company info
    print("\n📋 Apple Info:")
    info = fetcher.fetch_info("AAPL")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Multiple tickers
    print("\n📊 Fetching multiple assets...")
    data = fetcher.fetch_multiple(["AAPL", "MSFT", "GOOGL"], "2023-01-01")
    for ticker, df in data.items():
        print(f"{ticker}: {len(df)} rows")
