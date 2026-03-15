import React, { useEffect, useState } from 'react';
import type { WatchlistItem } from '../api/client';
import { apiClient } from '../api/client';

function Sparkline({ prices }: { prices: number[] }) {
  if (prices.length < 2) return <span style={{ color: '#555' }}>—</span>;
  const w = 100, h = 30;
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const pts = prices
    .map((p, i) => `${(i / (prices.length - 1)) * w},${h - ((p - min) / range) * h}`)
    .join(' ');
  const color = prices[prices.length - 1] >= prices[0] ? '#00ff88' : '#ff4444';
  return (
    <svg width={w} height={h}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}

function RsiCell({ rsi }: { rsi: number | null }) {
  if (rsi === null) return <span style={{ color: '#555' }}>—</span>;
  const color = rsi < 30 ? '#00ff88' : rsi > 70 ? '#ff4444' : '#8888aa';
  return <span style={{ color }}>{rsi.toFixed(1)}</span>;
}

function ChangeCell({ pct }: { pct: number | null }) {
  if (pct === null) return <span style={{ color: '#555' }}>—</span>;
  const color = pct >= 0 ? '#00ff88' : '#ff4444';
  const sign = pct >= 0 ? '+' : '';
  return <span style={{ color }}>{sign}{pct.toFixed(2)}%</span>;
}

export default function WatchlistView() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addTicker, setAddTicker] = useState('');
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const fetchWatchlist = () => {
    setLoading(true);
    setError(null);
    apiClient
      .getWatchlist()
      .then((res) => setItems(res.items))
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchWatchlist(); }, []);

  const handleAdd = () => {
    const t = addTicker.trim().toUpperCase();
    if (!t) return;
    setAdding(true);
    setAddError(null);
    apiClient
      .addToWatchlist({ ticker: t })
      .then(() => { setAddTicker(''); fetchWatchlist(); })
      .catch((e) => setAddError(e?.response?.data?.detail ?? e.message))
      .finally(() => setAdding(false));
  };

  const handleDelete = (ticker: string) => {
    apiClient
      .removeFromWatchlist(ticker)
      .then(fetchWatchlist)
      .catch((e) => setError(e?.response?.data?.detail ?? e.message));
  };

  return (
    <div style={styles.root}>
      {loading && <div style={styles.status}>Loading watchlist…</div>}
      {error && <div style={{ ...styles.status, color: '#ff6666' }}>{error}</div>}

      {!loading && (
        <table style={styles.table}>
          <thead>
            <tr>
              {['Ticker', 'Price', 'Day Chg', 'RSI', '30d Sparkline', ''].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={6} style={{ ...styles.td, color: '#555', textAlign: 'center', padding: 24 }}>
                  No tickers in watchlist
                </td>
              </tr>
            )}
            {items.map((item, i) => (
              <tr key={item.ticker} style={i % 2 === 0 ? styles.trEven : styles.trOdd}>
                <td style={{ ...styles.td, fontWeight: 600, color: '#a0a0ff' }}>{item.ticker}</td>
                <td style={styles.td}>
                  {item.current_price !== null ? `$${item.current_price.toFixed(2)}` : '—'}
                </td>
                <td style={styles.td}><ChangeCell pct={item.day_change_pct} /></td>
                <td style={styles.td}><RsiCell rsi={item.rsi} /></td>
                <td style={styles.td}><Sparkline prices={item.prices} /></td>
                <td style={styles.td}>
                  <button style={styles.deleteBtn} onClick={() => handleDelete(item.ticker)} title="Remove">✕</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={styles.addRow}>
        <input
          style={styles.input}
          type="text"
          placeholder="Ticker (e.g. AAPL)"
          value={addTicker}
          onChange={(e) => setAddTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          disabled={adding}
        />
        <button style={styles.addBtn} onClick={handleAdd} disabled={adding || !addTicker.trim()}>
          {adding ? '…' : 'Add ▶'}
        </button>
        {addError && <span style={{ color: '#ff6666', fontSize: 12 }}>{addError}</span>}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: { maxWidth: 800 },
  status: { color: '#8888aa', padding: 24, textAlign: 'center' },
  table: { borderCollapse: 'collapse', width: '100%', marginBottom: 16 },
  th: {
    background: '#1a1a2e',
    color: '#8888aa',
    padding: '8px 12px',
    textAlign: 'left',
    borderBottom: '1px solid #2d2d44',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  td: { padding: '8px 12px', borderBottom: '1px solid #1e1e30', fontSize: 13 },
  trEven: { background: '#0d0d1a' },
  trOdd: { background: '#11112a' },
  deleteBtn: {
    background: 'none',
    border: 'none',
    color: '#555',
    cursor: 'pointer',
    fontSize: 14,
    padding: '2px 6px',
    borderRadius: 3,
  },
  addRow: { display: 'flex', gap: 8, alignItems: 'center', marginTop: 8 },
  input: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#e0e0f0',
    padding: '6px 10px',
    fontSize: 13,
    outline: 'none',
    width: 160,
  },
  addBtn: {
    background: '#2d2d44',
    border: '1px solid #3d3d55',
    borderRadius: 4,
    color: '#a0a0ff',
    padding: '6px 14px',
    fontSize: 13,
    cursor: 'pointer',
    fontWeight: 600,
  },
};
