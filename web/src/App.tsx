import { useEffect, useMemo, useState } from "react"
import { Activity, BarChart3, FlaskConical, Menu, RefreshCw, Settings, Shield, TrendingUp, Wallet, X, Zap } from "lucide-react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { Analytics, ApiConfig, Experiment, MarketBar, ResearchReport, RuntimeStatus, Trade } from "@/lib/types"

type Page = "overview" | "research" | "portfolio" | "execution" | "activity" | "risk" | "settings"

const nav: Array<{ id: Page; label: string; icon: typeof TrendingUp; group: string }> = [
  { id: "overview", label: "Overview", icon: TrendingUp, group: "Workspace" },
  { id: "research", label: "Research", icon: FlaskConical, group: "Workspace" },
  { id: "portfolio", label: "Portfolio", icon: Wallet, group: "Workspace" },
  { id: "execution", label: "Execution", icon: Zap, group: "Workspace" },
  { id: "activity", label: "Activity", icon: Activity, group: "Workspace" },
  { id: "risk", label: "Risk & Safety", icon: Shield, group: "Control" },
  { id: "settings", label: "Settings", icon: Settings, group: "Control" },
]

const money = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—"
const pct = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? `${(v * 100).toFixed(2)}%` : "—"
const num = (v: unknown, digits = 2) => typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "—"
const human = (v: unknown) => typeof v === "string" && v ? v.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()) : "Unknown"

function parseReport(report?: ResearchReport) {
  if (!report) return null
  if (typeof report.report === "object") return report.report as Record<string, any>
  try { return JSON.parse(report.report) as Record<string, any> } catch { return null }
}

function App() {
  const [page, setPage] = useState<Page>(() => {
    const value = window.location.pathname.slice(1) as Page
    return nav.some(item => item.id === value) ? value : "overview"
  })
  const [mobile, setMobile] = useState(false)
  const [status, setStatus] = useState<RuntimeStatus | null>(null)
  const [config, setConfig] = useState<ApiConfig | null>(null)
  const [bars, setBars] = useState<MarketBar[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [reports, setReports] = useState<ResearchReport[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [symbol, setSymbol] = useState("BTC/USDT")
  const [timeframe, setTimeframe] = useState("30m")
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("Ready")
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("the-trader-api-key") || "")

  const refresh = async () => {
    try {
      const [s, c, m, t, e, r] = await Promise.all([
        api.status(apiKey), api.config(apiKey), api.market(symbol, timeframe, 180, apiKey),
        api.trades(apiKey), api.experiments(apiKey), api.reports(apiKey),
      ])
      setStatus(s); setConfig(c); setBars(m); setTrades(t); setExperiments(e); setReports(r)
      const latest = parseReport(r[0])
      setAnalytics(latest?.candidate?.analytics || latest?.candidate?.goal || latest?.analytics || latest?.goal || null)
      setMessage("Updated just now")
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to connect") }
  }

  useEffect(() => { localStorage.setItem("the-trader-api-key", apiKey) }, [apiKey])
  useEffect(() => { void refresh() }, [symbol, timeframe, apiKey])

  const go = (next: Page) => {
    window.history.pushState({}, "", next === "overview" ? "/" : `/${next}`)
    setPage(next); setMobile(false)
  }

  const run = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true); setMessage("Working…")
    try { await action(); setMessage(success); await refresh() }
    catch (error) { setMessage(error instanceof Error ? error.message : "Action failed") }
    finally { setBusy(false) }
  }

  const report = parseReport(reports[0])
  const current = nav.find(item => item.id === page) || nav[0]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <Button className="lg:hidden" size="icon" variant="ghost" onClick={() => setMobile(true)}><Menu className="size-5" /></Button>
            <button onClick={() => go("overview")} className="flex items-center gap-2 text-left">
              <div className="flex size-8 items-center justify-center rounded-md border border-border bg-muted"><TrendingUp className="size-4" /></div>
              <div><div className="text-sm font-semibold">The-Trader</div><div className="text-[11px] text-muted-foreground">Research · Execution</div></div>
            </button>
            <span className="hidden border-l border-border pl-3 text-sm text-muted-foreground lg:block">{current.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-border px-2.5 py-1 text-xs font-medium">{(status?.mode || "paper").toUpperCase()}</span>
            <span className="hidden max-w-56 truncate text-xs text-muted-foreground md:block">{message}</span>
            <Button size="icon" variant="ghost" onClick={() => void refresh()} disabled={busy}><RefreshCw className={busy ? "size-4 animate-spin" : "size-4"} /></Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px]">
        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-60 shrink-0 border-r border-border p-4 lg:block"><Navigation page={page} status={status} onNavigate={go} /></aside>
        {mobile && <div className="fixed inset-0 z-50 lg:hidden"><div className="absolute inset-0 bg-black/60" onClick={() => setMobile(false)} /><aside className="absolute left-0 top-0 h-full w-72 border-r border-border bg-background p-4"><div className="mb-5 flex justify-between"><span className="font-semibold">The-Trader</span><Button size="icon" variant="ghost" onClick={() => setMobile(false)}><X className="size-4" /></Button></div><Navigation page={page} status={status} onNavigate={go} /></aside></div>}
        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          {page === "overview" && <Overview status={status} analytics={analytics} bars={bars} trades={trades} symbol={symbol} timeframe={timeframe} onResearch={() => void run(() => api.fullResearch({ symbol, timeframe, bars: 800, cycles: 10, folds: 4 }, apiKey), "Research completed")} onPaper={() => void run(() => api.paperTick({ symbol, timeframe }, apiKey), "Paper tick completed")} />}
          {page === "research" && <Research analytics={analytics} reports={reports} experiments={experiments} busy={busy} onBacktest={() => void run(async () => { const result = await api.backtest({ symbol, timeframe, bars: 700 }, apiKey); setAnalytics(result.goal) }, "Backtest completed")} onWalk={() => void run(() => api.walkForward({ symbol, timeframe, bars: 700, cycles: 6, folds: 4 }, apiKey), "Walk-forward completed")} onFull={() => void run(() => api.fullResearch({ symbol, timeframe, bars: 800, cycles: 10, folds: 4 }, apiKey), "Full research completed")} />}
          {page === "portfolio" && <Portfolio status={status} trades={trades} />}
          {page === "execution" && <Execution status={status} config={config} apiKey={apiKey} symbol={symbol} timeframe={timeframe} busy={busy} onPreflight={() => void run(() => api.executionPreflight(symbol, apiKey), "Preflight complete")} onArm={() => { const token = window.prompt("Execution arming token"); if (token) void run(() => api.arm(token, apiKey), "Execution armed") }} onDisarm={() => void run(() => api.disarm(apiKey), "Execution disarmed")} onKill={() => void run(() => api.killSwitch(apiKey), "Kill switch active")} onReconcile={() => void run(() => api.reconcile({ symbol, timeframe }, apiKey), "Reconciled")} />}
          {page === "activity" && <ActivityPage trades={trades} experiments={experiments} reports={reports} />}
          {page === "risk" && <Risk status={status} config={config} />}
          {page === "settings" && <SettingsPage symbol={symbol} setSymbol={setSymbol} timeframe={timeframe} setTimeframe={setTimeframe} apiKey={apiKey} setApiKey={setApiKey} config={config} />}
        </main>
      </div>
    </div>
  )
}

