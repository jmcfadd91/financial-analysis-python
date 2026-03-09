"""
Quick test of the data fetcher module
"""

import sys
sys.path.insert(0, 'src')

from data import DataFetcher

print("🚀 Testing Data Fetcher Module\n")

fetcher = DataFetcher()

# Test 1: Fetch single stock
print("=" * 60)
print("TEST 1: Fetching Apple (AAPL) - Last 3 months")
print("=" * 60)
aapl = fetcher.fetch_price_history("AAPL", "2023-10-01", "2024-01-31")
print(f"\nData shape: {aapl.shape}")
print("\nFirst 5 rows:")
print(aapl.head())
print("\nLast 5 rows:")
print(aapl.tail())

# Test 2: Company info
print("\n" + "=" * 60)
print("TEST 2: Fetching Apple Company Info")
print("=" * 60)
info = fetcher.fetch_info("AAPL")
print("\nCompany Information:")
for key, value in info.items():
    print(f"  {key:20s}: {value}")

# Test 3: Multiple tickers
print("\n" + "=" * 60)
print("TEST 3: Fetching Multiple Assets (AAPL, MSFT, GOOGL)")
print("=" * 60)
data = fetcher.fetch_multiple(["AAPL", "MSFT", "GOOGL"], "2023-10-01", "2024-01-31")
for ticker, df in data.items():
    print(f"{ticker}: {len(df)} rows, Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")

# Test 4: Dividends
print("\n" + "=" * 60)
print("TEST 4: Fetching Apple Dividends")
print("=" * 60)
divs = fetcher.fetch_dividends("AAPL", "2023-01-01")
if len(divs) > 0:
    print(f"Found {len(divs)} dividend payments:")
    print(divs)
else:
    print("No dividend data found")

# Test 5: Benchmark
print("\n" + "=" * 60)
print("TEST 5: Fetching S&P 500 Benchmark")
print("=" * 60)
sp500 = fetcher.get_benchmark_data("^GSPC", "2023-10-01", "2024-01-31")
print(f"\nS&P 500: {len(sp500)} rows")
print(f"Range: {sp500['Close'].min():.2f} - {sp500['Close'].max():.2f}")

print("\n✅ All tests completed!")
