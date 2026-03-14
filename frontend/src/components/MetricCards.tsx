import React from 'react';

interface Props {
  metrics: Record<string, number | string | null | unknown>;
  exclude?: string[];
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') {
    if (Math.abs(v) > 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    return v.toFixed(4);
  }
  if (typeof v === 'object') return JSON.stringify(v).slice(0, 40);
  return String(v);
}

export default function MetricCards({ metrics, exclude = [] }: Props) {
  const entries = Object.entries(metrics).filter(([k]) => !exclude.includes(k));

  return (
    <div style={styles.grid}>
      {entries.map(([key, val]) => (
        <div key={key} style={styles.card}>
          <div style={styles.cardLabel}>{key.replace(/_/g, ' ')}</div>
          <div style={styles.cardValue}>{fmt(val)}</div>
        </div>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 16,
  },
  card: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: '10px 14px',
    minWidth: 150,
  },
  cardLabel: {
    fontSize: 11,
    color: '#8888aa',
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  cardValue: { fontSize: 18, fontWeight: 700, color: '#a0a0ff' },
};
