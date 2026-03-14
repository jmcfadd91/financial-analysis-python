import React, { useEffect, useState } from 'react';
import { useApp } from '../App';
import { apiClient, SimulateResponse } from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

export default function SimulationChart() {
  const { ticker, start, end, runSignal } = useApp();
  const [nSims, setNSims] = useState(1000);
  const [horizon, setHorizon] = useState(252);
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (runSignal === 0) return;
    setLoading(true);
    setError(null);
    apiClient
      .simulate({ ticker, start, end, n_simulations: nSims, horizon_days: horizon })
      .then(setData)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  }, [runSignal]);

  return (
    <div>
      <div style={styles.controls}>
        <Control label="Simulations" value={nSims} onChange={setNSims} min={100} max={5000} step={100} />
        <Control label="Horizon (days)" value={horizon} onChange={setHorizon} min={30} max={756} step={30} />
      </div>

      {loading && <Status msg={`Running ${nSims} simulations for ${ticker}…`} />}
      {error && <Status msg={`Error: ${error}`} color="#ff6666" />}
      {data && (
        <>
          <PlotlyChart figure={data.chart} height={500} />
          <MetricCards metrics={data.metrics} />
        </>
      )}
      {!data && !loading && !error && <Status msg="Configure options and click Run ▶" />}
    </div>
  );
}

function Control({
  label,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
}) {
  return (
    <div style={styles.control}>
      <label style={styles.label}>
        {label}: <strong>{value}</strong>
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: 160 }}
      />
    </div>
  );
}

function Status({ msg, color = '#8888aa' }: { msg: string; color?: string }) {
  return <div style={{ color, padding: 32, textAlign: 'center', fontSize: 15 }}>{msg}</div>;
}

const styles: Record<string, React.CSSProperties> = {
  controls: { display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' },
  control: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: '#8888aa' },
};
