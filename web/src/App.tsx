import { useEffect, useMemo, useState, type ReactNode } from "react"
import { AppShell, type RouteId } from "@/components/app-shell"
import { Overview } from "@/pages/overview"
import { ResearchPage } from "@/pages/research"
import { AILabPage } from "@/pages/ai-lab"
import { PortfolioPage } from "@/pages/portfolio"
import { ExecutionPage } from "@/pages/execution"
import { ActivityPage } from "@/pages/activity"
import { RiskPage } from "@/pages/risk"
import { SettingsPage } from "@/pages/settings"
import { api } from "@/lib/api"
import type { AIStrategyLabResult, Analytics, ApiConfig, Experiment, MarketBar, ResearchReport, RuntimeStatus, Trade } from "@/lib/types"

const routes: RouteId[] = ["overview", "research", "ai-lab", "portfolio", "execution", "activity", "risk", "settings"]
const routeFromPath = (): RouteId => {
  const path = window.location.pathname.replace(/^\//, "")
  return routes.includes(path as RouteId) ? path as RouteId : "overview"
}
const readClientKey = () => sessionStorage.getItem("the-trader-api-key") ?? ""
const asArray = <T,>(value: unknown): T[] => Array.isArray(value) ? value as T[] : []

export default function App() {
  const [route, setRoute] = useState<RouteId>(routeFromPath)
  const [status, setStatus] = useState<RuntimeStatus | null>(null)
  const [config, setConfig] = useState<ApiConfig | null>(null)
  const [market, setMarket] = useState<MarketBar[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [reports, setReports] = useState<ResearchReport[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [aiResult, setAIResult] = useState<AIStrategyLabResult | null>(null)
  const [symbol, setSymbol] = useState("BTC/USDT")
  const [timeframe, setTimeframe] = useState("30m")
  const [apiKey, setApiKey] = useState(readClientKey)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState("Ready")

  const parseReport = (report?: ResearchReport) => {
    if (!report) return null
    if (report.report && typeof report.report === "object") return report.report as Record<string, unknown>
    if (typeof report.report !== "string") return null
    try { return JSON.parse(report.report) as Record<string, unknown> } catch { return null }
  }

  const refresh = async () => {
    try {
      const [nextStatus, nextConfig, nextMarket, nextTrades, nextExperiments, nextReports, nextAI] = await Promise.all([
        api.status(apiKey), api.config(apiKey), api.market(symbol, timeframe, 180, apiKey), api.trades(apiKey), api.experiments(apiKey), api.reports(apiKey), api.aiInsights(apiKey),
      ])
      const safeMarket = asArray<MarketBar>(nextMarket)
      const safeTrades = asArray<Trade>(nextTrades)
      const safeExperiments = asArray<Experiment>(nextExperiments)
      const safeReports = asArray<ResearchReport>(nextReports)
      setStatus(nextStatus); setConfig(nextConfig); setMarket(safeMarket); setTrades(safeTrades); setExperiments(safeExperiments); setReports(safeReports)
      const latest = parseReport(safeReports[0])
      const latestRecord = latest as { candidate?: { analytics?: Analytics; goal?: Analytics }; analytics?: Analytics; goal?: Analytics } | null
      setAnalytics(latestRecord?.candidate?.analytics ?? latestRecord?.candidate?.goal ?? latestRecord?.analytics ?? latestRecord?.goal ?? null)
      const latestAI = asArray<{ kind?: string; payload?: unknown }>(nextAI)[0]
      if (latestAI?.kind === "strategy_lab" && latestAI.payload && typeof latestAI.payload === "object") setAIResult(latestAI.payload as AIStrategyLabResult)
      setNotice("Updated just now")
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to connect")
    }
  }

  const run = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true); setNotice("Working…")
    try { await action(); await refresh(); setNotice(success) }
    catch (error) { setNotice(error instanceof Error ? error.message : "Action failed") }
    finally { setBusy(false) }
  }

  const navigate = (next: RouteId) => {
    window.history.pushState({}, "", next === "overview" ? "/" : `/${next}`)
    setRoute(next)
  }

  useEffect(() => { const onPop = () => setRoute(routeFromPath()); window.addEventListener("popstate", onPop); return () => window.removeEventListener("popstate", onPop) }, [])
  useEffect(() => { if (apiKey) sessionStorage.setItem("the-trader-api-key", apiKey); else sessionStorage.removeItem("the-trader-api-key") }, [apiKey])
  useEffect(() => { void refresh() }, [symbol, timeframe, apiKey])

  const latestReport = useMemo(() => parseReport(reports[0]), [reports])
  let page: ReactNode

  if (route === "overview") {
    page = <Overview status={status} analytics={analytics} bars={market} trades={trades} report={latestReport} onResearch={() => run(() => api.fullResearch({ symbol, timeframe, bars: 800, cycles: 10, folds: 4 }, apiKey), "Research completed")} onPaper={() => run(() => api.paperTick({ symbol, timeframe }, apiKey), "Paper tick completed")} busy={busy} symbol={symbol} timeframe={timeframe} />
  } else if (route === "research") {
    page = <ResearchPage status={status} analytics={analytics} reports={reports} experiments={experiments} busy={busy} onBacktest={() => run(() => api.backtest({ symbol, timeframe, bars: 700 }, apiKey), "Backtest completed")} onWalk={() => run(() => api.walkForward({ symbol, timeframe, bars: 700, cycles: 6, folds: 4 }, apiKey), "Walk-forward completed")} onFull={() => run(() => api.fullResearch({ symbol, timeframe, bars: 800, cycles: 10, folds: 4 }, apiKey), "Full research completed")} />
  } else if (route === "ai-lab") {
    page = <AILabPage result={aiResult} enabled={Boolean(config?.ai_enabled)} busy={busy} onRun={() => run(() => api.aiStrategyLab({ symbol, timeframe, bars: 400 }, apiKey).then(setAIResult), "AI evolution cycle completed")} onCopilot={(prompt) => api.aiCopilot(prompt, apiKey).then((value) => value.answer)} />
  } else if (route === "portfolio") {
    page = <PortfolioPage status={status} trades={trades} bars={market} />
  } else if (route === "execution") {
    page = <ExecutionPage status={status} config={config} apiKey={apiKey} setApiKey={setApiKey} busy={busy} onPreflight={() => run(() => api.executionPreflight(symbol, apiKey), "Preflight complete")} onArm={() => { const token = window.prompt("Execution arming token"); if (token) void run(() => api.arm(token, apiKey), "Execution armed") }} onDisarm={() => run(() => api.disarm(apiKey), "Execution disarmed")} onKill={() => run(() => api.killSwitch(apiKey), "Kill switch active")} onReconcile={() => run(() => api.reconcile({ symbol, timeframe }, apiKey), "Reconciled")} />
  } else if (route === "activity") {
    page = <ActivityPage trades={trades} experiments={experiments} reports={reports} />
  } else if (route === "risk") {
    page = <RiskPage status={status} config={config} />
  } else {
    page = <SettingsPage symbol={symbol} setSymbol={setSymbol} timeframe={timeframe} setTimeframe={setTimeframe} apiKey={apiKey} setApiKey={setApiKey} config={config} />
  }

  return <AppShell route={route} status={status} notice={notice} busy={busy} onNavigate={navigate} onRefresh={() => void refresh()}>{page}</AppShell>
}
