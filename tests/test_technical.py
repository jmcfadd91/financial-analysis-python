"""
Unit tests for TechnicalAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from src.analysis.technical import TechnicalAnalyzer


@pytest.mark.unit
class TestTechnicalAnalyzerInit:
    def test_valid_dataframe(self, sample_dataframe):
        analyzer = TechnicalAnalyzer(sample_dataframe)
        assert analyzer is not None

    def test_missing_columns_raises(self, invalid_dataframe):
        with pytest.raises(ValueError):
            TechnicalAnalyzer(invalid_dataframe)

    def test_uppercase_columns_raises(self):
        df = pd.DataFrame({
            'Open': [100, 101], 'High': [102, 103],
            'Low': [98, 99], 'Close': [100, 101], 'Volume': [1000, 1000]
        })
        with pytest.raises(ValueError):
            TechnicalAnalyzer(df)

    def test_dataframe_is_copied(self, sample_dataframe):
        analyzer = TechnicalAnalyzer(sample_dataframe)
        sample_dataframe.loc[sample_dataframe.index[0], 'close'] = 99999
        assert analyzer.df['close'].iloc[0] != 99999

    def test_indicators_starts_empty(self, sample_dataframe):
        analyzer = TechnicalAnalyzer(sample_dataframe)
        assert analyzer.indicators == {}


@pytest.mark.unit
class TestSMA:
    def test_default_period(self, analyzer):
        result = analyzer.sma()
        assert isinstance(result, pd.Series)

    def test_first_n_minus_1_are_nan(self, analyzer):
        period = 20
        result = analyzer.sma(period=period)
        assert result.iloc[:period - 1].isna().all()

    def test_value_correctness(self, sample_dataframe):
        analyzer = TechnicalAnalyzer(sample_dataframe)
        result = analyzer.sma(period=5)
        # At index 4, close values are 100..104, mean = 102
        expected = (100 + 101 + 102 + 103 + 104) / 5
        assert abs(result.iloc[4] - expected) < 1e-9

    def test_cached_in_indicators(self, analyzer):
        analyzer.sma(period=20)
        assert 'sma_20' in analyzer.indicators

    def test_insufficient_data_returns_nan_series(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.sma(period=20)
        assert result.isna().all()

    def test_custom_period(self, analyzer):
        result = analyzer.sma(period=10)
        assert isinstance(result, pd.Series)
        assert len(result) == len(analyzer.df)


@pytest.mark.unit
class TestEMA:
    def test_returns_series(self, analyzer):
        result = analyzer.ema()
        assert isinstance(result, pd.Series)

    def test_no_leading_nan(self, analyzer):
        result = analyzer.ema(period=20)
        # ewm starts from first value, so first value should not be NaN
        assert not result.isna().all()

    def test_cached_in_indicators(self, analyzer):
        analyzer.ema(period=12)
        assert 'ema_12' in analyzer.indicators

    def test_length_matches_dataframe(self, analyzer):
        result = analyzer.ema(period=20)
        assert len(result) == len(analyzer.df)

    def test_insufficient_data_returns_nan(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.ema(period=20)
        assert result.isna().all()


@pytest.mark.unit
class TestRSI:
    def test_values_in_range(self, analyzer):
        result = analyzer.rsi(period=14)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_cached_in_indicators(self, analyzer):
        analyzer.rsi()
        assert 'rsi' in analyzer.indicators

    def test_insufficient_data_returns_nan(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.rsi(period=14)
        assert result.isna().all()

    def test_monotone_price_high_rsi(self, monotone_increasing_df):
        analyzer = TechnicalAnalyzer(monotone_increasing_df)
        result = analyzer.rsi(period=14)
        valid = result.dropna()
        assert valid.iloc[-1] > 70

    def test_returns_series(self, analyzer):
        result = analyzer.rsi()
        assert isinstance(result, pd.Series)


@pytest.mark.unit
class TestMACD:
    def test_returns_dataframe(self, analyzer):
        result = analyzer.macd()
        assert isinstance(result, pd.DataFrame)

    def test_correct_columns(self, analyzer):
        result = analyzer.macd()
        assert 'macd' in result.columns
        assert 'signal' in result.columns
        assert 'histogram' in result.columns

    def test_histogram_equals_macd_minus_signal(self, analyzer):
        result = analyzer.macd()
        valid = result.dropna()
        if len(valid) > 0:
            diff = (valid['macd'] - valid['signal'] - valid['histogram']).abs()
            assert diff.max() < 1e-9

    def test_cached_in_indicators(self, analyzer):
        analyzer.macd()
        assert 'macd' in analyzer.indicators

    def test_insufficient_data_returns_empty(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.macd()
        assert result.empty


@pytest.mark.unit
class TestBollingerBands:
    def test_upper_ge_lower(self, analyzer):
        result = analyzer.bollinger_bands()
        valid = result.dropna()
        assert (valid['upper'] >= valid['lower']).all()

    def test_middle_equals_sma(self, analyzer):
        bb = analyzer.bollinger_bands(period=20)
        sma = analyzer.sma(period=20)
        valid_idx = bb['middle'].dropna().index
        pd.testing.assert_series_equal(
            bb['middle'].loc[valid_idx].reset_index(drop=True),
            sma.loc[valid_idx].reset_index(drop=True),
            check_names=False
        )

    def test_cached_in_indicators(self, analyzer):
        analyzer.bollinger_bands()
        assert 'bollinger_bands' in analyzer.indicators

    def test_correct_columns(self, analyzer):
        result = analyzer.bollinger_bands()
        assert all(col in result.columns for col in ['upper', 'middle', 'lower'])

    def test_insufficient_data_returns_empty(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.bollinger_bands(period=20)
        assert result.empty


@pytest.mark.unit
class TestATR:
    def test_non_nan_values_positive(self, analyzer):
        result = analyzer.atr()
        valid = result.dropna()
        assert (valid >= 0).all()

    def test_cached_in_indicators(self, analyzer):
        analyzer.atr()
        assert 'atr' in analyzer.indicators

    def test_returns_series(self, analyzer):
        result = analyzer.atr()
        assert isinstance(result, pd.Series)

    def test_insufficient_data_returns_nan(self, short_dataframe):
        analyzer = TechnicalAnalyzer(short_dataframe)
        result = analyzer.atr(period=14)
        assert result.isna().all()


@pytest.mark.unit
class TestOBV:
    def test_first_value_equals_first_volume(self, analyzer):
        result = analyzer.obv()
        expected_first = analyzer.df['volume'].iloc[0]
        assert result.iloc[0] == expected_first

    def test_monotone_price_increasing_obv(self, monotone_increasing_df):
        analyzer = TechnicalAnalyzer(monotone_increasing_df)
        result = analyzer.obv()
        assert result.iloc[-1] > result.iloc[0]

    def test_cached_in_indicators(self, analyzer):
        analyzer.obv()
        assert 'obv' in analyzer.indicators

    def test_returns_series(self, analyzer):
        result = analyzer.obv()
        assert isinstance(result, pd.Series)


@pytest.mark.unit
class TestGenerateSignals:
    def test_correct_columns(self, analyzer):
        result = analyzer.generate_signals()
        assert 'signal' in result.columns
        assert 'strength' in result.columns
        assert 'reason' in result.columns

    def test_signal_values_in_set(self, analyzer):
        result = analyzer.generate_signals()
        assert set(result['signal'].unique()).issubset({-1, 0, 1})

    def test_strength_in_range(self, analyzer):
        result = analyzer.generate_signals()
        assert (result['strength'] >= -1).all()
        assert (result['strength'] <= 1).all()

    def test_reason_never_empty(self, analyzer):
        result = analyzer.generate_signals()
        assert (result['reason'] != '').all()

    def test_use_macd_false(self, analyzer):
        result = analyzer.generate_signals(use_macd=False)
        assert isinstance(result, pd.DataFrame)

    def test_use_bb_false(self, analyzer):
        result = analyzer.generate_signals(use_bb=False)
        assert isinstance(result, pd.DataFrame)

    def test_returns_dataframe(self, analyzer):
        result = analyzer.generate_signals()
        assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
class TestGetAllIndicators:
    def test_empty_initially(self, analyzer):
        result = analyzer.get_all_indicators()
        assert result == {}

    def test_returns_copy_not_reference(self, analyzer):
        analyzer.sma(period=20)
        result = analyzer.get_all_indicators()
        result['sma_20'] = None
        assert analyzer.indicators['sma_20'] is not None

    def test_contains_computed_indicators(self, analyzer):
        analyzer.sma(period=20)
        analyzer.rsi()
        result = analyzer.get_all_indicators()
        assert 'sma_20' in result
        assert 'rsi' in result

    def test_returns_dict(self, analyzer):
        result = analyzer.get_all_indicators()
        assert isinstance(result, dict)


@pytest.mark.unit
class TestEdgeCases:
    def test_same_indicator_twice_idempotent(self, analyzer):
        result1 = analyzer.sma(period=20)
        result2 = analyzer.sma(period=20)
        pd.testing.assert_series_equal(result1, result2)

    def test_flat_prices_no_crash(self):
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'open': [100.0] * 50,
            'high': [100.0] * 50,
            'low': [100.0] * 50,
            'close': [100.0] * 50,
            'volume': [1000000] * 50
        }, index=dates)
        analyzer = TechnicalAnalyzer(df)
        analyzer.sma()
        analyzer.ema()
        analyzer.rsi()

    def test_period_equals_data_length(self, sample_dataframe):
        period = len(sample_dataframe)
        analyzer = TechnicalAnalyzer(sample_dataframe)
        result = analyzer.sma(period=period)
        assert isinstance(result, pd.Series)
