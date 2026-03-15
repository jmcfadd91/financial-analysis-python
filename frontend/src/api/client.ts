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
  benchmark?: string;
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

// ── Positions types ──────────────────────────────────────────────────────────

export interface AddPositionRequest {
  ticker: string;
  shares: number;
  entry_price: number;
  entry_date: string;
}

export interface Position {
  id: string;
  ticker: string;
  shares: number;
  entry_price: number;
  entry_date: string;
}

export interface PositionRow extends Position {
  current_price: number | null;
  cost_basis: number;
  current_value: number | null;
  pnl: number | null;
  pnl_pct: number | null;
}

export interface PortfolioSummary {
  total_invested: number;
  total_value: number | null;
  total_pnl: number | null;
  total_return_pct: number | null;
}

export interface GetPositionsResponse {
  positions: PositionRow[];
  summary: PortfolioSummary;
  allocation_chart: PlotlyFig;
}

export interface SimulatePortfolioRequest {
  n_simulations?: number;
  horizon_days?: number;
  history_days?: number;
}

export interface SimulatePortfolioResponse {
  chart: PlotlyFig;
  metrics: Record<string, number | null>;
}

// ── Watchlist types ──────────────────────────────────────────────────────────

export interface WatchlistItem {
  ticker: string;
  current_price: number | null;
  day_change_pct: number | null;
  rsi: number | null;
  prices: number[];
}

export interface GetWatchlistResponse {
  items: WatchlistItem[];
}

export interface AddWatchlistRequest {
  ticker: string;
}

// ── Notification types ────────────────────────────────────────────────────────

export interface NotificationConfigRequest {
  bot_token: string;
  chat_id: string;
}

export interface NotificationConfigResponse {
  bot_token_set: boolean;
  bot_token_masked: string;
  chat_id: string;
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
  getPositions: () =>
    api.get<GetPositionsResponse>('/positions').then((r) => r.data),
  addPosition: (req: AddPositionRequest) =>
    api.post<Position>('/positions', req).then((r) => r.data),
  deletePosition: (id: string) =>
    api.delete(`/positions/${id}`).then((r) => r.data),
  simulatePortfolio: (req: SimulatePortfolioRequest) =>
    api.post<SimulatePortfolioResponse>('/positions/simulate', req).then((r) => r.data),
  getWatchlist: () =>
    api.get<GetWatchlistResponse>('/watchlist').then((r) => r.data),
  addToWatchlist: (req: AddWatchlistRequest) =>
    api.post<WatchlistItem>('/watchlist', req).then((r) => r.data),
  removeFromWatchlist: (ticker: string) =>
    api.delete(`/watchlist/${ticker}`).then((r) => r.data),
  getNotificationConfig: () =>
    api.get<NotificationConfigResponse>('/notifications/config').then((r) => r.data),
  saveNotificationConfig: (req: NotificationConfigRequest) =>
    api.post<NotificationConfigResponse>('/notifications/config', req).then((r) => r.data),
  sendTestNotification: () =>
    api.post<{ status: string }>('/notifications/test').then((r) => r.data),
};
