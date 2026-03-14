import React, { createContext, useContext, useState } from 'react';
import Sidebar from './components/Sidebar';
import TechChart from './components/TechChart';
import RiskDashboard from './components/RiskDashboard';
import PortfolioView from './components/PortfolioView';
import SimulationChart from './components/SimulationChart';
import BacktestView from './components/BacktestView';

// ── Shared state ─────────────────────────────────────────────────────────────

export type Tab = 'technical' | 'risk' | 'portfolio' | 'simulation' | 'backtest';

export interface AppState {
  ticker: string;
  setTicker: (v: string) => void;
  start: string;
  setStart: (v: string) => void;
  end: string;
  setEnd: (v: string) => void;
  activeTab: Tab;
  setActiveTab: (t: Tab) => void;
  runSignal: number;
  triggerRun: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const AppContext = createContext<AppState>(null as any);
export const useApp = () => useContext(AppContext);

// ── Tabs config ──────────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string }[] = [
  { id: 'technical', label: 'Technical' },
  { id: 'risk', label: 'Risk' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'simulation', label: 'Simulation' },
  { id: 'backtest', label: 'Backtest' },
];

const TAB_COMPONENTS: Record<Tab, React.FC> = {
  technical: TechChart,
  risk: RiskDashboard,
  portfolio: PortfolioView,
  simulation: SimulationChart,
  backtest: BacktestView,
};

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [ticker, setTicker] = useState('AAPL');
  const [start, setStart] = useState('2024-01-01');
  const [end, setEnd] = useState('2025-01-01');
  const [activeTab, setActiveTab] = useState<Tab>('technical');
  const [runSignal, setRunSignal] = useState(0);

  const triggerRun = () => setRunSignal((n) => n + 1);

  const ActiveComponent = TAB_COMPONENTS[activeTab];

  return (
    <AppContext.Provider
      value={{ ticker, setTicker, start, setStart, end, setEnd, activeTab, setActiveTab, runSignal, triggerRun }}
    >
      <div style={styles.root}>
        <header style={styles.nav}>
          <span style={styles.navTitle}>📈 Financial Analysis</span>
        </header>

        <div style={styles.body}>
          <Sidebar />

          <main style={styles.main}>
            <div style={styles.tabBar}>
              {TABS.map((t) => (
                <button
                  key={t.id}
                  style={{ ...styles.tab, ...(activeTab === t.id ? styles.tabActive : {}) }}
                  onClick={() => setActiveTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div style={styles.content}>
              <ActiveComponent />
            </div>
          </main>
        </div>
      </div>
    </AppContext.Provider>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0d0d1a',
    color: '#e0e0f0',
    fontFamily: "'Inter', 'Segoe UI', sans-serif",
    fontSize: 14,
  },
  nav: {
    height: 48,
    background: '#1a1a2e',
    borderBottom: '1px solid #2d2d44',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    flexShrink: 0,
  },
  navTitle: { fontWeight: 700, fontSize: 16, letterSpacing: 0.5 },
  body: { display: 'flex', flex: 1, overflow: 'hidden' },
  main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  tabBar: {
    display: 'flex',
    background: '#1a1a2e',
    borderBottom: '1px solid #2d2d44',
    padding: '0 8px',
    flexShrink: 0,
  },
  tab: {
    padding: '10px 18px',
    background: 'none',
    border: 'none',
    color: '#8888aa',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    borderBottom: '2px solid transparent',
    transition: 'color 0.2s',
  },
  tabActive: { color: '#a0a0ff', borderBottom: '2px solid #a0a0ff' },
  content: { flex: 1, overflow: 'auto', padding: 16 },
};
