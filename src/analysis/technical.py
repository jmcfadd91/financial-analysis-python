"""Technical Analysis module for computing financial indicators."""

import logging
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TechnicalAnalysis:
    """
    Compute technical indicators for financial analysis.

    Provides methods for calculating momentum, trend, volatility, and volume indicators.
    """

    def __init__(self):
        """Initialize TechnicalAnalysis instance."""
        self.logger = setup_logger(__name__)

    def sma(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = 'Close'
    ) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            data: DataFrame with OHLCV data
            period: Number of periods for average (default: 20)
            column: Column to calculate SMA on (default: 'Close')

        Returns:
            Series with SMA values

        Raises:
            ValueError: If period > len(data) or column not in data
        """
        if len(data) < period:
            raise ValueError(f"Data length {len(data)} < period {period}")
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")

        return data[column].rolling(window=period).mean()

    def ema(
        self,
        data: pd.DataFrame,
        period: int = 12,
        column: str = 'Close'
    ) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            data: DataFrame with OHLCV data
            period: Number of periods for average (default: 12)
            column: Column to calculate EMA on (default: 'Close')

        Returns:
            Series with EMA values

        Raises:
            ValueError: If period > len(data) or column not in data
        """
        if len(data) < period:
            raise ValueError(f"Data length {len(data)} < period {period}")
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")

        return data[column].ewm(span=period, adjust=False).mean()

    def rsi(
        self,
        data: pd.DataFrame,
        period: int = 14,
        column: str = 'Close'
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        Range: 0-100. Overbought > 70, Oversold < 30.

        Args:
            data: DataFrame with OHLCV data
            period: Number of periods for RSI (default: 14)
            column: Column to calculate RSI on (default: 'Close')

        Returns:
            Series with RSI values (0-100)

        Raises:
            ValueError: If period > len(data) or column not in data
        """
        if len(data) < period + 1:
            raise ValueError(f"Data length {len(data)} < period {period} + 1")
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")

        delta = data[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def macd(
        self,
        data: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = 'Close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: DataFrame with OHLCV data
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
            column: Column to calculate MACD on (default: 'Close')

        Returns:
            Tuple of (macd_line, signal_line, histogram)

        Raises:
            ValueError: If column not in data or insufficient data
        """
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")
        if len(data) < slow + signal:
            raise ValueError(f"Data length {len(data)} < slow {slow} + signal {signal}")

        ema_fast = self.ema(data, period=fast, column=column)
        ema_slow = self.ema(data, period=slow, column=column)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        num_std: float = 2.0,
        column: str = 'Close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands (upper, middle, lower).

        Args:
            data: DataFrame with OHLCV data
            period: Period for SMA/std (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            column: Column to calculate on (default: 'Close')

        Returns:
            Tuple of (upper_band, middle_band, lower_band)

        Raises:
            ValueError: If period > len(data) or column not in data
        """
        if len(data) < period:
            raise ValueError(f"Data length {len(data)} < period {period}")
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in data")

        middle_band = self.sma(data, period=period, column=column)
        std_dev = data[column].rolling(window=period).std()

        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)

        return upper_band, middle_band, lower_band

    def atr(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility.

        Args:
            data: DataFrame with OHLCV data (requires High, Low, Close)
            period: Period for ATR (default: 14)

        Returns:
            Series with ATR values

        Raises:
            ValueError: If required columns missing or insufficient data
        """
        required = ['High', 'Low', 'Close']
        if not all(col in data.columns for col in required):
            raise ValueError(f"Data must contain {required}")
        if len(data) < period:
            raise ValueError(f"Data length {len(data)} < period {period}")

        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def obv(
        self,
        data: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).

        Args:
            data: DataFrame with OHLCV data (requires Close, Volume)

        Returns:
            Series with OBV values

        Raises:
            ValueError: If required columns missing
        """
        required = ['Close', 'Volume']
        if not all(col in data.columns for col in required):
            raise ValueError(f"Data must contain {required}")

        obv = np.zeros(len(data))
        obv[0] = data['Volume'].iloc[0]

        for i in range(1, len(data)):
            if data['Close'].iloc[i] > data['Close'].iloc[i - 1]:
                obv[i] = obv[i - 1] + data['Volume'].iloc[i]
            elif data['Close'].iloc[i] < data['Close'].iloc[i - 1]:
                obv[i] = obv[i - 1] - data['Volume'].iloc[i]
            else:
                obv[i] = obv[i - 1]

        return pd.Series(obv, index=data.index)

    def generate_signals(
        self,
        data: pd.DataFrame,
        rsi_period: int = 14,
        rsi_overbought: int = 70,
        rsi_oversold: int = 30,
        macd_signal_threshold: float = 0.0,
        sma_short: int = 20,
        sma_long: int = 50
    ) -> pd.DataFrame:
        """
        Generate buy/sell signals based on multiple indicators.

        Combines RSI, MACD, and SMA crossover signals.

        Args:
            data: DataFrame with OHLCV data
            rsi_period: RSI period (default: 14)
            rsi_overbought: RSI overbought threshold (default: 70)
            rsi_oversold: RSI oversold threshold (default: 30)
            macd_signal_threshold: MACD histogram threshold (default: 0.0)
            sma_short: Short SMA period (default: 20)
            sma_long: Long SMA period (default: 50)

        Returns:
            DataFrame with signals (1=buy, -1=sell, 0=neutral)

        Raises:
            ValueError: If data has insufficient rows
        """
        if len(data) < max(sma_long, rsi_period) + 1:
            raise ValueError("Insufficient data for signal generation")

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0

        try:
            # RSI signals
            rsi = self.rsi(data, period=rsi_period)
            signals.loc[rsi < rsi_oversold, 'signal'] += 1  # Buy
            signals.loc[rsi > rsi_overbought, 'signal'] -= 1  # Sell

            # MACD signals
            macd_line, signal_line, histogram = self.macd(data)
            signals.loc[histogram > macd_signal_threshold, 'signal'] += 1  # Buy
            signals.loc[histogram < -macd_signal_threshold, 'signal'] -= 1  # Sell

            # SMA crossover signals
            sma_short_vals = self.sma(data, period=sma_short)
            sma_long_vals = self.sma(data, period=sma_long)
            signals.loc[sma_short_vals > sma_long_vals, 'signal'] += 1  # Buy
            signals.loc[sma_short_vals < sma_long_vals, 'signal'] -= 1  # Sell

            # Normalize signals to -1, 0, 1
            signals['signal'] = signals['signal'].apply(
                lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
            )

            self.logger.info(f"Generated signals for {len(signals)} bars")
            return signals

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            raise

    def analyze_ticker(
        self,
        data: pd.DataFrame,
        ticker: str = "Unknown"
    ) -> Dict:
        """
        Comprehensive technical analysis for a single ticker.

        Args:
            data: DataFrame with OHLCV data
            ticker: Ticker symbol for logging (default: "Unknown")

        Returns:
            Dictionary with all indicators and signals

        Raises:
            ValueError: If data is invalid
        """
        if data.empty or len(data) < 50:
            raise ValueError(f"Insufficient data for {ticker}")

        try:
            analysis = {
                'ticker': ticker,
                'last_close': data['Close'].iloc[-1],
                'last_date': data.index[-1],
                'data_points': len(data)
            }

            # Indicators
            analysis['sma_20'] = self.sma(data, period=20).iloc[-1]
            analysis['sma_50'] = self.sma(data, period=50).iloc[-1]
            analysis['ema_12'] = self.ema(data, period=12).iloc[-1]
            analysis['rsi_14'] = self.rsi(data, period=14).iloc[-1]

            macd_line, signal_line, histogram = self.macd(data)
            analysis['macd'] = macd_line.iloc[-1]
            analysis['macd_signal'] = signal_line.iloc[-1]
            analysis['macd_histogram'] = histogram.iloc[-1]

            upper, middle, lower = self.bollinger_bands(data)
            analysis['bb_upper'] = upper.iloc[-1]
            analysis['bb_middle'] = middle.iloc[-1]
            analysis['bb_lower'] = lower.iloc[-1]

            analysis['atr_14'] = self.atr(data, period=14).iloc[-1]
            analysis['obv'] = self.obv(data).iloc[-1]

            # Signals
            signals = self.generate_signals(data)
            analysis['current_signal'] = signals['signal'].iloc[-1]

            self.logger.info(f"Completed analysis for {ticker}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing {ticker}: {e}")
            raise
