import pandas as pd
import numpy as np
import talib
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def compute_rsi_ewm(close: pd.Series) -> pd.Series:
    """
    Compute RSI using Wilder's EWM smoothing (com=13 ≈ 14-period).

    This is the shared RSI implementation used across the codebase.
    Returns a Series of RSI values [0–100] aligned to close.index.
    """
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


class TechnicalAnalyzer:
    """
    Technical analysis toolkit for financial data.
    
    Implements 8+ standard technical indicators:
    - Moving Averages (SMA, EMA)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - ATR (Average True Range)
    - OBV (On-Balance Volume)
    - Signal Generation
    
    Example:
        >>> analyzer = TechnicalAnalyzer(df)
        >>> sma = analyzer.sma(period=20)
        >>> signals = analyzer.generate_signals()
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with OHLCV data.
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
        Raises:
            ValueError: If required columns missing
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        self.df = df.copy()
        self.indicators = {}
        logger.info(f"TechnicalAnalyzer initialized with {len(df)} bars")
    
    def sma(self, period: int = 20) -> pd.Series:
        """
        Simple Moving Average (SMA).
        
        Args:
            period: Window size (default: 20)
        
        Returns:
            pd.Series: SMA values aligned with original data
        
        Example:
            >>> sma20 = analyzer.sma(period=20)
        """
        if len(self.df) < period:
            logger.warning(f"Insufficient data for SMA({period}): need {period}, have {len(self.df)}")
            return pd.Series(np.nan, index=self.df.index)
        
        sma = self.df['close'].rolling(window=period).mean()
        self.indicators[f'sma_{period}'] = sma
        logger.debug(f"SMA({period}) calculated")
        return sma
    
    def ema(self, period: int = 20) -> pd.Series:
        """
        Exponential Moving Average (EMA).
        
        Args:
            period: Span size (default: 20)
        
        Returns:
            pd.Series: EMA values
        
        Example:
            >>> ema12 = analyzer.ema(period=12)
        """
        if len(self.df) < period:
            logger.warning(f"Insufficient data for EMA({period})")
            return pd.Series(np.nan, index=self.df.index)
        
        ema = self.df['close'].ewm(span=period, adjust=False).mean()
        self.indicators[f'ema_{period}'] = ema
        logger.debug(f"EMA({period}) calculated")
        return ema
    
    def rsi(self, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (RSI).
        
        Measures momentum, range [0-100].
        Overbought: >70, Oversold: <30
        
        Args:
            period: Lookback window (default: 14)
        
        Returns:
            pd.Series: RSI values [0-100]
        
        Example:
            >>> rsi = analyzer.rsi(period=14)
            >>> oversold = rsi[rsi < 30]
        """
        if len(self.df) < period + 1:
            logger.warning(f"Insufficient data for RSI({period})")
            return pd.Series(np.nan, index=self.df.index)
        
        close = self.df['close'].values
        rsi = talib.RSI(close, timeperiod=period)
        result = pd.Series(rsi, index=self.df.index)
        self.indicators['rsi'] = result
        logger.debug(f"RSI({period}) calculated")
        return result
    
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        MACD (Moving Average Convergence Divergence).
        
        Returns MACD line, signal line, and histogram.
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
        
        Returns:
            pd.DataFrame: Columns ['macd', 'signal', 'histogram']
        
        Example:
            >>> macd_df = analyzer.macd()
            >>> bullish = macd_df[macd_df['histogram'] > 0]
        """
        if len(self.df) < slow + signal:
            logger.warning(f"Insufficient data for MACD({fast},{slow},{signal})")
            return pd.DataFrame(index=self.df.index)
        
        close = self.df['close'].values
        macd_line, signal_line, histogram = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        
        result = pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=self.df.index)
        
        self.indicators['macd'] = result
        logger.debug(f"MACD({fast},{slow},{signal}) calculated")
        return result
    
    def bollinger_bands(self, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """
        Bollinger Bands (volatility indicator).
        
        Returns upper, middle (SMA), and lower bands.
        
        Args:
            period: MA period (default: 20)
            std_dev: Standard deviations (default: 2)
        
        Returns:
            pd.DataFrame: Columns ['upper', 'middle', 'lower']
        
        Example:
            >>> bb = analyzer.bollinger_bands(period=20, std_dev=2)
            >>> oversold = bb[analyzer.df['close'] < bb['lower']]
        """
        if len(self.df) < period:
            logger.warning(f"Insufficient data for Bollinger Bands({period})")
            return pd.DataFrame(index=self.df.index)
        
        close = self.df['close'].values
        upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
        
        result = pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        }, index=self.df.index)
        
        self.indicators['bollinger_bands'] = result
        logger.debug(f"Bollinger Bands({period}, {std_dev}σ) calculated")
        return result
    
    def atr(self, period: int = 14) -> pd.Series:
        """
        Average True Range (volatility indicator).
        
        Measures market volatility independent of direction.
        
        Args:
            period: Lookback window (default: 14)
        
        Returns:
            pd.Series: ATR values
        
        Example:
            >>> atr = analyzer.atr(period=14)
            >>> volatility_increase = atr.pct_change() > 0.1
        """
        if len(self.df) < period:
            logger.warning(f"Insufficient data for ATR({period})")
            return pd.Series(np.nan, index=self.df.index)
        
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        atr = talib.ATR(high, low, close, timeperiod=period)
        
        result = pd.Series(atr, index=self.df.index)
        self.indicators['atr'] = result
        logger.debug(f"ATR({period}) calculated")
        return result
    
    def obv(self) -> pd.Series:
        """
        On-Balance Volume (volume momentum indicator).
        
        Cumulative volume indicator using price direction.
        Increasing: price up, decreasing: price down
        
        Returns:
            pd.Series: OBV values
        
        Example:
            >>> obv = analyzer.obv()
            >>> volume_strength = obv.diff()
        """
        if len(self.df) < 2:
            logger.warning("Insufficient data for OBV")
            return pd.Series(np.nan, index=self.df.index)
        
        close = self.df['close'].values
        volume = self.df['volume'].values
        obv = talib.OBV(close, volume)
        
        result = pd.Series(obv, index=self.df.index)
        self.indicators['obv'] = result
        logger.debug("OBV calculated")
        return result
    
    def generate_signals(self, 
                        rsi_oversold: int = 30, 
                        rsi_overbought: int = 70,
                        use_macd: bool = True,
                        use_bb: bool = True) -> pd.DataFrame:
        """
        Generate buy/sell signals based on multiple indicators.
        
        Signal Logic:
        - BUY: RSI < oversold AND MACD positive AND price near lower BB
        - SELL: RSI > overbought AND MACD negative AND price near upper BB
        
        Args:
            rsi_oversold: RSI oversold threshold (default: 30)
            rsi_overbought: RSI overbought threshold (default: 70)
            use_macd: Include MACD in signal (default: True)
            use_bb: Include Bollinger Bands in signal (default: True)
        
        Returns:
            pd.DataFrame: Columns ['signal', 'strength', 'reason']
            signal: 1 (buy), -1 (sell), 0 (neutral)
            strength: 0-1 (confidence level)
        
        Example:
            >>> signals = analyzer.generate_signals()
            >>> buy_signals = signals[signals['signal'] == 1]
        """
        logger.info("Generating trading signals...")

        signals = pd.DataFrame(index=self.df.index)
        signals['signal'] = 0
        signals['strength'] = 0.0
        signals['reason'] = 'neutral'

        try:
            # Per-row strength: buy contributions are positive, sell are negative.
            buy_strength = pd.Series(0.0, index=self.df.index)
            sell_strength = pd.Series(0.0, index=self.df.index)

            # RSI signals (per-row)
            rsi = self.rsi(period=14)
            buy_strength[rsi < rsi_oversold] += 0.4
            sell_strength[rsi > rsi_overbought] += 0.4

            # MACD signals (per-row)
            if use_macd:
                macd_df = self.macd()
                if not macd_df.empty:
                    buy_strength[macd_df['histogram'] > 0] += 0.3
                    sell_strength[macd_df['histogram'] < 0] += 0.3

            # Bollinger Band signals (per-row: below lower band = buy, above upper = sell)
            if use_bb:
                bb = self.bollinger_bands()
                if not bb.empty:
                    buy_strength[self.df['close'] < bb['lower']] += 0.3
                    sell_strength[self.df['close'] > bb['upper']] += 0.3

            net = buy_strength - sell_strength
            signals['strength'] = np.clip(net, -1, 1)
            signals['signal'] = signals['strength'].apply(
                lambda x: 1 if x > 0.3 else (-1 if x < -0.3 else 0)
            )

            # Build a descriptive reason label for rows with a signal
            def _reason(row_strength: float) -> str:
                if row_strength > 0.3:
                    return 'buy_signal'
                if row_strength < -0.3:
                    return 'sell_signal'
                return 'neutral'

            signals['reason'] = signals['strength'].apply(_reason)

            logger.info(f"Generated {(signals['signal'] != 0).sum()} signals")
            return signals

        except Exception as e:
            logger.error(f"Error generating signals: {e}", exc_info=True)
            return signals
    
    def get_all_indicators(self) -> dict:
        """
        Get all calculated indicators at once.
        
        Returns:
            dict: All cached indicators
        
        Example:
            >>> indicators = analyzer.get_all_indicators()
        """
        return self.indicators.copy()
