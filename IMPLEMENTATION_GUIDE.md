# Financial Analysis in Python - Implementation Guide

## Overview
This guide walks you through building a financial analysis toolkit in Python, from data collection to portfolio analysis and risk modeling.

---

## Step 1: Environment Setup

### 1.1 Install Required Libraries
```bash
pip install pandas numpy matplotlib seaborn yfinance pandas-datareader scikit-learn scipy
```

**Key libraries:**
- `pandas` - Data manipulation & analysis
- `numpy` - Numerical computing
- `yfinance` - Fetch stock data from Yahoo Finance
- `matplotlib/seaborn` - Visualization
- `scikit-learn` - Machine learning for predictions
- `scipy` - Statistical analysis

### 1.2 Create Virtual Environment
```bash
python -m venv financial-env
source financial-env/bin/activate  # macOS/Linux
# or
financial-env\Scripts\activate  # Windows
```

---

## Step 2: Data Collection & Preparation

### 2.1 Fetch Historical Stock Data
```python
import yfinance as yf
import pandas as pd

# Download 5 years of AAPL data
ticker = yf.Ticker("AAPL")
df = yf.download("AAPL", start="2019-01-01", end="2024-01-01")

print(df.head())
print(df.info())
```

### 2.2 Calculate Returns
```python
# Daily returns
df['Daily_Return'] = df['Adj Close'].pct_change()

# Cumulative returns
df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1

print(df[['Adj Close', 'Daily_Return']].head(10))
```

### 2.3 Handle Missing Data
```python
# Check for NaN values
print(df.isnull().sum())

# Forward fill for small gaps
df = df.fillna(method='ffill')

# Drop remaining NaN
df = df.dropna()
```

---

## Step 3: Technical Analysis

### 3.1 Moving Averages
```python
# Simple Moving Average
df['SMA_20'] = df['Adj Close'].rolling(window=20).mean()
df['SMA_50'] = df['Adj Close'].rolling(window=50).mean()

# Exponential Moving Average
df['EMA_12'] = df['Adj Close'].ewm(span=12, adjust=False).mean()
```

### 3.2 Volatility Calculation
```python
# Standard deviation (20-day rolling)
df['Volatility'] = df['Daily_Return'].rolling(window=20).std()

# Annualized volatility
annual_volatility = df['Daily_Return'].std() * (252 ** 0.5)
print(f"Annualized Volatility: {annual_volatility:.2%}")
```

### 3.3 Relative Strength Index (RSI)
```python
def calculate_rsi(prices, period=14):
    deltas = prices.diff()
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = 100 - 100 / (1 + rs)
    
    rsis = [rsi]
    for i in range(period, len(prices)):
        delta = deltas[i]
        if delta > 0:
            up = (up * (period - 1) + delta) / period
            down = (down * (period - 1)) / period
        else:
            up = (up * (period - 1)) / period
            down = (down * (period - 1) - delta) / period
        rs = up / down
        rsi = 100 - 100 / (1 + rs)
        rsis.append(rsi)
    
    return pd.Series(rsis, index=prices.index[period:])

df['RSI'] = calculate_rsi(df['Adj Close'])
```

---

## Step 4: Portfolio Analysis

### 4.1 Multi-Stock Portfolio
```python
# Download multiple stocks
symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
portfolio_data = yf.download(symbols, start="2023-01-01")['Adj Close']

# Calculate returns
returns = portfolio_data.pct_change()

print(returns.describe())
```

### 4.2 Portfolio Statistics
```python
# Correlation matrix
correlation = returns.corr()
print(correlation)

# Mean annual returns
mean_returns = returns.mean() * 252

# Covariance matrix
cov_matrix = returns.cov() * 252

print(f"Mean Returns:\n{mean_returns}")
print(f"\nCovariance Matrix:\n{cov_matrix}")
```

### 4.3 Calculate Portfolio Metrics
```python
def portfolio_metrics(weights, mean_returns, cov_matrix):
    portfolio_return = (weights * mean_returns).sum()
    portfolio_std = (weights.T @ cov_matrix @ weights) ** 0.5
    sharpe_ratio = portfolio_return / portfolio_std
    
    return {
        'return': portfolio_return,
        'volatility': portfolio_std,
        'sharpe_ratio': sharpe_ratio
    }

weights = np.array([0.25, 0.25, 0.25, 0.25])
metrics = portfolio_metrics(weights, mean_returns, cov_matrix)
print(f"Portfolio Return: {metrics['return']:.2%}")
print(f"Portfolio Volatility: {metrics['volatility']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
```

