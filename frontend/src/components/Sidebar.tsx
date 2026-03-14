import React from 'react';
import { useApp } from '../App';

export default function Sidebar() {
  const { ticker, setTicker, start, setStart, end, setEnd, triggerRun } = useApp();

  return (
    <aside style={styles.sidebar}>
      <div style={styles.section}>
        <label style={styles.label}>Ticker</label>
        <input style={styles.input} value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())} placeholder="e.g. AAPL" />
      </div>
      <div style={styles.section}>
        <label style={styles.label}>Start date</label>
        <input style={styles.input} type="date" value={start} onChange={(e) => setStart(e.target.value)} />
      </div>
      <div style={styles.section}>
        <label style={styles.label}>End date</label>
        <input style={styles.input} type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>
      <button style={styles.runBtn} onClick={triggerRun}>Run ▶</button>
      <p style={styles.hint}>Results update on each tab when you click Run.</p>
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 200, flexShrink: 0, background: '#1a1a2e', borderRight: '1px solid #2d2d44',
    padding: 16, display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto',
  },
  section: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 11, color: '#8888aa', textTransform: 'uppercase', letterSpacing: 0.5 },
  input: {
    background: '#0d0d1a', border: '1px solid #2d2d44', borderRadius: 4,
    color: '#e0e0f0', padding: '6px 8px', fontSize: 13, outline: 'none',
    width: '100%', boxSizing: 'border-box',
  },
  runBtn: {
    marginTop: 8, padding: '10px 0', background: '#4444cc', border: 'none',
    borderRadius: 6, color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer',
  },
  hint: { fontSize: 11, color: '#555577', marginTop: 4, lineHeight: 1.5 },
};
