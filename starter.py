"""
Financial Analysis Starter Script
End-to-end demo using all src modules.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.data.fetcher import DataFetcher
from src.analysis.technical import TechnicalAnalyzer
from src.analysis.risk import RiskAnalyzer
from src.analysis.portfolio import PortfolioAnalyzer
from src.analysis.simulation import MonteCarloSimulator
from src.backtesting.strategy import SMACrossover, RSIThreshold
from src.backtesting.backtester import Backtester
from src.reporting.dashboard import Dashboard
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

TICKERS = ['AAPL', 'MSFT', 'GOOGL']
DAYS = 365


def fetch_data(tickers, days=DAYS):
    """Fetch historical OHLCV data for a list of tickers."""
    fetcher = DataFetcher()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    data = {}
    for ticker in tickers:
        logger.info(f"Fetching {ticker}...")
        try:
            df = fetcher.fetch_historical_data(
                ticker, start=str(start_date), end=str(end_date)
            )
            data[ticker] = df
            logger.info(f"  {ticker}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"  Could not fetch {ticker}: {e}")
    return data


def run_technical_analysis(ticker, df):
    """Run technical analysis and print indicator summary."""
    print(f"\n--- Technical Analysis: {ticker} ---")
    ta = TechnicalAnalyzer(df)
    ta.sma(20)
    ta.ema(20)
    ta.rsi()
    macd = ta.macd()
    print(f"  Latest Close: {df['close'].iloc[-1]:.2f}")
    print(f"  SMA(20):      {ta.indicators.get('sma_20', pd.Series([float('nan')])).iloc[-1]:.2f}")
    print(f"  RSI:          {ta.indicators.get('rsi', pd.Series([float('nan')])).iloc[-1]:.2f}")
    return ta


def run_risk_analysis(ticker, df):
    """Compute and print risk metrics."""
    print(f"\n--- Risk Analysis: {ticker} ---")
    ra = RiskAnalyzer(df)
    metrics = ra.get_all_metrics()
    print(f"  Sharpe Ratio:     {metrics.get('sharpe_ratio', float('nan')):.4f}")
    print(f"  Sortino Ratio:    {metrics.get('sortino_ratio', float('nan')):.4f}")
    print(f"  VaR (95%, hist):  {metrics.get('var_historical', float('nan')):.4f}")
    print(f"  Max Drawdown:     {metrics['max_drawdown']['max_drawdown']:.4f}")
    return ra


def run_portfolio_analysis(data):
    """Compute portfolio-level metrics."""
    print(f"\n--- Portfolio Analysis: {list(data.keys())} ---")
    pa = PortfolioAnalyzer(data)
    metrics = pa.get_all_metrics()
    print(f"  Portfolio Return:     {metrics['portfolio_return']:.4f}")
    print(f"  Portfolio Volatility: {metrics['portfolio_volatility']:.4f}")
    print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:.4f}")
    return pa


def run_simulation(ticker, df):
    """Run Monte Carlo simulation and print summary stats."""
    print(f"\n--- Monte Carlo Simulation: {ticker} ---")
    sim = MonteCarloSimulator(df, n_simulations=500, horizon_days=60)
    sim.simulate(seed=42)
    er = sim.expected_return()
    pol = sim.probability_of_loss()
    var = sim.value_at_risk(confidence=0.95)
    print(f"  Expected Return (60d): {er:.4f}")
    print(f"  Probability of Loss:   {pol:.4f}")
    print(f"  VaR (95%, Monte Carlo): {var:.4f}")
    return sim


def run_backtest(ticker, df):
    """Run SMA crossover backtest and print summary."""
    print(f"\n--- Backtest (SMA Crossover): {ticker} ---")
    strategy = SMACrossover(fast=20, slow=50)
    bt = Backtester(df, strategy, initial_capital=10_000)
    bt.run()
    s = bt.summary()
    print(f"  Total Return: {s['total_return']:.4f}")
    print(f"  Max Drawdown: {s['max_drawdown']:.4f}")
    print(f"  Sharpe Ratio: {s['sharpe']:.4f}")
    print(f"  Trades:       {s['n_trades']}")
    print(f"  Win Rate:     {s['win_rate']:.4f}")
    return bt


def main():
    print("=" * 60)
    print("FINANCIAL ANALYSIS TOOLKIT — END-TO-END DEMO")
    print("=" * 60)

    data = fetch_data(TICKERS)

    if not data:
        print("No data fetched. Exiting.")
        return

    # Use first available ticker for single-asset demos
    primary_ticker = next(iter(data))
    primary_df = data[primary_ticker]

    ta = run_technical_analysis(primary_ticker, primary_df)
    ra = run_risk_analysis(primary_ticker, primary_df)

    if len(data) >= 2:
        run_portfolio_analysis(data)
    else:
        print("\n(Portfolio analysis requires >= 2 tickers)")

    sim = run_simulation(primary_ticker, primary_df)
    bt = run_backtest(primary_ticker, primary_df)

    # Dashboard export (HTML only — kaleido not required)
    print(f"\n--- Dashboard Export: {primary_ticker} ---")
    db = Dashboard(ticker=primary_ticker, df=primary_df, technical=ta, risk=ra)
    html_path = f"{primary_ticker}_dashboard.html"
    db.export_html(html_path)
    print(f"  HTML dashboard saved to: {html_path}")

    print("\n" + "=" * 60)
    print("Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
