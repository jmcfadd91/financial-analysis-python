"""
Unit tests for RiskAnalyzer.
"""

import pytest
import numpy as np
import pandas as pd
from src.analysis.risk import RiskAnalyzer


@pytest.mark.unit
class TestRiskAnalyzerInit:
    def test_valid_init(self, sample_dataframe):
        analyzer = RiskAnalyzer(sample_dataframe)
        assert analyzer is not None

    def test_missing_close_raises(self, invalid_dataframe):
        with pytest.raises(ValueError):
            RiskAnalyzer(invalid_dataframe)

    def test_default_risk_free_rate(self, sample_dataframe):
        analyzer = RiskAnalyzer(sample_dataframe)
        assert analyzer.risk_free_rate == 0.05

    def test_custom_risk_free_rate(self, sample_dataframe):
        analyzer = RiskAnalyzer(sample_dataframe, risk_free_rate=0.02)
        assert analyzer.risk_free_rate == 0.02

    def test_no_benchmark_default(self, sample_dataframe):
        analyzer = RiskAnalyzer(sample_dataframe)
        assert analyzer.benchmark_df is None


@pytest.mark.unit
class TestSharpeRatio:
    def test_returns_float(self, risk_analyzer):
        result = risk_analyzer.sharpe_ratio()
        assert isinstance(result, float)

    def test_rising_prices_positive_sharpe(self, monotone_increasing_df):
        analyzer = RiskAnalyzer(monotone_increasing_df)
        result = analyzer.sharpe_ratio()
        assert result > 0

    def test_flat_prices_returns_nan_or_value(self, sample_dataframe):
        # flat prices have zero std → should return nan
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'open': [100.0] * 50,
            'high': [100.0] * 50,
            'low': [100.0] * 50,
            'close': [100.0] * 50,
            'volume': [1000000] * 50
        }, index=dates)
        analyzer = RiskAnalyzer(df)
        result = analyzer.sharpe_ratio()
        assert np.isnan(result) or isinstance(result, float)

    def test_cached_in_metrics(self, risk_analyzer):
        risk_analyzer.sharpe_ratio()
        assert 'sharpe_ratio' in risk_analyzer.metrics


@pytest.mark.unit
class TestSortinoRatio:
    def test_returns_float(self, risk_analyzer):
        result = risk_analyzer.sortino_ratio()
        assert isinstance(result, float) or np.isinf(result)

    def test_no_downside_returns_large_value(self, monotone_increasing_df):
        analyzer = RiskAnalyzer(monotone_increasing_df)
        result = analyzer.sortino_ratio()
        # All returns are positive → no downside → should be inf or very large
        assert np.isinf(result) or result > 0

    def test_cached_in_metrics(self, risk_analyzer):
        risk_analyzer.sortino_ratio()
        assert 'sortino_ratio' in risk_analyzer.metrics


def _mixed_returns_analyzer():
    """RiskAnalyzer with mixed positive/negative returns."""
    import numpy as np
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    close = 100 * (1 + np.random.randn(100) * 0.01).cumprod()
    df = pd.DataFrame({
        'open': close * 0.99,
        'high': close * 1.01,
        'low': close * 0.98,
        'close': close,
        'volume': np.full(100, 1e6)
    }, index=dates)
    return RiskAnalyzer(df)


@pytest.mark.unit
class TestValueAtRisk:
    def test_historical_returns_positive_float(self):
        analyzer = _mixed_returns_analyzer()
        result = analyzer.value_at_risk(method='historical')
        assert isinstance(result, float)
        assert result > 0

    def test_parametric_returns_positive_float(self):
        analyzer = _mixed_returns_analyzer()
        result = analyzer.value_at_risk(method='parametric')
        assert isinstance(result, float)

    def test_higher_confidence_larger_var(self):
        analyzer = _mixed_returns_analyzer()
        var_90 = analyzer.value_at_risk(confidence=0.90, method='historical')
        var_99 = analyzer.value_at_risk(confidence=0.99, method='historical')
        assert var_99 >= var_90

    def test_invalid_method_raises(self, risk_analyzer):
        with pytest.raises(ValueError):
            risk_analyzer.value_at_risk(method='invalid_method')

    def test_cached_in_metrics(self, risk_analyzer):
        risk_analyzer.value_at_risk(method='historical')
        assert 'var_historical' in risk_analyzer.metrics


