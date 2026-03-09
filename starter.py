"""
Financial Analysis Starter Script
Quick start for common financial analysis tasks
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def fetch_data(symbol, days=365):
    """Fetch historical stock data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    return df

def calculate_metrics(df):
    """Calculate key financial metrics"""
    df['Daily_Return'] = df['Adj Close'].pct_change()
    
    metrics = {
        'Current_Price': df['Adj Close'].iloc[-1],
        'YTD_Return': (df['Adj Close'].iloc[-1] / df['Adj Close'].iloc[0] - 1),
        'Annualized_Return': df['Daily_Return'].mean() * 252,
        'Annualized_Volatility': df['Daily_Return'].std() * np.sqrt(252),
        'Sharpe_Ratio': (df['Daily_Return'].mean() * 252) / (df['Daily_Return'].std() * np.sqrt(252))
    }
    
    return metrics, df

def main():
    # Get data
    print("Fetching AAPL data...")
    df = fetch_data('AAPL', days=365)
    
    # Calculate metrics
    metrics, df = calculate_metrics(df)
    
    # Display results
    print("\n" + "="*50)
    print("FINANCIAL ANALYSIS REPORT - AAPL")
    print("="*50)
    print(f"Current Price: ${metrics['Current_Price']:.2f}")
    print(f"YTD Return: {metrics['YTD_Return']:.2%}")
    print(f"Annualized Return: {metrics['Annualized_Return']:.2%}")
    print(f"Annualized Volatility: {metrics['Annualized_Volatility']:.2%}")
    print(f"Sharpe Ratio: {metrics['Sharpe_Ratio']:.3f}")
    print("="*50)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['Adj Close'], linewidth=2)
    plt.title('AAPL - Last 12 Months')
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('aapl_chart.png')
    print("\nChart saved as 'aapl_chart.png'")

if __name__ == "__main__":
    main()
