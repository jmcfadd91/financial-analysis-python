import pytest
import numpy as np
import pandas as pd
from src.analysis.simulation import MonteCarloSimulator


@pytest.mark.unit
class TestMonteCarloSimulatorInit:
    def test_valid_init(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe)
        assert sim is not None

    def test_missing_close_raises(self):
        df = pd.DataFrame({'open': [1, 2, 3]})
        with pytest.raises(ValueError, match="'close' column"):
            MonteCarloSimulator(df)

    def test_too_short_raises(self):
        df = pd.DataFrame({'close': [100.0]})
        with pytest.raises(ValueError, match="at least 2 rows"):
            MonteCarloSimulator(df)

    def test_defaults_stored(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe)
        assert sim.n_simulations == 1000
        assert sim.horizon_days == 252

    def test_custom_params_stored(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=500, horizon_days=60)
        assert sim.n_simulations == 500
        assert sim.horizon_days == 60

    def test_s0_is_last_close(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe)
        assert sim._s0 == float(sample_dataframe['close'].iloc[-1])

    def test_results_none_before_simulate(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe)
        assert sim.results is None


@pytest.mark.unit
class TestSimulate:
    def test_simulate_returns_array(self, simulator):
        paths = simulator.simulate(seed=42)
        assert isinstance(paths, np.ndarray)

    def test_simulate_shape(self, simulator):
        paths = simulator.simulate(seed=42)
        assert paths.shape == (simulator.n_simulations, simulator.horizon_days)

    def test_simulate_first_col_is_s0(self, simulator):
        paths = simulator.simulate(seed=42)
        assert np.allclose(paths[:, 0], simulator._s0)

    def test_simulate_stores_results(self, simulator):
        simulator.simulate(seed=42)
        assert simulator.results is not None

    def test_simulate_positive_prices(self, simulator):
        paths = simulator.simulate(seed=42)
        assert (paths > 0).all()

    def test_simulate_deterministic_with_seed(self, sample_dataframe):
        sim1 = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=20)
        sim2 = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=20)
        p1 = sim1.simulate(seed=0)
        p2 = sim2.simulate(seed=0)
        assert np.allclose(p1, p2)

    def test_simulate_different_seeds_differ(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=20)
        p1 = sim.simulate(seed=0)
        p2 = sim.simulate(seed=1)
        assert not np.allclose(p1, p2)


@pytest.mark.unit
class TestPercentilePaths:
    def test_percentile_paths_returns_dataframe(self, simulator):
        simulator.simulate(seed=42)
        pp = simulator.percentile_paths([5, 50, 95])
        assert isinstance(pp, pd.DataFrame)

    def test_percentile_paths_columns(self, simulator):
        simulator.simulate(seed=42)
        pp = simulator.percentile_paths([5, 50, 95])
        assert set(pp.columns) == {'p5', 'p50', 'p95'}

    def test_percentile_paths_length(self, simulator):
        simulator.simulate(seed=42)
        pp = simulator.percentile_paths([5, 50, 95])
        # horizon_days + 1 (including s0 at day 0)
        assert len(pp) == simulator.horizon_days + 1

    def test_percentile_paths_first_row_is_s0(self, simulator):
        simulator.simulate(seed=42)
        pp = simulator.percentile_paths([5, 50, 95])
        assert abs(pp['p50'].iloc[0] - simulator._s0) < 1e-9
        assert abs(pp['p5'].iloc[0] - simulator._s0) < 1e-9

    def test_percentile_ordering(self, simulator):
        simulator.simulate(seed=42)
        pp = simulator.percentile_paths([5, 50, 95])
        # p5 <= p50 <= p95 at all points
        assert (pp['p5'] <= pp['p50'] + 1e-9).all()
        assert (pp['p50'] <= pp['p95'] + 1e-9).all()

    def test_percentile_paths_auto_simulates(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=10)
        pp = sim.percentile_paths()
        assert pp is not None
        assert sim.results is not None


@pytest.mark.unit
class TestProbabilityAndReturn:
    def test_probability_of_loss_range(self, simulator):
        simulator.simulate(seed=42)
        p = simulator.probability_of_loss()
        assert 0.0 <= p <= 1.0

    def test_probability_of_loss_custom_threshold(self, simulator):
        simulator.simulate(seed=42)
        p = simulator.probability_of_loss(threshold=0.5)
        assert 0.0 <= p <= 1.0

    def test_probability_of_loss_high_threshold(self, simulator):
        simulator.simulate(seed=42)
        # Very high threshold => high probability of "loss" relative to it
        p_high = simulator.probability_of_loss(threshold=10.0)
        p_low = simulator.probability_of_loss(threshold=-10.0)
        assert p_high >= p_low

    def test_probability_auto_simulates(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=10)
        p = sim.probability_of_loss()
        assert sim.results is not None

    def test_expected_return_is_float(self, simulator):
        simulator.simulate(seed=42)
        er = simulator.expected_return()
        assert isinstance(er, float)

    def test_expected_return_auto_simulates(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=10)
        er = sim.expected_return()
        assert sim.results is not None


@pytest.mark.unit
class TestValueAtRisk:
    def test_var_raises_before_simulate(self, sample_dataframe):
        sim = MonteCarloSimulator(sample_dataframe, n_simulations=50, horizon_days=10)
        with pytest.raises(ValueError, match="simulate"):
            sim.value_at_risk()

    def test_var_is_float(self, simulator):
        simulator.simulate(seed=42)
        var = simulator.value_at_risk()
        assert isinstance(var, float)

    def test_var_non_negative(self, simulator):
        simulator.simulate(seed=42)
        var = simulator.value_at_risk()
        assert var >= 0.0

    def test_var_95_higher_than_99(self):
        # Use volatile data with enough simulations for reliable percentile ordering
        np.random.seed(0)
        dates = pd.date_range('2023-01-01', periods=252, freq='B')
        prices = 100 * np.cumprod(1 + np.random.randn(252) * 0.02)
        df = pd.DataFrame({'close': prices}, index=dates)
        sim = MonteCarloSimulator(df, n_simulations=5000, horizon_days=60)
        sim.simulate(seed=0)
        var_95 = sim.value_at_risk(confidence=0.95)
        var_99 = sim.value_at_risk(confidence=0.99)
        # Higher confidence => higher VaR (larger potential loss)
        assert var_99 >= var_95 - 1e-9

    def test_var_custom_confidence(self, simulator):
        simulator.simulate(seed=42)
        var = simulator.value_at_risk(confidence=0.90)
        assert isinstance(var, float)
        assert var >= 0.0
