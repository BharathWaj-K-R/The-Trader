export type ExecutionMode = "paper" | "sandbox" | "live"
export type HealthState = "healthy" | "warning" | "critical" | "unknown"

export interface StrategyParams {
  fast_window: number
  slow_window: number
  rsi_window: number
  rsi_entry: number
  rsi_exit: number
}

export interface PaperAccount {
  account_id: string
  cash: number
  asset: number
  last_price: number
  equity: number
  average_entry_price: number
  realized_pnl: number
  unrealized_pnl: number
  drawdown_pct: number
  daily_loss_pct: number
  holding_bars: number
  cooldown_until: number
  trading_halted: boolean
  strategy: StrategyParams
  updated_at?: string
}

export interface ExecutionState {
  account_id?: string
  mode?: ExecutionMode
  environment?: string
  exchange?: string
  armed?: boolean
  kill_switch?: boolean
  orders_today?: number
  max_orders_per_day?: number
  last_reconcile?: string | null
  connected?: boolean
  reason?: string
  [key: string]: unknown
}

export interface RuntimeStatus {
  mode: ExecutionMode
  environment: string
  strategy: StrategyParams
  paper: PaperAccount
  execution: ExecutionState
  [key: string]: unknown
}

export interface Analytics {
  return_pct?: number
  benchmark_return_pct?: number
  excess_return_pct?: number
  max_drawdown_pct?: number
  score?: number
  trade_count?: number
  win_rate_pct?: number
  realized_pnl?: number
  profit_factor?: number
  fees?: number
  slippage?: number
}

export interface Trade {
  id?: number
  run_id?: number
  timestamp: string
  side: "BUY" | "SELL" | string
  price: number
  quantity: number
  fee: number
  pnl: number
  reason: string
}

export interface Experiment {
  id?: number
  created_at?: string
  baseline: string | Record<string, unknown>
  candidate: string | Record<string, unknown>
  baseline_score: number
  candidate_score: number
  accepted: number | boolean
  reason: string
}

export interface ResearchReport {
  id?: number
  created_at?: string
  kind: string
  symbol: string
  timeframe: string
  report: string | Record<string, unknown>
}

export interface MarketBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface ApiConfig {
  mode?: ExecutionMode
  environment?: string
  exchange_id?: string
  symbol?: string
  timeframe?: string
  initial_capital?: number
  max_position_fraction?: number
  max_daily_loss_fraction?: number
  max_drawdown_fraction?: number
  fee_bps?: number
  slippage_bps?: number
  stop_loss_fraction?: number
  take_profit_fraction?: number
  max_holding_bars?: number
  cooldown_bars?: number
  max_live_order_notional?: number
  max_live_orders_per_day?: number
  live_reconcile_interval_seconds?: number
  scheduler_interval_seconds?: number
  live_trading_enabled?: boolean
}

export interface FullResearchResult {
  started_at: string
  finished_at: string
  symbol: string
  timeframe: string
  bars: number
  baseline: { params: StrategyParams; goal: Analytics; analytics: Analytics }
  candidate: { params: StrategyParams; goal: Analytics; analytics: Analytics }
  experiments: Array<Record<string, unknown>>
  walk_forward: Record<string, unknown>
  cost_stress: Record<string, unknown>
  promotion: { promoted: boolean; reason: string }
}
