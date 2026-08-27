import type {
  AIStrategyLabResult,
  Analytics,
  ApiConfig,
  ExecutionState,
  Experiment,
  FullResearchResult,
  MarketBar,
  PaperAccount,
  ResearchReport,
  RuntimeStatus,
  Trade,
} from "./types"

const base = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "")

function headers(apiKey?: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  }
}

async function request<T>(path: string, init: RequestInit = {}, apiKey?: string): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { ...headers(apiKey), ...(init.headers || {}) },
  })

  const text = await response.text()
  let data: unknown = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }

  if (!response.ok) {
    const detail = typeof data === "object" && data && "detail" in data ? String((data as { detail: unknown }).detail) : `Request failed (${response.status})`
    throw new Error(detail)
  }
  return data as T
}

export const api = {
  status: (key?: string) => request<RuntimeStatus>("/api/status", {}, key),
  config: (key?: string) => request<ApiConfig>("/api/config", {}, key),
  trades: (key?: string) => request<Trade[]>("/api/trades", {}, key),
  experiments: (key?: string) => request<Experiment[]>("/api/experiments", {}, key),
  reports: (key?: string) => request<ResearchReport[]>("/api/reports", {}, key),
  aiInsights: (key?: string) => request<unknown[]>("/api/ai/insights", {}, key),
  market: (symbol: string, timeframe: string, bars = 160, key?: string) =>
    request<MarketBar[]>(`/api/market?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&bars=${bars}`, {}, key),
  backtest: (body: { symbol: string; timeframe: string; bars: number }, key?: string) =>
    request<{ goal: Analytics; trades: Trade[] }>("/api/backtest", { method: "POST", body: JSON.stringify(body) }, key),
  improve: (body: { symbol: string; timeframe: string; bars: number; cycles: number }, key?: string) =>
    request<{ goal: Analytics; strategy: RuntimeStatus["strategy"]; experiments: unknown[] }>("/api/improve", { method: "POST", body: JSON.stringify(body) }, key),
  walkForward: (body: { symbol: string; timeframe: string; bars: number; cycles: number; folds: number }, key?: string) =>
    request<Record<string, unknown>>("/api/walk-forward", { method: "POST", body: JSON.stringify(body) }, key),
  fullResearch: (body: { symbol: string; timeframe: string; bars: number; cycles: number; folds: number }, key?: string) =>
    request<FullResearchResult>("/api/research/full", { method: "POST", body: JSON.stringify(body) }, key),
  aiStrategyLab: (body: { symbol: string; timeframe: string; bars: number }, key?: string) =>
    request<AIStrategyLabResult>("/api/ai/strategy-lab", { method: "POST", body: JSON.stringify(body) }, key),
  aiAnalyze: (body: { symbol: string; timeframe: string; bars: number }, key?: string) =>
    request<Record<string, unknown>>("/api/ai/analyze", { method: "POST", body: JSON.stringify(body) }, key),
  aiRegime: (body: { symbol: string; timeframe: string; bars: number }, key?: string) =>
    request<Record<string, unknown>>("/api/ai/regime", { method: "POST", body: JSON.stringify(body) }, key),
  aiAnomaly: (body: { symbol: string; timeframe: string; bars: number }, key?: string) =>
    request<Record<string, unknown>>("/api/ai/anomaly", { method: "POST", body: JSON.stringify(body) }, key),
  paperTick: (body: { symbol: string; timeframe: string }, key?: string) =>
    request<PaperAccount>("/api/paper/tick", { method: "POST", body: JSON.stringify(body) }, key),
  paperReset: (body: { symbol: string; timeframe: string }, key?: string) =>
    request<PaperAccount>("/api/paper/reset", { method: "POST", body: JSON.stringify(body) }, key),
  executionPreflight: (symbol: string, key?: string) =>
    request<ExecutionState>(`/api/execution/preflight?symbol=${encodeURIComponent(symbol)}`, {}, key),
  arm: (token: string, key?: string) => request<ExecutionState>("/api/execution/arm", { method: "POST", body: JSON.stringify({ token }) }, key),
  disarm: (key?: string) => request<ExecutionState>("/api/execution/disarm", { method: "POST", body: JSON.stringify({}) }, key),
  killSwitch: (key?: string) => request<ExecutionState>("/api/execution/kill-switch", { method: "POST", body: JSON.stringify({}) }, key),
  reconcile: (body: { symbol: string; timeframe: string }, key?: string) => request<ExecutionState>("/api/execution/reconcile", { method: "POST", body: JSON.stringify(body) }, key),
  executionOrders: (key?: string) => request<unknown[]>("/api/execution/orders", {}, key),
  executionSnapshots: (key?: string) => request<unknown[]>("/api/execution/snapshots", {}, key),
}
