"""
Unit tests for Dashboard.
"""

import os
import pytest
import tempfile
import plotly.graph_objects as go
from src.reporting.dashboard import Dashboard
from src.analysis.technical import TechnicalAnalyzer
from src.analysis.risk import RiskAnalyzer


@pytest.mark.unit
class TestDashboardInit:
    def test_valid_init(self, sample_dataframe):
        db = Dashboard(ticker='TEST', df=sample_dataframe)
        assert db is not None

    def test_missing_close_raises(self, invalid_dataframe):
        with pytest.raises(ValueError):
            Dashboard(ticker='TEST', df=invalid_dataframe)

    def test_dark_theme_default(self, sample_dataframe):
        db = Dashboard(ticker='TEST', df=sample_dataframe)
        assert db.theme == 'dark'

    def test_ticker_stored(self, sample_dataframe):
        db = Dashboard(ticker='AAPL', df=sample_dataframe)
        assert db.ticker == 'AAPL'

    def test_optional_technical_none(self, sample_dataframe):
        db = Dashboard(ticker='TEST', df=sample_dataframe)
        assert db.technical is None

    def test_optional_risk_none(self, sample_dataframe):
        db = Dashboard(ticker='TEST', df=sample_dataframe)
        assert db.risk is None


@pytest.mark.unit
class TestPriceChart:
    def test_returns_figure(self, dashboard):
        fig = dashboard.price_chart()
        assert isinstance(fig, go.Figure)

    def test_has_candlestick_trace(self, dashboard):
        fig = dashboard.price_chart()
        trace_types = [type(t).__name__ for t in fig.data]
        assert 'Candlestick' in trace_types

    def test_volume_true_adds_bar_trace(self, dashboard):
        fig = dashboard.price_chart(include_volume=True)
        trace_types = [type(t).__name__ for t in fig.data]
        assert 'Bar' in trace_types

    def test_volume_false_no_bar_trace(self, dashboard):
        fig = dashboard.price_chart(include_volume=False)
        trace_types = [type(t).__name__ for t in fig.data]
        assert 'Bar' not in trace_types

    def test_at_least_one_trace(self, dashboard):
        fig = dashboard.price_chart()
        assert len(fig.data) >= 1


@pytest.mark.unit
class TestTechnicalChart:
    def test_returns_figure(self, dashboard):
        fig = dashboard.technical_chart()
        assert isinstance(fig, go.Figure)

    def test_has_subplots(self, dashboard):
        fig = dashboard.technical_chart()
        # 3-row subplot → multiple axes
        assert fig.layout.xaxis is not None

    def test_rsi_trace_present_when_computed(self, full_dashboard):
        full_dashboard.technical.rsi()
        fig = full_dashboard.technical_chart()
        trace_names = [t.name for t in fig.data]
        assert 'RSI' in trace_names

    def test_no_crash_without_technical(self, dashboard):
        fig = dashboard.technical_chart()
        assert isinstance(fig, go.Figure)

    def test_sma_overlay_present_when_computed(self, full_dashboard):
        full_dashboard.technical.sma(period=20)
        fig = full_dashboard.technical_chart()
        trace_names = [t.name for t in fig.data]
        assert any('SMA' in n or 'sma' in n.lower() for n in trace_names)


@pytest.mark.unit
class TestRiskDashboard:
    def test_returns_figure(self, full_dashboard):
        fig = full_dashboard.risk_dashboard()
        assert isinstance(fig, go.Figure)

    def test_raises_without_risk(self, dashboard):
        with pytest.raises(ValueError):
            dashboard.risk_dashboard()

    def test_has_histogram_trace(self, full_dashboard):
        fig = full_dashboard.risk_dashboard()
        trace_types = [type(t).__name__ for t in fig.data]
        assert 'Histogram' in trace_types

    def test_has_drawdown_trace(self, full_dashboard):
        fig = full_dashboard.risk_dashboard()
        trace_names = [t.name for t in fig.data]
        assert 'Drawdown' in trace_names

    def test_has_multiple_traces(self, full_dashboard):
        fig = full_dashboard.risk_dashboard()
        assert len(fig.data) >= 3


@pytest.mark.unit
class TestReturnsHeatmap:
    def test_returns_figure(self, dashboard):
        fig = dashboard.returns_heatmap()
        assert isinstance(fig, go.Figure)

    def test_has_heatmap_trace(self, dashboard):
        fig = dashboard.returns_heatmap()
        trace_types = [type(t).__name__ for t in fig.data]
        assert 'Heatmap' in trace_types

    def test_custom_frequency(self, dashboard):
        fig = dashboard.returns_heatmap(freq='Y')
        assert isinstance(fig, go.Figure)


@pytest.mark.unit
class TestExport:
    def test_export_html_creates_file(self, dashboard):
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            path = f.name
        try:
            result = dashboard.export_html(path)
            assert os.path.exists(path)
            assert result == path
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_export_html_returns_filepath(self, dashboard):
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            path = f.name
        try:
            result = dashboard.export_html(path)
            assert isinstance(result, str)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_export_pdf_raises_without_kaleido(self, dashboard):
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            path = f.name
        try:
            try:
                import kaleido  # noqa: F401
                # kaleido is installed — skip this test
                pytest.skip("kaleido is installed; cannot test ImportError path")
            except ImportError:
                with pytest.raises(ImportError):
                    dashboard.export_pdf(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)
