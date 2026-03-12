import logging
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return Series of {-1, 0, 1} aligned to df.index."""

class SMACrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50):
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df['close']
        fast_sma = close.rolling(self.fast).mean()
        slow_sma = close.rolling(self.slow).mean()

        signals = pd.Series(0, index=df.index, dtype=int)
        # Buy when fast crosses above slow
        cross_above = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
        # Sell when fast crosses below slow
        cross_below = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))

        signals[cross_above] = 1
        signals[cross_below] = -1
        return signals

class RSIThreshold(Strategy):
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df['close']
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(self.period).mean()
        avg_loss = loss.rolling(self.period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[rsi < self.oversold] = 1
        signals[rsi > self.overbought] = -1
        return signals
