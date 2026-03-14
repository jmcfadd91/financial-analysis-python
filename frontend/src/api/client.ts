import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

// ── Request types ───────────────────────────────────────────────────────────

export interface AnalyzeRequest {
  ticker: string;
  start: string;
  end: string;
  interval?: string;
}

export interface PortfolioRequest {
  tickers: string[];
  weights?: number[];
  start: string;
  end: string;
}

export interface SimulateRequest {
  ticker: string;
  start: string;
  end: string;
  n_simulations?: number;
  horizon_days?: number;
}

export interface BacktestRequest {
  ticker: string;
  strategy: 'sma' | 'rsi';
  params?: Record<string, number>;
  start: string;
  end: string;
  capital?: number;
}

// ── Response types ──────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type PlotlyFig = Record<string, any>;

export interface AnalyzeResponse {
  charts: { price: PlotlyFig; technical: PlotlyFig; risk: PlotlyFig };
  metrics: Record<string, number | null | string>;
}

export interface PortfolioResponse {
  charts: { frontier: PlotlyFig; correlation: PlotlyFig };
  metrics: Record<string, number | null | string | unknown[]>;
}

export interface SimulateResponse {
  chart: PlotlyFig;
  metrics: Record<string, number | null>;
}

export interface BacktestResponse {
  chart: PlotlyFig;
  summary: Record<string, number | null>;
  trades: Record<string, string | number | null>[];
}

// ── Client ──────────────────────────────────────────────────────────────────

export const apiClient = {
  analyze: (req: AnalyzeRequest) =>
    api.post<AnalyzeResponse>('/analyze', req).then((r) => r.data),
  portfolio: (req: PortfolioRequest) =>
    api.post<PortfolioResponse>('/portfolio', req).then((r) => r.data),
  simulate: (req: SimulateRequest) =>
    api.post<SimulateResponse>('/simulate', req).then((r) => r.data),
  backtest: (req: BacktestRequest) =>
    api.post<BacktestResponse>('/backtest', req).then((r) => r.data),
};
