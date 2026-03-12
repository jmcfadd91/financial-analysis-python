"""
Risk analysis module for financial data.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from scipy import stats
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskAnalyzer:
    """
    Risk metrics toolkit for financial data.

    Computes standard risk metrics: Sharpe, Sortino, VaR, CVaR,
    max drawdown, and beta.

    Example:
        >>> analyzer = RiskAnalyzer(df)
        >>> sharpe = analyzer.sharpe_ratio()
        >>> metrics = analyzer.get_all_metrics()
    """

    def __init__(
        self,
        df: pd.DataFrame,
        benchmark_df: Optional[pd.DataFrame] = None,
        risk_free_rate: float = 0.05
    ):
        """
        Initialize RiskAnalyzer.

        Args:
            df: DataFrame with 'close' column (OHLCV format)
            benchmark_df: Optional benchmark DataFrame with 'close' column
            risk_free_rate: Annual risk-free rate (default: 0.05)

        Raises:
            ValueError: If 'close' column is missing
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        self.df = df.copy()
        self.benchmark_df = benchmark_df.copy() if benchmark_df is not None else None
        self.risk_free_rate = risk_free_rate
        self.metrics = {}
        self._returns = self.df['close'].pct_change().dropna()
        logger.info(f"RiskAnalyzer initialized with {len(df)} bars")

    def sharpe_ratio(self, periods: int = 252) -> float:
        """
        Calculate annualised Sharpe ratio.

        Args:
            periods: Trading periods per year (default: 252)

        Returns:
            float: Sharpe ratio, or np.nan if insufficient data
        """
        if len(self._returns) < 2:
            return np.nan

        rf_daily = self.risk_free_rate / periods
        excess = self._returns - rf_daily
        std = excess.std()
        if std == 0:
            return np.nan

        sharpe = (excess.mean() / std) * np.sqrt(periods)
        self.metrics['sharpe_ratio'] = sharpe
        return sharpe

    def sortino_ratio(self, periods: int = 252) -> float:
        """
        Calculate annualised Sortino ratio (downside deviation only).

        Args:
            periods: Trading periods per year (default: 252)

        Returns:
            float: Sortino ratio
        """
        if len(self._returns) < 2:
            return np.nan

        rf_daily = self.risk_free_rate / periods
        excess = self._returns - rf_daily
        downside = excess[excess < 0]

        if len(downside) == 0:
            sortino = np.inf
        else:
            downside_std = downside.std()
            if downside_std == 0:
                sortino = np.inf
            else:
                sortino = (excess.mean() / downside_std) * np.sqrt(periods)

        self.metrics['sortino_ratio'] = sortino
        return sortino

    def value_at_risk(self, confidence: float = 0.95, method: str = 'historical') -> float:
        """
        Calculate Value at Risk.

        Args:
            confidence: Confidence level (default: 0.95)
            method: 'historical' or 'parametric'

        Returns:
            float: VaR as a positive number (loss magnitude)

        Raises:
            ValueError: If method is not 'historical' or 'parametric'
        """
        if method not in ('historical', 'parametric'):
            raise ValueError(f"Unknown VaR method: '{method}'. Use 'historical' or 'parametric'.")

        if len(self._returns) < 2:
            return np.nan

        if method == 'historical':
            var = -np.percentile(self._returns, (1 - confidence) * 100)
        else:
            mean = self._returns.mean()
            std = self._returns.std()
            var = -(mean + stats.norm.ppf(1 - confidence) * std)

        self.metrics[f'var_{method}'] = var
        return var

    def conditional_var(self, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).

        Args:
            confidence: Confidence level (default: 0.95)

        Returns:
            float: CVaR as a positive number
        """
        if len(self._returns) < 2:
            return np.nan

        threshold = np.percentile(self._returns, (1 - confidence) * 100)
        tail = self._returns[self._returns <= threshold]

        if len(tail) == 0:
            return np.nan

        cvar = -tail.mean()
        self.metrics['cvar'] = cvar
        return cvar

    def max_drawdown(self) -> Dict:
        """
        Calculate maximum drawdown.

        Returns:
            dict: {max_drawdown, peak_date, trough_date}
        """
        close = self.df['close']
        rolling_max = close.cummax()
        drawdown = (close - rolling_max) / rolling_max

        max_dd = drawdown.min()
        trough_date = drawdown.idxmin()
        peak_date = rolling_max[:trough_date].idxmax()

        result = {
            'max_drawdown': abs(max_dd),
            'peak_date': peak_date,
            'trough_date': trough_date
        }
        self.metrics['max_drawdown'] = result
        return result

    def beta(self) -> float:
        """
        Calculate beta relative to benchmark.

        Returns:
            float: Beta coefficient

        Raises:
            ValueError: If no benchmark DataFrame was provided
        """
        if self.benchmark_df is None:
            raise ValueError("No benchmark DataFrame provided. Pass benchmark_df to RiskAnalyzer.")

        if 'close' not in self.benchmark_df.columns:
            raise ValueError("benchmark_df must contain 'close' column")

        asset_returns = self._returns
        bench_returns = self.benchmark_df['close'].pct_change().dropna()

        # Align on common index
        common_idx = asset_returns.index.intersection(bench_returns.index)
        if len(common_idx) < 2:
            return np.nan

        a = asset_returns.loc[common_idx]
        b = bench_returns.loc[common_idx]

        cov_matrix = np.cov(a, b)
        bench_var = cov_matrix[1, 1]
        if bench_var == 0:
            return np.nan

        beta_val = cov_matrix[0, 1] / bench_var
        self.metrics['beta'] = beta_val
        return beta_val

    def get_all_metrics(self) -> Dict:
        """
        Compute and return all risk metrics.

        Returns:
            dict: All computed metrics
        """
        self.sharpe_ratio()
        self.sortino_ratio()
        self.value_at_risk(method='historical')
        self.value_at_risk(method='parametric')
        self.conditional_var()
        self.max_drawdown()
        if self.benchmark_df is not None:
            self.beta()

        return dict(self.metrics)
