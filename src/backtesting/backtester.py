import logging
import numpy as np
import pandas as pd
from .strategy import Strategy

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, df: pd.DataFrame, strategy: Strategy,
                 initial_capital: float = 10_000,
                 commission: float = 0.001):
        if 'close' not in df.columns:
            raise ValueError("DataFrame must have 'close' column")
        self.df = df.copy()
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self._equity_curve = None
        self._trades = None

    @property
    def equity_curve(self) -> pd.Series:
        if self._equity_curve is None:
            raise ValueError("Must call run() first")
        return self._equity_curve

    @property
    def trades(self) -> pd.DataFrame:
        if self._trades is None:
            raise ValueError("Must call run() first")
        return self._trades

    def run(self) -> 'Backtester':
        signals = self.strategy.generate_signals(self.df)
        # Forward-fill so a buy/sell signal is held until an opposing signal
        # arrives, then shift by 1 bar to avoid look-ahead bias.
        positions = signals.replace(0, np.nan).ffill().fillna(0).shift(1).fillna(0)

        close = self.df['close']
        cash = self.initial_capital
        shares = 0.0
        equity = []
        trade_list = []

        entry_date = None
        entry_price = None
        current_position = 0

        for i, (date, price) in enumerate(close.items()):
            pos = positions.iloc[i]

            # Check for position change
            if pos != current_position:
                if current_position != 0 and entry_date is not None:
                    # Close existing position
                    proceeds = shares * price * (1 - self.commission)
                    cash += proceeds
                    pnl = proceeds - (shares * entry_price * (1 + self.commission))
                    ret = pnl / (shares * entry_price * (1 + self.commission)) if entry_price > 0 else 0
                    trade_list.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': price,
                        'pnl': pnl,
                        'return': ret,
                    })
                    shares = 0.0
                    current_position = 0
                    entry_date = None
                    entry_price = None

                if pos == 1 and cash > 0:
                    # Open long position
                    cost = cash / (price * (1 + self.commission))
                    shares = cost
                    cash -= shares * price * (1 + self.commission)
                    current_position = 1
                    entry_date = date
                    entry_price = price
                elif pos == -1:
                    current_position = -1

            equity.append(cash + shares * price)

        self._equity_curve = pd.Series(equity, index=close.index)
        self._trades = pd.DataFrame(trade_list)
        if self._trades.empty:
            self._trades = pd.DataFrame(columns=['entry_date', 'exit_date', 'entry_price', 'exit_price', 'pnl', 'return'])

        logger.info(f"Backtest complete: {len(trade_list)} trades")
        return self

    def total_return(self) -> float:
        return float(self.equity_curve.iloc[-1] / self.initial_capital - 1)

    def max_drawdown(self) -> float:
        eq = self.equity_curve
        rolling_max = eq.expanding().max()
        drawdown = (eq - rolling_max) / rolling_max
        return float(drawdown.min())

    def sharpe_ratio(self) -> float:
        returns = self.equity_curve.pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))

    def summary(self) -> dict:
        t = self.trades
        n_trades = len(t)
        win_rate = float((t['pnl'] > 0).mean()) if n_trades > 0 else 0.0
        return {
            'total_return': self.total_return(),
            'max_drawdown': self.max_drawdown(),
            'sharpe': self.sharpe_ratio(),
            'n_trades': n_trades,
            'win_rate': win_rate,
        }
