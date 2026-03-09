"""Data module for financial analysis."""

from .fetcher import DataFetcher, get_stock_data, get_multiple_stocks

__all__ = ['DataFetcher', 'get_stock_data', 'get_multiple_stocks']