function Navigation({ page, status, onNavigate }: { page: Page; status: RuntimeStatus | null; onNavigate: (page: Page) => void }) {
  return <div className="flex h-full flex-col">
    <div className="mb-5 rounded-lg border border-border bg-muted/20 p-3"><div className="text-[10px] uppercase tracking-[.18em] text-muted-foreground">Environment</div><div className="mt-1 text-sm font-medium">{human(status?.environment || "development")}</div><div className="mt-1 text-xs text-muted-foreground">{(status?.mode || "paper").toUpperCase()} execution</div></div>
    {["Workspace", "Control"].map(group => <div key={group} className="mb-5"><div className="px-2 pb-2 text-[10px] uppercase tracking-[.18em] text-muted-foreground">{group}</div><div className="space-y-1">{nav.filter(item => item.group === group).map(item => { const Icon = item.icon; const active = page === item.id; return <button key={item.id} onClick={() => onNavigate(item.id)} className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm ${active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon className="size-4" /><span>{item.label}</span></button> })}</div></div>)}
    <div className="mt-auto rounded-lg border border-border p-3 text-xs text-muted-foreground"><div className="font-medium text-foreground">Risk controls</div><p className="mt-1 leading-5">Policy, preflight and reconciliation remain visible before consequential actions.</p></div>
  </div>
}

function Header({ eyebrow, title, subtitle, action }: { eyebrow: string; title: string; subtitle: string; action?: React.ReactNode }) { return <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><div className="mb-2 text-[10px] uppercase tracking-[.2em] text-muted-foreground">{eyebrow}</div><h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{subtitle}</p></div>{action}</div> }
function Metric({ label, value, detail }: { label: string; value: string; detail: string }) { return <Card><CardContent className="p-5"><div className="text-xs text-muted-foreground">{label}</div><div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div><div className="mt-1 text-xs text-muted-foreground">{detail}</div></CardContent></Card> }
function Row({ label, value }: { label: string; value: string }) { return <div className="flex justify-between gap-4 border-b border-border py-3 last:border-0"><span className="text-sm text-muted-foreground">{label}</span><span className="text-sm font-medium">{value}</span></div> }

function Overview({ status, analytics, bars, trades, symbol, timeframe, onResearch, onPaper }: { status: RuntimeStatus | null; analytics: Analytics | null; bars: MarketBar[]; trades: Trade[]; symbol: string; timeframe: string; onResearch: () => void; onPaper: () => void }) {
  const chart = useMemo(() => bars.map(b => ({ time: new Date(b.time).toLocaleDateString(undefined, { month: "short", day: "numeric" }), close: b.close })), [bars])
  const p = status?.paper
  return <><Header eyebrow="Overview" title="A calm control room for the trading system." subtitle="Research, portfolio state and execution posture without turning every metric into a siren." action={<div className="flex gap-2"><Button variant="outline" onClick={onPaper}>Paper tick</Button><Button onClick={onResearch}>Run research</Button></div>} />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Equity" value={money(p?.equity)} detail={`Cash ${money(p?.cash)}`} /><Metric label="Return" value={pct(analytics?.return_pct)} detail={`Score ${num(analytics?.score)}`} /><Metric label="Drawdown" value={pct(p?.drawdown_pct)} detail={`Daily loss ${pct(p?.daily_loss_pct)}`} /><Metric label="Position" value={num(p?.asset, 5)} detail={`${symbol} · ${timeframe}`} /></div>
    <div className="mt-4 grid gap-4 xl:grid-cols-[1.7fr_1fr]"><Card><CardHeader><CardTitle>Market</CardTitle><CardDescription>{symbol} · {timeframe}</CardDescription></CardHeader><CardContent><div className="h-72">{chart.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><XAxis dataKey="time" hide /><YAxis hide domain={["auto", "auto"]} /><Tooltip contentStyle={{ background: "hsl(var(--background))", border: "1px solid hsl(var(--border))", borderRadius: 8 }} /><Area type="monotone" dataKey="close" stroke="currentColor" fill="currentColor" fillOpacity={0.08} /></AreaChart></ResponsiveContainer> : <Empty title="No market data" body="Connect the backend to populate the chart." />}</div></CardContent></Card><Card><CardHeader><CardTitle>Execution posture</CardTitle><CardDescription>Current runtime state.</CardDescription></CardHeader><CardContent><Row label="Mode" value={(status?.mode || "paper").toUpperCase()} /><Row label="Environment" value={human(status?.environment)} /><Row label="Armed" value={status?.execution?.armed ? "Yes" : "No"} /><Row label="Kill switch" value={status?.execution?.kill_switch ? "Active" : "Clear"} /></CardContent></Card></div>
    <Card className="mt-4"><CardHeader><CardTitle>Recent trades</CardTitle></CardHeader><CardContent>{trades.length ? <div className="space-y-1">{trades.slice(0, 6).map((t, i) => <div key={`${t.timestamp}-${i}`} className="flex items-center justify-between border-b border-border py-3 last:border-0"><div><div className="text-sm font-medium">{t.side} · {human(t.reason)}</div><div className="text-xs text-muted-foreground">{new Date(t.timestamp).toLocaleString()}</div></div><div className="text-right"><div className="text-sm">{money(t.price)}</div><div className="text-xs text-muted-foreground">{num(t.quantity, 5)}</div></div></div>)}</div> : <Empty title="No trades yet" body="Paper execution activity will appear here." />}</CardContent></Card></>
}

function Research({ analytics, reports, experiments, busy, onBacktest, onWalk, onFull }: { analytics: Analytics | null; reports: ResearchReport[]; experiments: Experiment[]; busy: boolean; onBacktest: () => void; onWalk: () => void; onFull: () => void }) { return <><Header eyebrow="Research" title="Evidence before exposure." subtitle="Run a baseline, test improvements, validate robustness and inspect persisted reports." action={<div className="flex flex-wrap gap-2"><Button variant="outline" disabled={busy} onClick={onBacktest}>Backtest</Button><Button variant="outline" disabled={busy} onClick={onWalk}>Walk-forward</Button><Button disabled={busy} onClick={onFull}>Full research</Button></div>} /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Return" value={pct(analytics?.return_pct)} detail="Latest research" /><Metric label="Max drawdown" value={pct(analytics?.max_drawdown_pct)} detail="Risk profile" /><Metric label="Win rate" value={analytics?.win_rate_pct != null ? `${analytics.win_rate_pct.toFixed(2)}%` : "—"} detail={`${analytics?.trade_count ?? "—"} trades`} /><Metric label="Profit factor" value={num(analytics?.profit_factor)} detail={`Fees ${money(analytics?.fees)}`} /></div><div className="mt-4 grid gap-4 xl:grid-cols-2"><Card><CardHeader><CardTitle>Experiments</CardTitle><CardDescription>{experiments.length} persisted experiment records.</CardDescription></CardHeader><CardContent>{experiments.length ? experiments.slice(0, 8).map((e, i) => <Row key={e.id ?? i} label={e.reason} value={`${num(e.baseline_score)} → ${num(e.candidate_score)}`} />) : <Empty title="No experiments" body="Run research to create experiment records." />}</CardContent></Card><Card><CardHeader><CardTitle>Reports</CardTitle><CardDescription>Persisted research artifacts.</CardDescription></CardHeader><CardContent>{reports.length ? reports.slice(0, 8).map((r, i) => <Row key={r.id ?? i} label={`${human(r.kind)} · ${r.symbol}`} value={r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"} />) : <Empty title="No reports" body="Completed research reports will appear here." />}</CardContent></Card></div></> }

