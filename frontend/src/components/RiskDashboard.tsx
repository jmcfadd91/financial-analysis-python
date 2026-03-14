import { useEffect, useState } from 'react';
import { useApp } from '../App';
import type { AnalyzeResponse } from '../api/client';
import { apiClient } from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

export default function RiskDashboard() {
  const { ticker, start, end, runSignal } = useApp();
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) return <Status msg={`Computing risk metrics for ${ticker}…`} />;
  if (error) return <Status msg={`Error: ${error}`} color="#ff6666" />;
  if (!data) return <Status msg="Configure options and click Run ▶" />;

  return (
    <div>
      <PlotlyChart figure={data.charts.risk} height={560} />
      <MetricCards metrics={data.metrics} />
    </div>
  );
}

function Status({ msg, color = '#8888aa' }: { msg: string; color?: string }) {
  return <div style={{ color, padding: 32, textAlign: 'center', fontSize: 15 }}>{msg}</div>;
}
