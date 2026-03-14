"""
Dashboard module — Plotly-based financial charts and reporting.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Dark theme colour palette
THEME = {
    'bg': '#1a1a2e',
    'grid': '#2d2d44',
    'up': '#00ff88',
    'down': '#ff4444',
    'sma': '#ffaa00',
    'ema': '#00aaff',
    'text': '#ffffff',
    'accent': '#8888ff',
}


def _apply_dark_theme(fig: go.Figure) -> go.Figure:
    """Apply dark theme layout to a figure."""
    fig.update_layout(
        paper_bgcolor=THEME['bg'],
        plot_bgcolor=THEME['bg'],
        font=dict(color=THEME['text']),
        xaxis=dict(gridcolor=THEME['grid']),
        yaxis=dict(gridcolor=THEME['grid']),
    )
    return fig


class Dashboard:
    """
    Financial data dashboard built on Plotly.

    Generates interactive charts for price, technical indicators,
    risk metrics, and returns heatmaps.

    Example:
        >>> db = Dashboard(ticker='AAPL', df=ohlcv_df, technical=ta, risk=ra)
        >>> fig = db.price_chart()
        >>> fig.show()
    """

    def __init__(
        self,
        ticker: str,
        df: pd.DataFrame,
        technical=None,
        risk=None,
        theme: str = 'dark'
    ):
        """
        Initialise Dashboard.

        Args:
            ticker: Ticker symbol label
            df: OHLCV DataFrame with lowercase columns
            technical: Optional TechnicalAnalyzer instance
            risk: Optional RiskAnalyzer instance
            theme: Colour theme (default: 'dark')

        Raises:
            ValueError: If 'close' column is missing
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        self.ticker = ticker
        self.df = df.copy()
        self.technical = technical
        self.risk = risk
        self.theme = theme
        logger.info(f"Dashboard initialised for {ticker}")

    def price_chart(self, include_volume: bool = True) -> go.Figure:
        """
        Candlestick price chart with optional volume bars.

        Args:
            include_volume: Show volume subplot (default: True)

        Returns:
            go.Figure
        """
        rows = 2 if include_volume else 1
        row_heights = [0.7, 0.3] if include_volume else [1.0]

        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights
        )

        has_ohlc = all(c in self.df.columns for c in ['open', 'high', 'low', 'close'])

        if has_ohlc:
            fig.add_trace(go.Candlestick(
                x=self.df.index,
                open=self.df['open'],
                high=self.df['high'],
                low=self.df['low'],
                close=self.df['close'],
                name=self.ticker,
                increasing_line_color=THEME['up'],
                decreasing_line_color=THEME['down'],
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df['close'],
                name=self.ticker, line=dict(color=THEME['up'])
            ), row=1, col=1)

        if include_volume and 'volume' in self.df.columns:
            fig.add_trace(go.Bar(
                x=self.df.index,
                y=self.df['volume'],
                name='Volume',
                marker_color=THEME['accent'],
                opacity=0.5,
            ), row=2, col=1)

        fig.update_layout(
            title=f'{self.ticker} Price Chart',
            xaxis_rangeslider_visible=False,
        )
        _apply_dark_theme(fig)
        return fig

    def technical_chart(self, indicators: Optional[List[str]] = None) -> go.Figure:
        """
        3-row subplot: price with overlays / RSI / MACD.

        Args:
            indicators: List of indicator names to overlay on price row.
                        Defaults to all SMA/EMA in technical.indicators.

        Returns:
            go.Figure
        """
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=[f'{self.ticker} Price', 'RSI', 'MACD']
        )

        # Row 1: price
        fig.add_trace(go.Scatter(
            x=self.df.index, y=self.df['close'],
            name='Close', line=dict(color=THEME['up'])
        ), row=1, col=1)

        if self.technical is not None:
            cached = self.technical.indicators
            overlay_keys = indicators or [k for k in cached if k.startswith(('sma_', 'ema_'))]
            for key in overlay_keys:
                series = cached.get(key)
                if series is not None and isinstance(series, pd.Series):
                    color = THEME['sma'] if key.startswith('sma') else THEME['ema']
                    fig.add_trace(go.Scatter(
                        x=series.index, y=series,
                        name=key.upper(), line=dict(color=color)
                    ), row=1, col=1)

            # Row 2: RSI
            if 'rsi' in cached:
                rsi = cached['rsi']
                fig.add_trace(go.Scatter(
                    x=rsi.index, y=rsi, name='RSI',
                    line=dict(color=THEME['accent'])
                ), row=2, col=1)
                fig.add_hline(y=70, line_dash='dash', line_color=THEME['down'], row=2, col=1)
                fig.add_hline(y=30, line_dash='dash', line_color=THEME['up'], row=2, col=1)

            # Row 3: MACD
            if 'macd' in cached:
                macd_df = cached['macd']
                if isinstance(macd_df, pd.DataFrame) and 'macd' in macd_df.columns:
                    fig.add_trace(go.Scatter(
                        x=macd_df.index, y=macd_df['macd'],
                        name='MACD', line=dict(color=THEME['ema'])
                    ), row=3, col=1)
                    fig.add_trace(go.Scatter(
                        x=macd_df.index, y=macd_df['signal'],
                        name='Signal', line=dict(color=THEME['sma'])
                    ), row=3, col=1)
                    fig.add_trace(go.Bar(
                        x=macd_df.index, y=macd_df['histogram'],
                        name='Histogram', marker_color=THEME['accent']
                    ), row=3, col=1)

        _apply_dark_theme(fig)
        return fig

    def risk_dashboard(self) -> go.Figure:
        """
        4-panel risk overview: returns histogram, drawdown, rolling Sharpe, metrics table.

        Returns:
            go.Figure

        Raises:
            ValueError: If no RiskAnalyzer was provided
        """
        if self.risk is None:
            raise ValueError("No RiskAnalyzer provided. Pass risk= to Dashboard.")

        returns = self.risk._returns
        close = self.df['close']

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Returns Distribution', 'Drawdown', 'Rolling Sharpe (30d)', 'Risk Metrics'],
            specs=[
                [{'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'table'}],
            ]
        )

        # Panel 1: returns histogram
        fig.add_trace(go.Histogram(
            x=returns, name='Returns',
            marker_color=THEME['accent'], opacity=0.7
        ), row=1, col=1)

        # Panel 2: drawdown area
        rolling_max = close.cummax()
        drawdown = (close - rolling_max) / rolling_max
        fig.add_trace(go.Scatter(
            x=drawdown.index, y=drawdown,
            name='Drawdown', fill='tozeroy',
            line=dict(color=THEME['down'])
        ), row=1, col=2)

        # Panel 3: rolling Sharpe
        window = min(30, len(returns) // 2)
        if window >= 2:
            rolling_mean = returns.rolling(window).mean()
            rolling_std = returns.rolling(window).std()
            rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
            fig.add_trace(go.Scatter(
                x=rolling_sharpe.index, y=rolling_sharpe,
                name='Rolling Sharpe', line=dict(color=THEME['sma'])
            ), row=2, col=1)

        # Panel 4: metrics table
        metrics = self.risk.get_all_metrics()
        table_keys = ['sharpe_ratio', 'sortino_ratio', 'var_historical', 'cvar']
        table_vals = []
        for k in table_keys:
            v = metrics.get(k, np.nan)
            table_vals.append(f'{v:.4f}' if isinstance(v, float) and not np.isnan(v) else str(v))

        fig.add_trace(go.Table(
            header=dict(values=['Metric', 'Value'], fill_color=THEME['grid']),
            cells=dict(
                values=[table_keys, table_vals],
                fill_color=THEME['bg'],
                font=dict(color=THEME['text'])
            )
        ), row=2, col=2)

        fig.update_layout(title=f'{self.ticker} Risk Dashboard')
        _apply_dark_theme(fig)
        return fig

    def returns_heatmap(self, freq: str = 'M') -> go.Figure:
        """
        Calendar-grid heatmap of returns by period.

        Args:
            freq: Resample frequency ('M' for monthly, 'Y' for yearly, etc.)

        Returns:
            go.Figure
        """
        returns = self.df['close'].pct_change().dropna()
        resampled = returns.resample(freq).sum()

        # Build a simple matrix: one row, all periods as columns
        values = resampled.values.reshape(1, -1)
        labels = [str(d.date()) for d in resampled.index]

        fig = go.Figure(go.Heatmap(
            z=values,
            x=labels,
            y=[self.ticker],
            colorscale='RdYlGn',
            zmid=0,
            name='Returns'
        ))

        fig.update_layout(title=f'{self.ticker} Returns Heatmap ({freq})')
        _apply_dark_theme(fig)
        return fig

    def simulation_chart(self, simulator) -> go.Figure:
        """Fan chart of Monte Carlo simulation percentile paths."""
        paths = simulator.percentile_paths([5, 50, 95])
        days = list(range(len(paths)))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=paths['p5'], name='5th Percentile',
                                 line=dict(color='red', dash='dash'), opacity=0.7))
        fig.add_trace(go.Scatter(x=days, y=paths['p95'], name='95th Percentile',
                                 line=dict(color='green', dash='dash'), opacity=0.7,
                                 fill='tonexty', fillcolor='rgba(0,255,0,0.1)'))
        fig.add_trace(go.Scatter(x=days, y=paths['p50'], name='Median',
                                 line=dict(color='blue', width=2)))

        fig.update_layout(title=f'{self.ticker} Monte Carlo Simulation',
                          xaxis_title='Days', yaxis_title='Price')
        return fig

    def equity_chart(self, backtester) -> go.Figure:
        """2-row subplot: equity curve + price with buy/sell markers."""
        eq = backtester.equity_curve
        price = self.df['close']
        trades = backtester.trades

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=['Equity Curve', 'Price'])

        fig.add_trace(go.Scatter(x=eq.index, y=eq.values, name='Equity',
                                 line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=price.index, y=price.values, name='Price',
                                 line=dict(color='gray')), row=2, col=1)

        if not trades.empty:
            fig.add_trace(go.Scatter(x=trades['entry_date'], y=trades['entry_price'],
                                     mode='markers', name='Buy',
                                     marker=dict(color='green', symbol='triangle-up', size=10)),
                          row=2, col=1)
            fig.add_trace(go.Scatter(x=trades['exit_date'], y=trades['exit_price'],
                                     mode='markers', name='Sell',
                                     marker=dict(color='red', symbol='triangle-down', size=10)),
                          row=2, col=1)

        fig.update_layout(title=f'{self.ticker} Backtest Results')
        return fig

    def export_html(self, filepath: str, include_all: bool = True) -> str:
        """
        Export dashboard as a self-contained HTML file.

        Args:
            filepath: Output file path
            include_all: Include all charts (default: True)

        Returns:
            str: filepath
        """
        if include_all:
            fig = self.price_chart()
        else:
            fig = self.price_chart(include_volume=False)

        pio.write_html(fig, file=filepath, full_html=True, include_plotlyjs=True)
        logger.info(f"Exported HTML to {filepath}")
        return filepath

    def export_pdf(self, filepath: str) -> str:
        """
        Export dashboard as PDF via kaleido.

        Args:
            filepath: Output file path

        Returns:
            str: filepath

        Raises:
            ImportError: If kaleido is not installed
        """
        try:
            import kaleido  # noqa: F401
        except ImportError:
            raise ImportError(
                "kaleido is required for PDF export. Install with: pip install kaleido"
            )

        fig = self.price_chart()
        pio.write_image(fig, file=filepath, format='pdf')
        logger.info(f"Exported PDF to {filepath}")
        return filepath
