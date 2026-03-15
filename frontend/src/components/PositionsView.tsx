import React, { useEffect, useState } from 'react';
import {
  apiClient,
  type AddPositionRequest,
  type GetPositionsResponse,
  type PositionRow,
  type SimulatePortfolioResponse,
} from '../api/client';
import PlotlyChart from './PlotlyChart';
import MetricCards from './MetricCards';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtMoney(v: number | null): string {
  if (v === null || v === undefined) return '—';
  return v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });
}

function fmtPct(v: number | null): string {
  if (v === null || v === undefined) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

function fmtNum(v: number | null): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(4);
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function PositionsView() {
  // Data state
  const [data, setData] = useState<GetPositionsResponse | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [fetchLoading, setFetchLoading] = useState(false);

  // Add-form state
  const [form, setForm] = useState<AddPositionRequest>({
    ticker: '',
    shares: 0,
    entry_price: 0,
    entry_date: new Date().toISOString().slice(0, 10),
  });
  const [addError, setAddError] = useState<string | null>(null);
  const [addLoading, setAddLoading] = useState(false);

  // Delete state
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Simulation state
  const [simOpen, setSimOpen] = useState(false);
  const [simNSims, setSimNSims] = useState(1000);
  const [simHorizon, setSimHorizon] = useState(252);
  const [simHistory, setSimHistory] = useState(365);
  const [simResult, setSimResult] = useState<SimulatePortfolioResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);
  const [simLoading, setSimLoading] = useState(false);

  // ── Fetch positions ─────────────────────────────────────────────────────────

  async function fetchPositions() {
    setFetchLoading(true);
    setFetchError(null);
    try {
      const result = await apiClient.getPositions();
      setData(result);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })
        ?.response?.data?.detail ?? (e as { message?: string })?.message ?? 'Failed to load positions.';
      setFetchError(msg);
    } finally {
      setFetchLoading(false);
    }
  }

  useEffect(() => { fetchPositions(); }, []);

  // ── Add position ────────────────────────────────────────────────────────────

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setAddError(null);
    setAddLoading(true);
    try {
      await apiClient.addPosition({ ...form, ticker: form.ticker.toUpperCase() });
      setForm({ ticker: '', shares: 0, entry_price: 0, entry_date: new Date().toISOString().slice(0, 10) });
      await fetchPositions();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })
        ?.response?.data?.detail ?? (e as { message?: string })?.message ?? 'Failed to add position.';
      setAddError(msg);
    } finally {
      setAddLoading(false);
    }
  }

  // ── Delete position ─────────────────────────────────────────────────────────

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await apiClient.deletePosition(id);
      await fetchPositions();
    } catch {
      // silently ignore — row will stay
    } finally {
      setDeletingId(null);
    }
  }

  // ── Simulate portfolio ──────────────────────────────────────────────────────

  async function handleSimulate() {
    setSimError(null);
    setSimLoading(true);
    try {
      const result = await apiClient.simulatePortfolio({
        n_simulations: simNSims,
        horizon_days: simHorizon,
        history_days: simHistory,
      });
      setSimResult(result);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })
        ?.response?.data?.detail ?? (e as { message?: string })?.message ?? 'Simulation failed.';
      setSimError(msg);
    } finally {
      setSimLoading(false);
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  const summary = data?.summary;

  return (
    <div style={s.root}>

      {/* Summary cards */}
      <div style={s.summaryRow}>
        <SummaryCard label="Total Invested" value={fmtMoney(summary?.total_invested ?? null)} />
        <SummaryCard label="Current Value" value={fmtMoney(summary?.total_value ?? null)} />
        <SummaryCard
          label="Total P&L"
          value={fmtMoney(summary?.total_pnl ?? null)}
          color={(summary?.total_pnl ?? 0) >= 0 ? '#00ff88' : '#ff4444'}
        />
        <SummaryCard
          label="Total Return"
          value={fmtPct(summary?.total_return_pct ?? null)}
          color={(summary?.total_return_pct ?? 0) >= 0 ? '#00ff88' : '#ff4444'}
        />
      </div>

      {/* Table + Pie row */}
      <div style={s.midRow}>

        {/* Positions table */}
        <div style={s.tablePanel}>
          <div style={s.panelTitle}>Holdings</div>

          {fetchLoading && <div style={s.msg}>Loading positions…</div>}
          {fetchError && <div style={s.error}>{fetchError}</div>}

          {!fetchLoading && data && (
            data.positions.length === 0
              ? <div style={s.msg}>No positions yet. Add one below.</div>
              : (
                <table style={s.table}>
                  <thead>
                    <tr>
                      {['Ticker', 'Shares', 'Entry $', 'Current $', 'Cost Basis', 'Value', 'P&L', 'Return', ''].map((h) => (
                        <th key={h} style={s.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.positions.map((row: PositionRow) => (
                      <tr key={row.id} style={s.tr}>
                        <td style={s.td}><strong>{row.ticker}</strong></td>
                        <td style={s.td}>{row.shares}</td>
                        <td style={s.td}>{fmtMoney(row.entry_price)}</td>
                        <td style={s.td}>{row.current_price !== null ? fmtMoney(row.current_price) : '—'}</td>
                        <td style={s.td}>{fmtMoney(row.cost_basis)}</td>
                        <td style={s.td}>{fmtMoney(row.current_value)}</td>
                        <td style={{ ...s.td, color: (row.pnl ?? 0) >= 0 ? '#00ff88' : '#ff4444' }}>
                          {fmtMoney(row.pnl)}
                        </td>
                        <td style={{ ...s.td, color: (row.pnl_pct ?? 0) >= 0 ? '#00ff88' : '#ff4444' }}>
                          {fmtPct(row.pnl_pct)}
                        </td>
                        <td style={s.td}>
                          <button
                            style={s.delBtn}
                            onClick={() => handleDelete(row.id)}
                            disabled={deletingId === row.id}
                          >
                            {deletingId === row.id ? '…' : '✕'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
          )}
        </div>

        {/* Allocation pie */}
        {data && data.positions.length > 0 && (
          <div style={s.piePanel}>
            <PlotlyChart figure={data.allocation_chart} height={320} />
          </div>
        )}
      </div>

      {/* Add position form */}
      <div style={s.addPanel}>
        <div style={s.panelTitle}>Add Position</div>
        <form onSubmit={handleAdd} style={s.form}>
          <input
            style={s.input}
            placeholder="Ticker (e.g. AAPL)"
            value={form.ticker}
            onChange={(e) => setForm({ ...form, ticker: e.target.value })}
            required
          />
          <input
            style={s.input}
            type="number"
            placeholder="Shares"
            min="0.0001"
            step="any"
            value={form.shares || ''}
            onChange={(e) => setForm({ ...form, shares: parseFloat(e.target.value) || 0 })}
            required
          />
          <input
            style={s.input}
            type="number"
            placeholder="Entry Price ($)"
            min="0.0001"
            step="any"
            value={form.entry_price || ''}
            onChange={(e) => setForm({ ...form, entry_price: parseFloat(e.target.value) || 0 })}
            required
          />
          <input
            style={s.input}
            type="date"
            value={form.entry_date}
            onChange={(e) => setForm({ ...form, entry_date: e.target.value })}
            required
          />
          <button style={s.addBtn} type="submit" disabled={addLoading}>
            {addLoading ? 'Adding…' : 'Add ▶'}
          </button>
        </form>
        {addError && <div style={s.error}>{addError}</div>}
      </div>

      {/* Simulation panel */}
      <div style={s.simPanel}>
        <button style={s.simToggle} onClick={() => setSimOpen((v) => !v)}>
          {simOpen ? '▼' : '▶'} Run Portfolio Simulation
        </button>

        {simOpen && (
          <div style={s.simBody}>
            <div style={s.sliderRow}>
              <SliderField
                label={`Simulations: ${simNSims}`}
                min={100} max={5000} step={100}
                value={simNSims}
                onChange={setSimNSims}
              />
              <SliderField
                label={`Horizon: ${simHorizon} days`}
                min={30} max={756} step={30}
                value={simHorizon}
                onChange={setSimHorizon}
              />
              <SliderField
                label={`History: ${simHistory} days`}
                min={90} max={1825} step={90}
                value={simHistory}
                onChange={setSimHistory}
              />
            </div>

            <button
              style={s.runBtn}
              onClick={handleSimulate}
              disabled={simLoading}
            >
              {simLoading ? 'Running…' : 'Run ▶'}
            </button>

            {simError && <div style={s.error}>{simError}</div>}

            {simResult && (
              <>
                <PlotlyChart figure={simResult.chart} height={420} />
                <MetricCards
                  metrics={{
                    'Expected Return': fmtPct((simResult.metrics.expected_return ?? 0) * 100),
                    'Prob. of Loss': fmtPct((simResult.metrics.prob_loss ?? 0) * 100),
                    'VaR 95%': fmtNum(simResult.metrics.var_95),
                    'Simulations': simResult.metrics.n_simulations,
                    'Horizon (days)': simResult.metrics.horizon_days,
                    'Positions': simResult.metrics.n_positions,
                  }}
                />
              </>
            )}
          </div>
        )}
      </div>

    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function SummaryCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={s.summaryCard}>
      <div style={s.summaryLabel}>{label}</div>
      <div style={{ ...s.summaryValue, ...(color ? { color } : {}) }}>{value}</div>
    </div>
  );
}

function SliderField({
  label, min, max, step, value, onChange,
}: {
  label: string; min: number; max: number; step: number; value: number;
  onChange: (v: number) => void;
}) {
  return (
    <label style={s.sliderLabel}>
      {label}
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={s.slider}
      />
    </label>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
  root: { display: 'flex', flexDirection: 'column', gap: 16 },

  summaryRow: { display: 'flex', gap: 12, flexWrap: 'wrap' },
  summaryCard: {
    flex: '1 1 150px',
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: '12px 16px',
  },
  summaryLabel: { fontSize: 11, color: '#8888aa', marginBottom: 4 },
  summaryValue: { fontSize: 20, fontWeight: 700, color: '#a0a0ff' },

  midRow: { display: 'flex', gap: 16, alignItems: 'flex-start' },
  tablePanel: {
    flex: 1,
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: 16,
    overflowX: 'auto',
  },
  piePanel: {
    width: 340,
    flexShrink: 0,
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: 8,
  },
  panelTitle: { fontWeight: 600, fontSize: 13, color: '#a0a0ff', marginBottom: 12 },

  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    textAlign: 'left',
    padding: '6px 10px',
    color: '#8888aa',
    fontWeight: 500,
    borderBottom: '1px solid #2d2d44',
    whiteSpace: 'nowrap',
  },
  tr: { borderBottom: '1px solid #1e1e30' },
  td: { padding: '7px 10px', whiteSpace: 'nowrap' },

  delBtn: {
    background: 'transparent',
    border: '1px solid #ff4444',
    color: '#ff4444',
    borderRadius: 4,
    cursor: 'pointer',
    padding: '2px 7px',
    fontSize: 12,
  },

  addPanel: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: 16,
  },
  form: { display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' },
  input: {
    background: '#0d0d1a',
    border: '1px solid #2d2d44',
    borderRadius: 6,
    color: '#e0e0f0',
    padding: '8px 12px',
    fontSize: 13,
    width: 160,
  },
  addBtn: {
    background: '#3333aa',
    border: 'none',
    borderRadius: 6,
    color: '#e0e0f0',
    cursor: 'pointer',
    padding: '8px 18px',
    fontSize: 13,
    fontWeight: 600,
  },

  simPanel: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: 16,
  },
  simToggle: {
    background: 'none',
    border: 'none',
    color: '#a0a0ff',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 600,
    padding: 0,
  },
  simBody: { marginTop: 14, display: 'flex', flexDirection: 'column', gap: 12 },
  sliderRow: { display: 'flex', gap: 24, flexWrap: 'wrap' },
  sliderLabel: { display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#8888aa', minWidth: 200 },
  slider: { accentColor: '#a0a0ff', width: '100%' },
  runBtn: {
    alignSelf: 'flex-start',
    background: '#3333aa',
    border: 'none',
    borderRadius: 6,
    color: '#e0e0f0',
    cursor: 'pointer',
    padding: '8px 20px',
    fontSize: 13,
    fontWeight: 600,
  },

  msg: { color: '#8888aa', fontSize: 13 },
  error: {
    marginTop: 8,
    color: '#ff6666',
    background: '#2a1a1a',
    border: '1px solid #ff4444',
    borderRadius: 6,
    padding: '8px 12px',
    fontSize: 12,
  },
};
