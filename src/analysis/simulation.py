import logging
import numpy as np
import pandas as pd
from typing import List, Optional

logger = logging.getLogger(__name__)

class MonteCarloSimulator:
    def __init__(self, df: pd.DataFrame, n_simulations: int = 1000, horizon_days: int = 252):
        if 'close' not in df.columns:
            raise ValueError("DataFrame must have 'close' column")
        if len(df) < 2:
            raise ValueError("DataFrame must have at least 2 rows")

        self.df = df.copy()
        self.n_simulations = n_simulations
        self.horizon_days = horizon_days
        self.results = None
        self._s0 = float(df['close'].iloc[-1])

        returns = df['close'].pct_change().dropna()
        self._mu = float(returns.mean() * 252)
        self._sigma = float(returns.std() * np.sqrt(252))
        logger.info(f"MonteCarloSimulator initialized: {n_simulations} sims, {horizon_days} days")

    def simulate(self, seed=None) -> np.ndarray:
        rng = np.random.default_rng(seed)
        dt = 1.0 / 252

        paths = np.zeros((self.n_simulations, self.horizon_days))
        paths[:, 0] = self._s0

        for t in range(1, self.horizon_days):
            Z = rng.standard_normal(self.n_simulations)
            paths[:, t] = paths[:, t-1] * np.exp(
                (self._mu - 0.5 * self._sigma**2) * dt + self._sigma * np.sqrt(dt) * Z
            )

        self.results = paths
        return paths

    def percentile_paths(self, percentiles: List[int] = [5, 50, 95]) -> pd.DataFrame:
        if self.results is None:
            self.simulate()

        # Include S0 at day 0
        s0_row = np.full((1, self.n_simulations), self._s0)
        all_paths = np.concatenate([s0_row, self.results.T], axis=0)

        result = {}
        for p in percentiles:
            result[f'p{p}'] = np.percentile(all_paths, p, axis=1)

        return pd.DataFrame(result)

    def probability_of_loss(self, threshold: float = 0.0) -> float:
        if self.results is None:
            self.simulate()
        final_prices = self.results[:, -1]
        target = self._s0 * (1 + threshold)
        return float(np.mean(final_prices < target))

    def expected_return(self) -> float:
        if self.results is None:
            self.simulate()
        mean_final = float(np.mean(self.results[:, -1]))
        return float(mean_final / self._s0 - 1)

    def value_at_risk(self, confidence: float = 0.95) -> float:
        if self.results is None:
            raise ValueError("Must call simulate() before value_at_risk()")
        final_prices = self.results[:, -1]
        final_returns = final_prices / self._s0 - 1
        var = float(np.percentile(final_returns, (1 - confidence) * 100))
        return abs(var)
