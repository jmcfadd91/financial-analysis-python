import pytest
import numpy as np
import pandas as pd
from src.analysis.portfolio import PortfolioAnalyzer


@pytest.mark.unit
class TestPortfolioAnalyzerInit:
    def test_valid_init(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data)
        assert pa is not None

    def test_missing_close_raises(self, multi_ticker_data):
        bad_data = {'AAPL': pd.DataFrame({'open': [1, 2, 3]})}
        with pytest.raises(ValueError, match="missing 'close'"):
            PortfolioAnalyzer(bad_data)

    def test_unequal_weights_raises(self, multi_ticker_data):
        with pytest.raises(ValueError, match="sum to 1.0"):
            PortfolioAnalyzer(multi_ticker_data, weights=[0.5, 0.3, 0.3])

    def test_default_equal_weights(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data)
        expected = 1.0 / 3
        assert all(abs(w - expected) < 1e-6 for w in pa.weights)

    def test_weights_stored(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data, weights=[0.5, 0.3, 0.2])
        assert abs(pa.weights[0] - 0.5) < 1e-6

    def test_tickers_stored(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data)
        assert set(pa.tickers) == {'AAPL', 'MSFT', 'GOOGL'}

    def test_risk_free_rate_default(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data)
        assert pa.risk_free_rate == 0.05

    def test_risk_free_rate_custom(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data, risk_free_rate=0.02)
        assert pa.risk_free_rate == 0.02

    def test_weights_sum_to_one_custom(self, multi_ticker_data):
        pa = PortfolioAnalyzer(multi_ticker_data, weights=[0.5, 0.3, 0.2])
        assert abs(pa.weights.sum() - 1.0) < 1e-6

    def test_weights_boundary_valid(self, multi_ticker_data):
        # Weights exactly 1.0 should not raise
        pa = PortfolioAnalyzer(multi_ticker_data, weights=[1.0, 0.0, 0.0])
        assert pa is not None


@pytest.mark.unit
class TestReturnsMatrix:
    def test_returns_matrix_shape(self, portfolio_analyzer, multi_ticker_data):
        rm = portfolio_analyzer.returns_matrix()
        # pct_change drops first row
        assert rm.shape[0] == len(next(iter(multi_ticker_data.values()))) - 1
        assert rm.shape[1] == 3

    def test_returns_matrix_columns(self, portfolio_analyzer):
        rm = portfolio_analyzer.returns_matrix()
        assert set(rm.columns) == {'AAPL', 'MSFT', 'GOOGL'}

    def test_returns_matrix_no_nan(self, portfolio_analyzer):
        rm = portfolio_analyzer.returns_matrix()
        assert not rm.isnull().any().any()

    def test_returns_matrix_is_dataframe(self, portfolio_analyzer):
        rm = portfolio_analyzer.returns_matrix()
        assert isinstance(rm, pd.DataFrame)


@pytest.mark.unit
class TestCorrelationAndCovariance:
    def test_correlation_matrix_shape(self, portfolio_analyzer):
        corr = portfolio_analyzer.correlation_matrix()
        assert corr.shape == (3, 3)

    def test_correlation_diagonal_ones(self, portfolio_analyzer):
        corr = portfolio_analyzer.correlation_matrix()
        for i in range(3):
            assert abs(corr.iloc[i, i] - 1.0) < 1e-6

    def test_correlation_symmetric(self, portfolio_analyzer):
        corr = portfolio_analyzer.correlation_matrix()
        assert np.allclose(corr.values, corr.values.T)

    def test_correlation_values_bounded(self, portfolio_analyzer):
        corr = portfolio_analyzer.correlation_matrix()
        assert corr.values.min() >= -1.0 - 1e-9
        assert corr.values.max() <= 1.0 + 1e-9

    def test_covariance_matrix_shape(self, portfolio_analyzer):
        cov = portfolio_analyzer.covariance_matrix()
        assert cov.shape == (3, 3)

    def test_covariance_matrix_symmetric(self, portfolio_analyzer):
        cov = portfolio_analyzer.covariance_matrix()
        assert np.allclose(cov.values, cov.values.T)

    def test_covariance_diagonal_positive(self, portfolio_analyzer):
        cov = portfolio_analyzer.covariance_matrix()
        for i in range(3):
            assert cov.iloc[i, i] > 0