---

## Step 5: Risk Analysis

### 5.1 Value at Risk (VaR)
```python
# Historical VaR (95% confidence)
var_95 = returns.quantile(0.05)
print(f"VaR (95%): {var_95}")

# Parametric VaR
from scipy.stats import norm
mean = returns.mean()
std = returns.std()
var_parametric = mean - norm.ppf(0.95) * std
print(f"Parametric VaR: {var_parametric}")
```

### 5.2 Conditional Value at Risk (CVaR)
```python
# Expected Shortfall - average loss beyond VaR
cvar = returns[returns <= returns.quantile(0.05)].mean()
print(f"CVaR (95%): {cvar}")
```

### 5.3 Beta Calculation
```python
# Market data (S&P 500)
market = yf.download("^GSPC", start="2023-01-01")['Adj Close'].pct_change()
stock = returns['AAPL']

# Covariance & Beta
covariance = stock.cov(market)
market_variance = market.var()
beta = covariance / market_variance

print(f"Beta: {beta:.3f}")
```

---

## Step 6: Visualization

### 6.1 Price Charts with Moving Averages
```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(df.index, df['Adj Close'], label='Close Price', linewidth=2)
ax.plot(df.index, df['SMA_20'], label='20-Day SMA', alpha=0.7)
ax.plot(df.index, df['SMA_50'], label='50-Day SMA', alpha=0.7)
ax.set_title('AAPL Stock Price with Moving Averages')
ax.set_xlabel('Date')
ax.set_ylabel('Price ($)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

### 6.2 Returns Distribution
```python
fig, ax = plt.subplots(figsize=(10, 6))
returns.hist(bins=50, ax=ax, edgecolor='black')
ax.set_title('Distribution of Daily Returns')
ax.set_xlabel('Daily Return')
ax.set_ylabel('Frequency')
plt.tight_layout()
plt.show()
```

### 6.3 Correlation Heatmap
```python
import seaborn as sns

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0, ax=ax)
ax.set_title('Asset Correlation Matrix')
plt.tight_layout()
plt.show()
```

---

## Step 7: Advanced: Monte Carlo Simulation

```python
def monte_carlo_simulation(S0, mu, sigma, T, dt, num_simulations=1000):
    """
    S0: Initial stock price
    mu: Expected return (drift)
    sigma: Volatility
    T: Time horizon (years)
    dt: Time step
    """
    N = int(T / dt)
    paths = np.zeros((num_simulations, N))
    paths[:, 0] = S0
    
    for i in range(1, N):
        Z = np.random.standard_normal(num_simulations)
        paths[:, i] = paths[:, i-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
    
    return paths

# Run simulation
S0 = df['Adj Close'].iloc[-1]
mu = df['Daily_Return'].mean() * 252
sigma = df['Daily_Return'].std() * np.sqrt(252)
paths = monte_carlo_simulation(S0, mu, sigma, T=1, dt=1/252, num_simulations=10000)

# Visualize
plt.figure(figsize=(14, 7))
for i in range(100):
    plt.plot(paths[i, :])
plt.title('Monte Carlo Simulation - 10,000 Paths')
plt.xlabel('Days')
plt.ylabel('Stock Price ($)')
plt.tight_layout()
plt.show()
```

---

## Step 8: Next Steps

1. **Backtesting Framework** - Test trading strategies on historical data
2. **Machine Learning Models** - Price prediction using LSTM/Random Forest
3. **Real-time Data** - Connect to live market feeds
4. **Database Integration** - Store analysis results
5. **Dashboard** - Build interactive visualization with Dash/Streamlit

---

## Resources

- [Pandas Documentation](https://pandas.pydata.org/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Investopedia Financial Ratios](https://www.investopedia.com/)
- [CAPM & Portfolio Theory](https://en.wikipedia.org/wiki/Capital_asset_pricing_model)