function Portfolio({ status, trades }: { status: RuntimeStatus | null; trades: Trade[] }) { const p = status?.paper; return <><Header eyebrow="Portfolio" title="Know what the account is actually carrying." subtitle="Position, capital, P&L and holding state from the paper account." /><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Equity" value={money(p?.equity)} detail={`Cash ${money(p?.cash)}`} /><Metric label="Asset" value={num(p?.asset, 5)} detail={`Entry ${money(p?.average_entry_price)}`} /><Metric label="Realized P&L" value={money(p?.realized_pnl)} detail="Closed trades" /><Metric label="Unrealized P&L" value={money(p?.unrealized_pnl)} detail={`${p?.holding_bars ?? 0} holding bars`} /></div><Card className="mt-4"><CardHeader><CardTitle>Account state</CardTitle></CardHeader><CardContent><Row label="Last price" value={money(p?.last_price)} /><Row label="Drawdown" value={pct(p?.drawdown_pct)} /><Row label="Daily loss" value={pct(p?.daily_loss_pct)} /><Row label="Trading halted" value={p?.trading_halted ? "Yes" : "No"} /></CardContent></Card><Card className="mt-4"><CardHeader><CardTitle>Trade ledger</CardTitle></CardHeader><CardContent>{trades.length ? trades.slice(0, 20).map((t, i) => <Row key={t.id ?? i} label={`${t.side} · ${human(t.reason)}`} value={`${money(t.price)} · P&L ${money(t.pnl)}`} />) : <Empty title="No trades" body="The ledger is empty." />}</CardContent></Card></> }

function Execution({ status, config, apiKey, symbol, timeframe, busy, onPreflight, onArm, onDisarm, onKill, onReconcile }: { status: RuntimeStatus | null; config: ApiConfig | null; apiKey: string; symbol: string; timeframe: string; busy: boolean; onPreflight: () => void; onArm: () => void; onDisarm: () => void; onKill: () => void; onReconcile: () => void }) { return <><Header eyebrow="Execution" title="Consequential actions stay behind controls." subtitle="Preflight, arming, reconciliation and kill-switch actions are explicit." /><div className="grid gap-4 lg:grid-cols-2"><Card><CardHeader><CardTitle>Runtime</CardTitle><CardDescription>{symbol} · {timeframe}</CardDescription></CardHeader><CardContent><Row label="Mode" value={(status?.mode || "paper").toUpperCase()} /><Row label="Connected" value={status?.execution?.connected ? "Yes" : "No"} /><Row label="Armed" value={status?.execution?.armed ? "Yes" : "No"} /><Row label="Orders today" value={String(status?.execution?.orders_today ?? 0)} /><Row label="Max orders" value={String(config?.max_live_orders_per_day ?? "—")} /></CardContent></Card><Card><CardHeader><CardTitle>Actions</CardTitle><CardDescription>Use the least consequential operation first.</CardDescription></CardHeader><CardContent className="flex flex-wrap gap-2"><Button variant="outline" disabled={busy} onClick={onPreflight}>Preflight</Button><Button variant="outline" disabled={busy || !apiKey} onClick={onArm}>Arm</Button><Button variant="outline" disabled={busy} onClick={onDisarm}>Disarm</Button><Button variant="outline" disabled={busy} onClick={onReconcile}>Reconcile</Button><Button variant="destructive" disabled={busy} onClick={onKill}>Kill switch</Button></CardContent></Card></div></> }

function ActivityPage({ trades, experiments, reports }: { trades: Trade[]; experiments: Experiment[]; reports: ResearchReport[] }) { const items = [...trades.map(t => ({ at: t.timestamp, label: `${t.side} · ${human(t.reason)}`, detail: money(t.price), type: "Trade" })), ...experiments.map(e => ({ at: e.created_at || "", label: e.accepted ? "Candidate accepted" : "Candidate rejected", detail: e.reason, type: "Experiment" })), ...reports.map(r => ({ at: r.created_at || "", label: human(r.kind), detail: `${r.symbol} · ${r.timeframe}`, type: "Research" }))].sort((a, b) => b.at.localeCompare(a.at)); return <><Header eyebrow="Activity" title="One timeline for system history." subtitle="Trades, experiments and research records without hunting through separate screens." /><Card><CardContent className="p-0">{items.length ? items.slice(0, 50).map((item, i) => <div key={`${item.at}-${i}`} className="flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-0"><div><div className="text-sm font-medium">{item.label}</div><div className="mt-1 text-xs text-muted-foreground">{item.type} · {item.detail}</div></div><div className="shrink-0 text-xs text-muted-foreground">{item.at ? new Date(item.at).toLocaleString() : "—"}</div></div>) : <Empty title="No activity" body="Activity appears as the system runs." />}</CardContent></Card></> }

function Risk({ status, config }: { status: RuntimeStatus | null; config: ApiConfig | null }) { const p = status?.paper; return <><Header eyebrow="Control" title="Risk & safety." subtitle="Make the risk budget visible before the system takes additional exposure." /><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><Metric label="Daily loss" value={pct(p?.daily_loss_pct)} detail={`Limit ${pct(config?.max_daily_loss_fraction)}`} /><Metric label="Drawdown" value={pct(p?.drawdown_pct)} detail={`Limit ${pct(config?.max_drawdown_fraction)}`} /><Metric label="Position" value={pct(config?.max_position_fraction)} detail="Maximum allocation" /></div><Card className="mt-4"><CardHeader><CardTitle>Protective policy</CardTitle></CardHeader><CardContent><Row label="Stop loss" value={pct(config?.stop_loss_fraction)} /><Row label="Take profit" value={pct(config?.take_profit_fraction)} /><Row label="Max holding" value={String(config?.max_holding_bars ?? "Disabled")} /><Row label="Cooldown" value={String(config?.cooldown_bars ?? "Disabled")} /><Row label="Kill switch" value={status?.execution?.kill_switch ? "ACTIVE" : "Clear"} /></CardContent></Card></> }

function SettingsPage({ symbol, setSymbol, timeframe, setTimeframe, apiKey, setApiKey, config }: { symbol: string; setSymbol: (v: string) => void; timeframe: string; setTimeframe: (v: string) => void; apiKey: string; setApiKey: (v: string) => void; config: ApiConfig | null }) { return <><Header eyebrow="Settings" title="Runtime preferences." subtitle="These controls shape the dashboard context. Execution policy remains server-side." /><Card><CardHeader><CardTitle>Market context</CardTitle></CardHeader><CardContent className="grid gap-4 sm:grid-cols-2"><label className="text-sm"><span className="mb-2 block text-muted-foreground">Symbol</span><input value={symbol} onChange={e => setSymbol(e.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3" /></label><label className="text-sm"><span className="mb-2 block text-muted-foreground">Timeframe</span><input value={timeframe} onChange={e => setTimeframe(e.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3" /></label><label className="text-sm sm:col-span-2"><span className="mb-2 block text-muted-foreground">API key</span><input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3" placeholder="Optional for protected deployments" /></label></CardContent></Card><Card className="mt-4"><CardHeader><CardTitle>Server policy</CardTitle><CardDescription>Read-only configuration from the backend.</CardDescription></CardHeader><CardContent><Row label="Mode" value={(config?.mode || "paper").toUpperCase()} /><Row label="Exchange" value={config?.exchange_id || "—"} /><Row label="Initial capital" value={money(config?.initial_capital)} /><Row label="Fee" value={config?.fee_bps != null ? `${config.fee_bps} bps` : "—"} /><Row label="Slippage" value={config?.slippage_bps != null ? `${config.slippage_bps} bps` : "—"} /></CardContent></Card></> }

function Empty({ title, body }: { title: string; body: string }) { return <div className="p-10 text-center"><div className="text-sm font-medium">{title}</div><p className="mt-2 text-xs text-muted-foreground">{body}</p></div> }

export default App
