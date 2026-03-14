import React, { useEffect, useState } from 'react';
import { useApp } from '../App';
import { apiClient, AnalyzeResponse } from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

export default function TechChart() {
  const { ticker, start, end, runSignal } = useApp();
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChart, setActiveChart] = useState<'price' | 'technical'>('technical');

  useEffect(() => {
    if (runSignal === 0) return;
    setLoading(true);
    setError(null);
    apiClient
      .analyze({ ticker, start, end })
      .then(setData)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  }, [runSignal]);

  if (loading) return <Status msg={`Fetching ${ticker}…`} />;
  if (error) return <Status msg={`Error: ${error}`} color="#ff6666" />;
  if (!data) return <Status msg="Configure options and click Run ▶" />;

  return (
    <div>
      <div style={styles.chartToggle}>
        {(['price', 'technical'] as const).map((c) => (
          <button
            key={c}
            style={{ ...styles.toggleBtn, ...(activeChart === c ? styles.toggleActive : {}) }}
            onClick={() => setActiveChart(c)}
          >
            {c === 'price' ? 'Price + Volume' : 'Price + Indicators'}
          </button>
        ))}
      </div>
      <PlotlyChart figure={data.charts[activeChart]} height={520} />
      <MetricCards metrics={data.metrics} />
    </div>
  );
}

function Status({ msg, color = '#8888aa' }: { msg: string; color?: string }) {
  return <div style={{ color, padding: 32, textAlign: 'center', fontSize: 15 }}>{msg}</div>;
}

const styles: Record<string, React.CSSProperties> = {
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
};