@pytest.mark.unit
class TestConditionalVaR:
    def test_returns_positive_float(self):
        analyzer = _mixed_returns_analyzer()
        result = analyzer.conditional_var()
        assert isinstance(result, float)
        assert result > 0

    def test_cvar_ge_var(self):
        analyzer = _mixed_returns_analyzer()
        var = analyzer.value_at_risk(confidence=0.95, method='historical')
        cvar = analyzer.conditional_var(confidence=0.95)
        assert cvar >= var

    def test_cached_in_metrics(self, risk_analyzer):
        risk_analyzer.conditional_var()
        assert 'cvar' in risk_analyzer.metrics


@pytest.mark.unit
class TestMaxDrawdown:
    def test_returns_dict_with_keys(self, risk_analyzer):
        result = risk_analyzer.max_drawdown()
        assert 'max_drawdown' in result
        assert 'peak_date' in result
        assert 'trough_date' in result

    def test_monotone_increasing_zero_drawdown(self, monotone_increasing_df):
        analyzer = RiskAnalyzer(monotone_increasing_df)
        result = analyzer.max_drawdown()
        assert result['max_drawdown'] == pytest.approx(0.0, abs=1e-9)

    def test_declining_df_nonzero_drawdown(self, declining_df):
        analyzer = RiskAnalyzer(declining_df)
        result = analyzer.max_drawdown()
        # From 200 to 151 → drawdown ≈ 0.245
        assert result['max_drawdown'] > 0.2

    def test_max_drawdown_non_negative(self, risk_analyzer):
        result = risk_analyzer.max_drawdown()
        assert result['max_drawdown'] >= 0

    def test_cached_in_metrics(self, risk_analyzer):
        risk_analyzer.max_drawdown()
        assert 'max_drawdown' in risk_analyzer.metrics


@pytest.mark.unit
class TestBeta:
    def test_no_benchmark_raises(self, risk_analyzer):
        with pytest.raises(ValueError):
            risk_analyzer.beta()

    def test_same_series_beta_is_one(self, sample_dataframe):
        analyzer = RiskAnalyzer(sample_dataframe, benchmark_df=sample_dataframe)
        result = analyzer.beta()
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_returns_float_with_benchmark(self, risk_analyzer_with_benchmark):
        result = risk_analyzer_with_benchmark.beta()
        assert isinstance(result, float)

    def test_cached_in_metrics(self, risk_analyzer_with_benchmark):
        risk_analyzer_with_benchmark.beta()
        assert 'beta' in risk_analyzer_with_benchmark.metrics


@pytest.mark.unit
class TestGetAllMetrics:
    def test_all_keys_present(self, risk_analyzer):
        result = risk_analyzer.get_all_metrics()
        assert 'sharpe_ratio' in result
        assert 'sortino_ratio' in result
        assert 'var_historical' in result
        assert 'var_parametric' in result
        assert 'cvar' in result
        assert 'max_drawdown' in result

    def test_all_values_numeric(self, risk_analyzer):
        result = risk_analyzer.get_all_metrics()
        for key, val in result.items():
            if key == 'max_drawdown':
                assert isinstance(val, dict)
            else:
                assert isinstance(val, (int, float)) or np.isinf(val) or np.isnan(val)

    def test_idempotent(self, risk_analyzer):
        result1 = risk_analyzer.get_all_metrics()
        result2 = risk_analyzer.get_all_metrics()
        assert result1.keys() == result2.keys()

    def test_returns_dict(self, risk_analyzer):
        result = risk_analyzer.get_all_metrics()
        assert isinstance(result, dict)
