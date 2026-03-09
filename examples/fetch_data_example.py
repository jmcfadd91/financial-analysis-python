"""
Example: Using the DataFetcher Module
Demonstrates how to fetch and work with financial data
"""

import sys
sys.path.insert(0, '../src')

from data.fetcher import DataFetcher, get_stock_data, get_multiple_stocks
import pandas as pd

# Example 1: Fetch single stock with DataFetcher
print("=" * 60)
print("EXAMPLE 1: Fetch Single Stock (AAPL)")
print("=" * 60)

fetcher = DataFetcher(cache=True)
aapl_data = fetcher.fetch_price_history('AAPL', start_date='2023-01-01', end_date='2024-01-01')
print(f"\nData shape: {aapl_data.shape}")
print(f"Date range: {aapl_data.index[0]} to {aapl_data.index[-1]}")
print(f"\nFirst 5 rows:")
print(aapl_data.head())
print(f"\nLast 5 rows:")
print(aapl_data.tail())

# Example 2: Get ticker info
print("\n" + "=" * 60)
print("EXAMPLE 2: Get Ticker Information")
print("=" * 60)

info = fetcher.get_ticker_info('AAPL')
for key, value in info.items():
    print(f"{key}: {value}")

# Example 3: Calculate returns
print("\n" + "=" * 60)
print("EXAMPLE 3: Calculate Returns")
print("=" * 60)

returns = fetcher.calculate_returns(aapl_data, method='simple')
print(f"\nDaily returns (first 10):")
print(returns.head(10))
print(f"\nReturn statistics:")
print(f"Mean daily return: {returns.mean():.4f} ({returns.mean()*252*100:.2f}% annualized)")
print(f"Std deviation: {returns.std():.4f} ({returns.std()*np.sqrt(252)*100:.2f}% annualized)")
print(f"Min daily return: {returns.min():.4f}")
print(f"Max daily return: {returns.max():.4f}")

# Example 4: Fetch multiple stocks
print("\n" + "=" * 60)
print("EXAMPLE 4: Fetch Multiple Stocks")
print("=" * 60)

tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
multi_data = fetcher.fetch_multiple_tickers(tickers, start_date='2023-01-01', end_date='2024-01-01')

print(f"\nFetched data for {len(multi_data)} tickers")
for ticker, data in multi_data.items():
    print(f"{ticker}: {len(data)} records, Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")

# Example 5: Quick convenience functions
print("\n" + "=" * 60)
print("EXAMPLE 5: Quick Convenience Functions")
print("=" * 60)

# Using convenience function for single stock
quick_data = get_stock_data('NVDA', days=90)
print(f"\nNVDA (last 90 days): {len(quick_data)} records")
print(f"Current price: ${quick_data['Close'].iloc[-1]:.2f}")
print(f"90-day high: ${quick_data['Close'].max():.2f}")
print(f"90-day low: ${quick_data['Close'].min():.2f}")

# Example 6: Intraday data for technical analysis
print("\n" + "=" * 60)
print("EXAMPLE 6: Intraday Data (Hourly)")
print("=" * 60)

intraday = fetcher.fetch_intraday('AAPL', interval='1h', days=5)
print(f"\nIntraday data shape: {intraday.shape}")
if not intraday.empty:
    print(f"Date range: {intraday.index[0]} to {intraday.index[-1]}")
    print(f"\nFirst 5 records:")
    print(intraday.head())

# Example 7: Daily OHLCV for standard analysis
print("\n" + "=" * 60)
print("EXAMPLE 7: Daily OHLCV (1 Year)")
print("=" * 60)

daily_data = fetcher.get_daily_ohlcv('SPY', lookback_days=252)
print(f"\nSPY daily data: {len(daily_data)} records")
print(f"Price change: ${daily_data['Close'].iloc[0]:.2f} → ${daily_data['Close'].iloc[-1]:.2f}")
pct_change = ((daily_data['Close'].iloc[-1] / daily_data['Close'].iloc[0]) - 1) * 100
print(f"1-year return: {pct_change:.2f}%")

print("\n" + "=" * 60)
print("✅ Data Fetcher Examples Complete!")
print("=" * 60)
