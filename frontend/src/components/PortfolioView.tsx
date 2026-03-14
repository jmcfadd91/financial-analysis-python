import React, { useEffect, useState } from 'react';
import { useApp } from '../App';
import { apiClient, PortfolioResponse } from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

export default function PortfolioView() {
  const { start, end, runSignal } = useApp();
  const [tickersInput, setTickersInput] = useState('AAPL,MSFT,GOOGL,AMZN');
  const [data, setData] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChart, setActiveChart] = useState<'frontier' | 'correlation'>('frontier');

  useEffect(() => {
    if (runSignal === 0) return;
    const tickers = tickersInput
      .split(',')
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);
    if (tickers.length < 2) {
      setError('Enter at least 2 comma-separated tickers.');
      return;
    }
    setLoading(true);
    setError(null);
    apiClient
      .portfolio({ tickers, start, end })
      .then(setData)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  }, [runSignal]);

  return (
    <div>
      <div style={styles.row}>
        <label style={styles.label}>Tickers (comma-separated)</label>
        <input
          style={styles.input}
          value={tickersInput}
          onChange={(e) => setTickersInput(e.target.value)}
          placeholder="AAPL,MSFT,GOOGL"
        />
      </div>

      {loading && <Status msg="Building portfolio…" />}
      {error && <Status msg={`Error: ${error}`} color="#ff6666" />}
      {data && (
        <>
          <div style={styles.chartToggle}>
            {(['frontier', 'correlation'] as const).map((c) => (
              <button
                key={c}
                style={{ ...styles.toggleBtn, ...(activeChart === c ? styles.toggleActive : {}) }}
                onClick={() => setActiveChart(c)}
              >
                {c === 'frontier' ? 'Efficient Frontier' : 'Correlation Heatmap'}
              </button>
            ))}
          </div>
          <PlotlyChart figure={data.charts[activeChart]} height={520} />
          <MetricCards metrics={data.metrics} exclude={['tickers', 'weights']} />
          <div style={styles.weights}>
            <strong>Equal weights:</strong>{' '}
            {(data.metrics.tickers as string[])?.join(', ')}
          </div>
        </>
      )}
      {!data && !loading && !error && <Status msg="Configure options and click Run ▶" />}
    </div>
  );
}

function Status({ msg, color = '#8888aa' }: { msg: string; color?: string }) {
  return <div style={{ color, padding: 32, textAlign: 'center', fontSize: 15 }}>{msg}</div>;
}

const styles: Record<string, React.CSSProperties> = {
  row: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 },
  label: { fontSize: 12, color: '#8888aa', whiteSpace: 'nowrap' },
  input: {
    flex: 1,
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#e0e0f0',
    padding: '6px 10px',
    fontSize: 13,
    outline: 'none',
  },
  chartToggle: { display: 'flex', gap: 8, marginBottom: 12 },
  toggleBtn: {
    padding: '6px 14px',
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#8888aa',
    cursor: 'pointer',
    fontSize: 12,
  },
  toggleActive: { color: '#a0a0ff', borderColor: '#a0a0ff' },
  weights: { marginTop: 12, fontSize: 12, color: '#8888aa' },
};
