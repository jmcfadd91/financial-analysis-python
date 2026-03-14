import React, { useEffect, useState } from 'react';
import { useApp } from '../App';
import { apiClient, BacktestResponse } from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

type Strategy = 'sma' | 'rsi';

export default function BacktestView() {
  const { ticker, start, end, runSignal } = useApp();
  const [strategy, setStrategy] = useState<Strategy>('sma');
  const [capital, setCapital] = useState(10000);
  // SMA params
  const [smaFast, setSmaFast] = useState(20);
  const [smaSlow, setSmaSlow] = useState(50);
  // RSI params
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiOversold, setRsiOversold] = useState(30);
  const [rsiOverbought, setRsiOverbought] = useState(70);

  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (runSignal === 0) return;
    const params =
      strategy === 'sma'
        ? { fast: smaFast, slow: smaSlow }
        : { period: rsiPeriod, oversold: rsiOversold, overbought: rsiOverbought };

    setLoading(true);
    setError(null);
    apiClient
      .backtest({ ticker, start, end, strategy, params, capital })
      .then(setData)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  }, [runSignal]);

  return (
    <div>
      {/* Controls */}
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>Strategy</label>
          <select
            style={styles.select}
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as Strategy)}
          >
            <option value="sma">SMA Crossover</option>
            <option value="rsi">RSI Threshold</option>
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>Capital ($)</label>
          <input
            style={styles.numInput}
            type="number"
            value={capital}
            min={1000}
            step={1000}
            onChange={(e) => setCapital(Number(e.target.value))}
          />
        </div>

        {strategy === 'sma' && (
          <>
            <div style={styles.controlGroup}>
              <label style={styles.label}>Fast SMA</label>
              <input style={styles.numInput} type="number" value={smaFast} min={5} max={100} onChange={(e) => setSmaFast(Number(e.target.value))} />
            </div>
            <div style={styles.controlGroup}>
              <label style={styles.label}>Slow SMA</label>
              <input style={styles.numInput} type="number" value={smaSlow} min={10} max={200} onChange={(e) => setSmaSlow(Number(e.target.value))} />
            </div>
          </>
        )}

        {strategy === 'rsi' && (
          <>
            <div style={styles.controlGroup}>
              <label style={styles.label}>RSI Period</label>
              <input style={styles.numInput} type="number" value={rsiPeriod} min={5} max={50} onChange={(e) => setRsiPeriod(Number(e.target.value))} />
            </div>
            <div style={styles.controlGroup}>
              <label style={styles.label}>Oversold</label>
              <input style={styles.numInput} type="number" value={rsiOversold} min={10} max={45} onChange={(e) => setRsiOversold(Number(e.target.value))} />
            </div>
            <div style={styles.controlGroup}>
              <label style={styles.label}>Overbought</label>
              <input style={styles.numInput} type="number" value={rsiOverbought} min={55} max={90} onChange={(e) => setRsiOverbought(Number(e.target.value))} />
            </div>
          </>
        )}
      </div>

      {loading && <Status msg={`Running ${strategy.toUpperCase()} backtest for ${ticker}…`} />}
      {error && <Status msg={`Error: ${error}`} color="#ff6666" />}

      {data && (
        <>
          <PlotlyChart figure={data.chart} height={500} />
          <MetricCards metrics={data.summary} />
          {data.trades.length > 0 && <TradesTable trades={data.trades} />}
        </>
      )}
      {!data && !loading && !error && <Status msg="Configure options and click Run ▶" />}
    </div>
  );
}

function TradesTable({ trades }: { trades: Record<string, string | number | null>[] }) {
  const cols = Object.keys(trades[0]);
  return (
    <div style={styles.tableWrap}>
      <h4 style={styles.tableTitle}>Trades ({trades.length})</h4>
      <div style={{ overflowX: 'auto' }}>
        <table style={styles.table}>
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c} style={styles.th}>{c.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {trades.map((row, i) => (
              <tr key={i} style={i % 2 === 0 ? styles.trEven : styles.trOdd}>
                {cols.map((c) => (
                  <td key={c} style={styles.td}>
                    {typeof row[c] === 'number' ? (row[c] as number).toFixed(4) : String(row[c] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Status({ msg, color = '#8888aa' }: { msg: string; color?: string }) {
  return <div style={{ color, padding: 32, textAlign: 'center', fontSize: 15 }}>{msg}</div>;
}

const styles: Record<string, React.CSSProperties> = {
  controls: { display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' },
  controlGroup: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 11, color: '#8888aa', textTransform: 'uppercase', letterSpacing: 0.5 },
  select: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#e0e0f0',
    padding: '6px 8px',
    fontSize: 13,
    outline: 'none',
  },
  numInput: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#e0e0f0',
    padding: '6px 8px',
    fontSize: 13,
    outline: 'none',
    width: 80,
  },
  tableWrap: { marginTop: 20 },
  tableTitle: { color: '#a0a0ff', marginBottom: 8, fontWeight: 600 },
  table: { borderCollapse: 'collapse', width: '100%', fontSize: 12 },
  th: {
    background: '#1a1a2e',
    color: '#8888aa',
    padding: '8px 10px',
    textAlign: 'left',
    borderBottom: '1px solid #2d2d44',
    textTransform: 'capitalize',
    whiteSpace: 'nowrap',
  },
  td: { padding: '6px 10px', borderBottom: '1px solid #1e1e30', whiteSpace: 'nowrap' },
  trEven: { background: '#0d0d1a' },
  trOdd: { background: '#11112a' },
};
