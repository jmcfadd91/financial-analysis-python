"""
Financial Data Fetcher Module
Handles data retrieval from multiple sources (yfinance, etc.)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Union, List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Professional data fetcher for financial instruments.
    Supports stocks, ETFs, cryptocurrencies, and indices.
    """
    
    def __init__(self, cache: bool = True):
        """
        Initialize DataFetcher
        
        Args:
            cache (bool): Enable caching to reduce API calls
        """
        self.cache = cache
        self._cache = {}
    
    def fetch_price_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical price data for a single ticker.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., 'AAPL', 'BTC-USD')
            start_date (str): Start date in 'YYYY-MM-DD' format (default: 1 year ago)
            end_date (str): End date in 'YYYY-MM-DD' format (default: today)
            interval (str): Data interval ('1d', '1h', '15m', '5m', '1m')
        
        Returns:
            pd.DataFrame: OHLCV data with columns [Open, High, Low, Close, Volume]
        """
        try:
            # Set default dates
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Check cache
            cache_key = f"{ticker}_{start_date}_{end_date}_{interval}"
            if self.cache and cache_key in self._cache:
                logger.info(f"Fetching {ticker} from cache")
                return self._cache[cache_key]
            
            logger.info(f"Fetching {ticker} from {start_date} to {end_date} ({interval})")
            
            # Fetch data
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            
            if data.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()
            
            # Cache if enabled
            if self.cache:
                self._cache[cache_key] = data
            
            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers.
        
        Args:
            tickers (List[str]): List of ticker symbols
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping tickers to DataFrames
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_price_history(ticker, start_date, end_date)
        return results
    
    def fetch_intraday(
        self,
        ticker: str,
        interval: str = "1h",
        days: int = 7
    ) -> pd.DataFrame:
        """
        Fetch intraday data for technical trading analysis.
        
        Args:
            ticker (str): Ticker symbol
            interval (str): '1m', '5m', '15m', '30m', '60m', '90m', '1h'
            days (int): Number of days to fetch (limited by yfinance)
        
        Returns:
            pd.DataFrame: Intraday OHLCV data
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return self.fetch_price_history(ticker, start_date, end_date, interval)
    
    def get_ticker_info(self, ticker: str) -> Dict:
        """
        Get comprehensive ticker information (company details, ratios, etc.)
        
        Args:
            ticker (str): Ticker symbol
        
        Returns:
            Dict: Ticker information
        """
        try:
            logger.info(f"Fetching info for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Extract key metrics
            key_metrics = {
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'beta': info.get('beta', 'N/A'),
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            return key_metrics
        
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {str(e)}")
            return {}
    
    def calculate_returns(
        self,
        price_data: pd.DataFrame,
        method: str = "simple"
    ) -> pd.Series:
        """
        Calculate returns from price data.
        
        Args:
            price_data (pd.DataFrame): DataFrame with 'Close' column
            method (str): 'simple' or 'log' returns
        
        Returns:
            pd.Series: Daily returns
        """
        close_prices = price_data['Close']
        
        if method == 'simple':
            returns = close_prices.pct_change()
        elif method == 'log':
            returns = pd.Series(
                np.log(close_prices / close_prices.shift(1)),
                index=close_prices.index
            )
        else:
            raise ValueError("Method must be 'simple' or 'log'")
        
        return returns.dropna()
    
    def get_daily_ohlcv(self, ticker: str, lookback_days: int = 252) -> pd.DataFrame:
        """
        Get daily OHLCV data (1 year default = 252 trading days).
        
        Args:
            ticker (str): Ticker symbol
            lookback_days (int): Number of trading days to fetch
        
        Returns:
            pd.DataFrame: Daily OHLCV data
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=int(lookback_days * 1.5))).strftime('%Y-%m-%d')
        
        data = self.fetch_price_history(ticker, start_date, end_date, interval="1d")
        return data.tail(lookback_days) if len(data) >= lookback_days else data
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()
        logger.info("Cache cleared")


# Convenience functions for quick usage
def get_stock_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """Quick function to fetch stock data."""
    fetcher = DataFetcher()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    return fetcher.fetch_price_history(ticker, start_date, end_date)


def get_multiple_stocks(tickers: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
    """Quick function to fetch multiple stocks."""
    fetcher = DataFetcher()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    return fetcher.fetch_multiple_tickers(tickers, start_date, end_date)
