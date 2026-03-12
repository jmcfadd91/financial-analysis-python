import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PortfolioAnalyzer:
    def __init__(self,
                 data: Dict[str, pd.DataFrame],
                 weights: Optional[List[float]] = None,
                 risk_free_rate: float = 0.05):
        # Validate all DataFrames have 'close' column
        for ticker, df in data.items():
            if 'close' not in df.columns:
                raise ValueError(f"DataFrame for {ticker} missing 'close' column")

        n = len(data)
        if weights is None:
            self.weights = np.array([1.0 / n] * n)
        else:
            weights_arr = np.array(weights)
            if not np.isclose(weights_arr.sum(), 1.0, atol=1e-6):
                raise ValueError(f"Weights must sum to 1.0, got {weights_arr.sum()}")
            self.weights = weights_arr

        self.data = data
        self.risk_free_rate = risk_free_rate
        self.tickers = list(data.keys())
        self.metrics = {}
        logger.info(f"PortfolioAnalyzer initialized with {n} tickers")

    def returns_matrix(self) -> pd.DataFrame:
        closes = pd.DataFrame({t: df['close'] for t, df in self.data.items()})
        return closes.pct_change().dropna()

    def correlation_matrix(self) -> pd.DataFrame:
        return self.returns_matrix().corr()

    def covariance_matrix(self) -> pd.DataFrame:
        return self.returns_matrix().cov() * 252

    def portfolio_return(self) -> float:
        returns = self.returns_matrix()
        mean_annual = returns.mean() * 252
        return float(np.dot(self.weights, mean_annual))

    def portfolio_volatility(self) -> float:
        cov = self.covariance_matrix()
        return float(np.sqrt(self.weights @ cov.values @ self.weights))

    def sharpe_ratio(self) -> float:
        ret = self.portfolio_return()
        vol = self.portfolio_volatility()
        if vol == 0:
            return 0.0
        return float((ret - self.risk_free_rate) / vol)

    def efficient_frontier(self, n_portfolios: int = 1000) -> pd.DataFrame:
        returns = self.returns_matrix()
        mean_annual = returns.mean() * 252
        cov = self.covariance_matrix()
        n = len(self.tickers)

        results = []
        rng = np.random.default_rng(42)
        for _ in range(n_portfolios):
            w = rng.random(n)
            w /= w.sum()
            r = float(np.dot(w, mean_annual))
            v = float(np.sqrt(w @ cov.values @ w))
            s = (r - self.risk_free_rate) / v if v > 0 else 0.0
            results.append({'return': r, 'volatility': v, 'sharpe': s, 'weights': w.tolist()})

        return pd.DataFrame(results)

    def get_all_metrics(self) -> dict:
        self.metrics = {
            'portfolio_return': self.portfolio_return(),
            'portfolio_volatility': self.portfolio_volatility(),
            'sharpe_ratio': self.sharpe_ratio(),
        }
        return self.metrics