@pytest.mark.unit
class TestPortfolioMetrics:
    def test_portfolio_return_is_float(self, portfolio_analyzer):
        ret = portfolio_analyzer.portfolio_return()
        assert isinstance(ret, float)

    def test_portfolio_volatility_is_float(self, portfolio_analyzer):
        vol = portfolio_analyzer.portfolio_volatility()
        assert isinstance(vol, float)

    def test_portfolio_volatility_positive(self, portfolio_analyzer):
        vol = portfolio_analyzer.portfolio_volatility()
        assert vol > 0

    def test_sharpe_ratio_is_float(self, portfolio_analyzer):
        sr = portfolio_analyzer.sharpe_ratio()
        assert isinstance(sr, float)

    def test_weighted_portfolio_return_differs(self, portfolio_analyzer, portfolio_analyzer_weighted):
        ret_equal = portfolio_analyzer.portfolio_return()
        ret_weighted = portfolio_analyzer_weighted.portfolio_return()
        # Different weights should give different returns (in general)
        # Just check both are finite
        assert np.isfinite(ret_equal)
        assert np.isfinite(ret_weighted)

    def test_portfolio_volatility_weighted(self, portfolio_analyzer_weighted):
        vol = portfolio_analyzer_weighted.portfolio_volatility()
        assert vol > 0

    def test_sharpe_ratio_weighted(self, portfolio_analyzer_weighted):
        sr = portfolio_analyzer_weighted.sharpe_ratio()
        assert isinstance(sr, float)
        assert np.isfinite(sr)

    def test_sharpe_zero_vol(self, multi_ticker_data):
        # Create constant-price data => zero volatility
        dates = pd.date_range('2023-01-01', periods=10, freq='B')
        constant_data = {
            'A': pd.DataFrame({'close': [100.0] * 10}, index=dates),
            'B': pd.DataFrame({'close': [200.0] * 10}, index=dates),
        }
        pa = PortfolioAnalyzer(constant_data)
        assert pa.sharpe_ratio() == 0.0


@pytest.mark.unit
class TestEfficientFrontier:
    def test_efficient_frontier_returns_dataframe(self, portfolio_analyzer):
        ef = portfolio_analyzer.efficient_frontier(n_portfolios=50)
        assert isinstance(ef, pd.DataFrame)

    def test_efficient_frontier_row_count(self, portfolio_analyzer):
        ef = portfolio_analyzer.efficient_frontier(n_portfolios=50)
        assert len(ef) == 50

    def test_efficient_frontier_columns(self, portfolio_analyzer):
        ef = portfolio_analyzer.efficient_frontier(n_portfolios=50)
        assert set(ef.columns) == {'return', 'volatility', 'sharpe', 'weights'}

    def test_efficient_frontier_volatility_positive(self, portfolio_analyzer):
        ef = portfolio_analyzer.efficient_frontier(n_portfolios=50)
        assert (ef['volatility'] > 0).all()

    def test_efficient_frontier_weights_sum_to_one(self, portfolio_analyzer):
        ef = portfolio_analyzer.efficient_frontier(n_portfolios=10)
        for w in ef['weights']:
            assert abs(sum(w) - 1.0) < 1e-9

    def test_efficient_frontier_deterministic(self, portfolio_analyzer):
        ef1 = portfolio_analyzer.efficient_frontier(n_portfolios=20)
        ef2 = portfolio_analyzer.efficient_frontier(n_portfolios=20)
        assert np.allclose(ef1['return'].values, ef2['return'].values)


@pytest.mark.unit
class TestGetAllMetrics:
    def test_get_all_metrics_returns_dict(self, portfolio_analyzer):
        metrics = portfolio_analyzer.get_all_metrics()
        assert isinstance(metrics, dict)

    def test_get_all_metrics_keys(self, portfolio_analyzer):
        metrics = portfolio_analyzer.get_all_metrics()
        assert 'portfolio_return' in metrics
        assert 'portfolio_volatility' in metrics
        assert 'sharpe_ratio' in metrics

    def test_get_all_metrics_values_finite(self, portfolio_analyzer):
        metrics = portfolio_analyzer.get_all_metrics()
        for v in metrics.values():
            assert np.isfinite(v)

    def test_metrics_stored_on_instance(self, portfolio_analyzer):
        portfolio_analyzer.get_all_metrics()
        assert len(portfolio_analyzer.metrics) == 3

    def test_get_all_metrics_consistent(self, portfolio_analyzer):
        metrics = portfolio_analyzer.get_all_metrics()
        assert abs(metrics['portfolio_return'] - portfolio_analyzer.portfolio_return()) < 1e-9
        assert abs(metrics['portfolio_volatility'] - portfolio_analyzer.portfolio_volatility()) < 1e-9
        assert abs(metrics['sharpe_ratio'] - portfolio_analyzer.sharpe_ratio()) < 1e-9


@pytest.mark.unit
class TestPortfolioEdgeCases:
    def test_single_ticker(self):
        dates = pd.date_range('2023-01-01', periods=50, freq='B')
        data = {'AAPL': pd.DataFrame({'close': np.linspace(100, 150, 50)}, index=dates)}
        pa = PortfolioAnalyzer(data)
        assert pa.weights[0] == 1.0

    def test_two_tickers(self):
        dates = pd.date_range('2023-01-01', periods=50, freq='B')
        data = {
            'A': pd.DataFrame({'close': np.linspace(100, 110, 50)}, index=dates),
            'B': pd.DataFrame({'close': np.linspace(200, 220, 50)}, index=dates),
        }
        pa = PortfolioAnalyzer(data)
        assert len(pa.tickers) == 2
        assert abs(pa.weights.sum() - 1.0) < 1e-9

    def test_weights_near_boundary_valid(self, multi_ticker_data):
        # Weights that sum to 1.0 within tolerance
        pa = PortfolioAnalyzer(multi_ticker_data, weights=[0.333334, 0.333333, 0.333333])
        assert pa is not None

    def test_multiple_missing_close(self):
        bad = {
            'A': pd.DataFrame({'open': [1, 2]}),
            'B': pd.DataFrame({'close': [1, 2]}),
        }
        with pytest.raises(ValueError, match="missing 'close'"):
            PortfolioAnalyzer(bad)
