import { useEffect, useMemo, useState } from "react"
import { Activity, ArrowDownRight, ArrowUpRight, Bot, ChartNoAxesCombined, ChevronDown, CircleAlert, Clock3, Command, FlaskConical, Gauge, LockKeyhole, Play, RefreshCw, ShieldCheck, SlidersHorizontal, Sparkles, Wallet, Zap } from "lucide-react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { AppSidebar } from "@/components/app-sidebar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

type Status = { mode: string; environment: string; strategy: Record<string, number>; paper: Record<string, number>; execution: Record<string, unknown> }
type Analytics = { return_pct?: number; benchmark_return_pct?: number; excess_return_pct?: number; max_drawdown_pct?: number; score?: number; trade_count?: number; win_rate_pct?: number; realized_pnl?: number }

function n(v: unknown, digits = 2) { return typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "—" }
function pct(v: unknown) { return typeof v === "number" && Number.isFinite(v) ? `${(v * 100).toFixed(2)}%` : "—" }

function App() {
  const [page, setPage] = useState("Overview")
  const [status, setStatus] = useState<Status | null>(null)
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [bars, setBars] = useState<Array<{time: string; close: number}>>([])
  const [reports, setReports] = useState<any[]>([])
  const [trades, setTrades] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("Ready")
  const [symbol, setSymbol] = useState("BTC/USDT")
  const [timeframe, setTimeframe] = useState("30m")
  const [apiKey, setApiKey] = useState(localStorage.getItem("the-trader-api-key") || "")

  const headers = useMemo(() => ({ "Content-Type": "application/json", ...(apiKey ? { "X-API-Key": apiKey } : {}) }), [apiKey])

  async function api(path: string, init?: RequestInit) {
    const res = await fetch(`${API}${path}`, { ...init, headers: { ...headers, ...(init?.headers || {}) } })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Request failed")
    return data
  }

  async function refresh() {
    try {
      const [s, t, r, m] = await Promise.all([
        api("/api/status"), api("/api/trades"), api("/api/reports"), api(`/api/market?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&bars=140`),
      ])
      setStatus(s); setTrades(t); setReports(r); setBars(m.map((x: any) => ({ time: x.time, close: x.close })))
      if (r?.[0]?.report) {
        const report = JSON.parse(r[0].report)
        const candidate = report.candidate_goal || report.baseline?.goal || report.goal
        if (candidate) setAnalytics(candidate)
      }
      setMessage("Updated just now")
    } catch (e) { setMessage(e instanceof Error ? e.message : "Unable to connect") }
  }

  useEffect(() => { localStorage.setItem("the-trader-api-key", apiKey) }, [apiKey])
  useEffect(() => { refresh() }, [])

  async function action(path: string, body: unknown) {
    setLoading(true); setMessage("Working…")
    try { const data = await api(path, { method: "POST", body: JSON.stringify(body) }); setMessage("Completed"); await refresh(); return data }
    catch (e) { setMessage(e instanceof Error ? e.message : "Action failed") }
    finally { setLoading(false) }
  }

  const mode = status?.mode || "paper"
  const paper = status?.paper || {}
  const execution = status?.execution || {}

  return <SidebarProvider>
    <AppSidebar page={page} onPage={setPage} />
    <div className="min-h-svh lg:pl-[228px]">
      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3"><SidebarTrigger /><div className="hidden h-5 w-px bg-border sm:block" /><div><div className="text-sm font-medium">{page}</div><div className="text-xs text-muted-foreground">{message}</div></div></div>
          <div className="flex items-center gap-2"><Badge variant={mode === "live" ? "danger" : mode === "sandbox" ? "warning" : "success"}>{mode.toUpperCase()}</Badge><Button size="icon" variant="ghost" onClick={refresh} disabled={loading}><RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} /></Button><div className="hidden items-center gap-2 rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground md:flex"><Command className="size-3" /> K / search</div></div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] p-4 sm:p-6">
        {page === "Overview" && <Overview status={status} analytics={analytics} bars={bars} trades={trades} paper={paper} execution={execution} symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} onResearch={() => action("/api/research/full", { symbol, timeframe, bars: 800, cycles: 10, folds: 4 })} onPaper={() => action("/api/paper/tick", { symbol, timeframe })} />}
        {page === "Research" && <Research reports={reports} analytics={analytics} loading={loading} onResearch={() => action("/api/research/full", { symbol, timeframe, bars: 800, cycles: 10, folds: 4 })} onBacktest={() => api(`/api/backtest`, { method: "POST", body: JSON.stringify({ symbol, timeframe, bars: 700 }) }).then(x => { setAnalytics(x.goal); setMessage("Backtest complete") }).catch(e => setMessage(e.message))} />}
        {page === "Portfolio" && <Portfolio paper={paper} trades={trades} mode={mode} />}
        {page === "Execution" && <Execution mode={mode} execution={execution} apiKey={apiKey} setApiKey={setApiKey} loading={loading} onPreflight={() => api(`/api/execution/preflight?symbol=${encodeURIComponent(symbol)}`).then(x => setMessage(x.ready ? "Preflight passed" : x.reason)).catch(e => setMessage(e.message))} onArm={() => { const token = prompt("Execution arming token"); if (token !== null) action("/api/execution/arm", { token }) }} onDisarm={() => action("/api/execution/disarm", {})} onKill={() => { if (confirm("Activate the emergency kill switch?")) action("/api/execution/kill-switch", {}) }} onReconcile={() => action("/api/execution/reconcile", { symbol, timeframe })} />}
        {page === "Activity" && <ActivityPage trades={trades} reports={reports} />}
        {page === "Risk & Safety" && <RiskPage status={status} execution={execution} />}
        {page === "Settings" && <SettingsPage symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} apiKey={apiKey} setApiKey={setApiKey} />}
      </main>
    </div>
  </SidebarProvider>
}

function Overview({ status, analytics, bars, trades, paper, execution, symbol, timeframe, setSymbol, setTimeframe, onResearch, onPaper }: any) {
  const last = bars.length ? bars[bars.length - 1].close : null
  return <div className="space-y-6">
    <section className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end"><div><div className="mb-2 flex items-center gap-2"><Badge variant="secondary">COMMAND CENTER</Badge><span className="text-xs text-muted-foreground">Live account state and research quality in one place</span></div><h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Good afternoon. Here is what matters.</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Monitor the portfolio, validate the strategy, and move through execution stages deliberately. No glitter, no casino dashboard.</p></div><div className="flex gap-2"><Button variant="outline" onClick={onPaper}><Play className="size-4" /> Paper tick</Button><Button onClick={onResearch}><Sparkles className="size-4" /> Run research</Button></div></section>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
      ["Equity", n(paper.equity), "Current portfolio value", Wallet], ["Strategy return", pct(analytics?.return_pct), "Latest measured run", ChartNoAxesCombined], ["Drawdown", pct(analytics?.max_drawdown_pct), "Peak-to-trough", ShieldCheck], ["Market price", last ? `$${n(last, 2)}` : "—", `${symbol} · ${timeframe}`, Activity],
    ].map(([label, value, sub, Icon]: any) => <Card key={label}><CardContent className="p-4"><div className="flex items-start justify-between"><div><div className="text-xs text-muted-foreground">{label}</div><div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div><div className="mt-1 text-xs text-muted-foreground">{sub}</div></div><div className="rounded-lg border border-border bg-muted/30 p-2"><Icon className="size-4 text-muted-foreground" /></div></div></CardContent></Card> )}</div>
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,.7fr)]">
      <Card><CardHeader className="pb-2"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><CardTitle>Market pulse</CardTitle><CardDescription>Actual public market data from the active symbol.</CardDescription></div><div className="flex gap-2"><input className="h-9 w-28 rounded-md border border-input bg-transparent px-3 text-sm outline-none" value={symbol} onChange={e=>setSymbol(e.target.value)} /><select className="h-9 rounded-md border border-input bg-transparent px-3 text-sm" value={timeframe} onChange={e=>setTimeframe(e.target.value)}><option>15m</option><option>30m</option><option>1h</option><option>4h</option></select></div></div></CardHeader><CardContent className="h-[330px] pb-5"><ResponsiveContainer width="100%" height="100%"><AreaChart data={bars}><defs><linearGradient id="pulse" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7c7cff" stopOpacity={0.28}/><stop offset="100%" stopColor="#7c7cff" stopOpacity={0}/></linearGradient></defs><XAxis dataKey="time" hide /><YAxis domain={['auto','auto']} hide /><Tooltip contentStyle={{background:'#111418', border:'1px solid #252a30', borderRadius:10, fontSize:12}} labelFormatter={(x)=>new Date(x).toLocaleString()} formatter={(v:number)=>[`$${v.toFixed(2)}`, 'Price']} /><Area type="monotone" dataKey="close" stroke="#7c7cff" fill="url(#pulse)" strokeWidth={2} dot={false}/></AreaChart></ResponsiveContainer></CardContent></Card>
      <Card><CardHeader><CardTitle>Execution posture</CardTitle><CardDescription>One glance before money moves.</CardDescription></CardHeader><CardContent className="space-y-4"><MetricRow label="Runtime mode" value={modeLabel(status?.mode)} /><MetricRow label="Armed" value={execution?.armed ? "Yes" : "No"} tone={execution?.armed ? "good" : "muted"} /><MetricRow label="Kill switch" value={execution?.kill_switch ? "Active" : "Clear"} tone={execution?.kill_switch ? "bad" : "good"} /><MetricRow label="Orders today" value={`${execution?.orders_today ?? 0} / ${execution?.max_orders_per_day ?? 0}`} /><div className="rounded-lg border border-border bg-muted/20 p-3 text-xs leading-5 text-muted-foreground">Execution stays behind an explicit gateway with order caps, reconciliation and an operator kill switch.</div></CardContent></Card>
    </div>
    <div className="grid gap-4 lg:grid-cols-2"><Card><CardHeader><CardTitle>Recent trades</CardTitle><CardDescription>Latest account activity.</CardDescription></CardHeader><CardContent><TradesTable rows={trades.slice(0,6)} /></CardContent></Card><Card><CardHeader><CardTitle>Research signal</CardTitle><CardDescription>What the current research process says.</CardDescription></CardHeader><CardContent className="space-y-4"><MetricRow label="Benchmark" value={pct(analytics?.benchmark_return_pct)} /><MetricRow label="Excess return" value={pct(analytics?.excess_return_pct)} /><MetricRow label="Win rate" value={analytics?.win_rate_pct != null ? `${analytics.win_rate_pct.toFixed(1)}%` : "—"} /><MetricRow label="Score" value={n(analytics?.score)} /><div className="flex items-center gap-2 text-xs text-muted-foreground"><CircleAlert className="size-4" /> Never treat a single backtest as proof of future performance.</div></CardContent></Card></div>
  </div>
}

const modeLabel = (m?: string) => m ? m[0].toUpperCase() + m.slice(1) : "Unknown"
function MetricRow({ label, value, tone="muted" }: { label:string; value:string; tone?:string }) { return <div className="flex items-center justify-between gap-4 border-b border-border/70 pb-3 text-sm last:border-0 last:pb-0"><span className="text-muted-foreground">{label}</span><span className={tone === "good" ? "text-emerald-300" : tone === "bad" ? "text-rose-300" : "font-medium"}>{value}</span></div> }
function TradesTable({ rows }: { rows:any[] }) { if (!rows.length) return <div className="py-8 text-center text-sm text-muted-foreground">No trades yet.</div>; return <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-xs text-muted-foreground"><th className="pb-3">Side</th><th className="pb-3">Price</th><th className="pb-3">Quantity</th><th className="pb-3">P&L</th><th className="pb-3">Reason</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i} className="border-t border-border/60"><td className="py-3"><span className={r.side === "BUY" ? "text-emerald-300" : "text-rose-300"}>{r.side}</span></td><td>{n(r.price,2)}</td><td>{n(r.quantity,5)}</td><td>{n(r.pnl,2)}</td><td className="max-w-[220px] truncate text-muted-foreground">{r.reason}</td></tr>)}</tbody></table></div> }

function Research({ reports, analytics, onResearch, onBacktest }: any) { return <div className="space-y-6"><PageIntro icon={FlaskConical} title="Research" subtitle="Improve strategy quality before you improve exposure." actions={<><Button variant="outline" onClick={onBacktest}><ChartNoAxesCombined className="size-4" /> Backtest</Button><Button onClick={onResearch}><Sparkles className="size-4" /> Full research</Button></>} /><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Stat label="Return" value={pct(analytics?.return_pct)} /><Stat label="Benchmark" value={pct(analytics?.benchmark_return_pct)} /><Stat label="Excess return" value={pct(analytics?.excess_return_pct)} /><Stat label="Drawdown" value={pct(analytics?.max_drawdown_pct)} /></div><Card><CardHeader><CardTitle>Research reports</CardTitle><CardDescription>Persisted decisions, not screenshots.</CardDescription></CardHeader><CardContent className="space-y-3">{reports.length ? reports.slice(0,8).map((r:any,i:number)=><div key={i} className="rounded-lg border border-border bg-muted/10 p-4"><div className="flex items-center justify-between gap-3"><div><div className="text-sm font-medium">{r.kind}</div><div className="text-xs text-muted-foreground">{r.symbol} · {r.timeframe} · {r.created_at}</div></div><Badge variant="outline">persisted</Badge></div><pre className="mt-3 max-h-52 overflow-auto rounded-md bg-black/10 p-3 text-xs text-muted-foreground">{r.report}</pre></div>) : <Empty text="Run full research to populate this workspace." />}</CardContent></Card></div> }
function Portfolio({ paper, trades, mode }: any) { return <div className="space-y-6"><PageIntro icon={Wallet} title="Portfolio" subtitle="Account state, exposure and recent execution." /><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Stat label="Equity" value={n(paper.equity)} /><Stat label="Cash" value={n(paper.cash)} /><Stat label="Asset" value={n(paper.asset,6)} /><Stat label="Realized P&L" value={n(paper.realized_pnl)} /></div><div className="grid gap-4 lg:grid-cols-2"><Card><CardHeader><CardTitle>Account posture</CardTitle><CardDescription>{modeLabel(mode)} mode</CardDescription></CardHeader><CardContent className="space-y-4"><MetricRow label="High watermark" value={n(paper.high_watermark)} /><MetricRow label="Average entry" value={n(paper.average_entry_price,2)} /><MetricRow label="Last price" value={n(paper.last_price,2)} /><MetricRow label="Drawdown" value={pct(paper.drawdown)} /></CardContent></Card><Card><CardHeader><CardTitle>Latest trades</CardTitle></CardHeader><CardContent><TradesTable rows={trades.slice(0,10)} /></CardContent></Card></div></div> }
function Execution({ mode, execution, apiKey, setApiKey, loading, onPreflight, onArm, onDisarm, onKill, onReconcile }: any) { return <div className="space-y-6"><PageIntro icon={Zap} title="Execution" subtitle="The last mile. Isolated, visible and deliberately harder to operate." actions={<Badge variant={mode === "live" ? "danger" : mode === "sandbox" ? "warning" : "success"}>{modeLabel(mode)} mode</Badge>} /><Card><CardHeader><CardTitle>Operator controls</CardTitle><CardDescription>Preflight first. Arm only when the target account is correct.</CardDescription></CardHeader><CardContent className="space-y-4"><div className="flex flex-col gap-3 sm:flex-row"><input type="password" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="Production API key" className="h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm outline-none" /><Button variant="outline" onClick={onPreflight} disabled={loading}><ShieldCheck className="size-4" /> Preflight</Button><Button variant="outline" onClick={onReconcile} disabled={loading}><RefreshCw className="size-4" /> Reconcile</Button><Button variant="outline" onClick={onArm} disabled={loading}><LockKeyhole className="size-4" /> Arm</Button><Button variant="outline" onClick={onDisarm} disabled={loading}>Disarm</Button><Button variant="destructive" onClick={onKill} disabled={loading}>Kill switch</Button></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Stat label="Armed" value={execution?.armed ? "Yes" : "No"} /><Stat label="Kill switch" value={execution?.kill_switch ? "Active" : "Clear"} /><Stat label="Orders today" value={`${execution?.orders_today ?? 0}`} /><Stat label="Order cap" value={n(execution?.max_order_notional)} /></div></CardContent></Card><Card><CardHeader><CardTitle>Execution principle</CardTitle></CardHeader><CardContent className="text-sm leading-6 text-muted-foreground">The strategy cannot bypass this gateway. Every order passes through mode checks, arming state, kill-switch state, order limits and exchange validation before submission. Reconciliation then brings the local state back in line with exchange truth.</CardContent></Card></div> }
function ActivityPage({ trades, reports }: any) { return <div className="space-y-6"><PageIntro icon={Activity} title="Activity" subtitle="The paper trail for decisions, experiments and trades." /><div className="grid gap-4 lg:grid-cols-2"><Card><CardHeader><CardTitle>Trades</CardTitle></CardHeader><CardContent><TradesTable rows={trades.slice(0,20)} /></CardContent></Card><Card><CardHeader><CardTitle>Research events</CardTitle></CardHeader><CardContent className="space-y-3">{reports.slice(0,15).map((r:any,i:number)=><div key={i} className="flex items-start gap-3 border-b border-border/60 pb-3 last:border-0"><div className="mt-1 rounded-full bg-primary/10 p-1.5"><FlaskConical className="size-3 text-primary" /></div><div><div className="text-sm font-medium">{r.kind}</div><div className="text-xs text-muted-foreground">{r.symbol} · {r.created_at}</div></div></div>)}</CardContent></Card></div></div> }
function RiskPage({ status, execution }: any) { const paper=status?.paper||{}; return <div className="space-y-6"><PageIntro icon={ShieldCheck} title="Risk & Safety" subtitle="The rules that should make the system boring when markets are not." /><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Stat label="Drawdown" value={pct(paper.drawdown)} /><Stat label="Daily loss" value={pct(paper.daily_loss)} /><Stat label="Kill switch" value={execution?.kill_switch ? "Active" : "Clear"} /><Stat label="Armed" value={execution?.armed ? "Yes" : "No"} /></div><Card><CardHeader><CardTitle>Safeguards</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-2">{["Position sizing cap","Daily loss limit","Max drawdown limit","Stop-loss / take-profit","Order notional cap","Orders-per-day cap","Explicit arming","Emergency kill switch","Exchange precision validation","Persistent reconciliation"].map(x=><div key={x} className="flex items-center gap-3 rounded-lg border border-border bg-muted/10 p-3 text-sm"><ShieldCheck className="size-4 text-emerald-300" />{x}</div>)}</CardContent></Card></div> }
function SettingsPage({ symbol, timeframe, setSymbol, setTimeframe, apiKey, setApiKey }: any) { return <div className="space-y-6"><PageIntro icon={SlidersHorizontal} title="Settings" subtitle="Customer-facing controls stay simple; advanced secrets remain server-side." /><Card><CardHeader><CardTitle>Workspace defaults</CardTitle><CardDescription>These affect research queries and the dashboard.</CardDescription></CardHeader><CardContent className="grid gap-4 sm:grid-cols-3"><Field label="Default symbol"><input className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm" value={symbol} onChange={e=>setSymbol(e.target.value)} /></Field><Field label="Timeframe"><select className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm" value={timeframe} onChange={e=>setTimeframe(e.target.value)}><option>15m</option><option>30m</option><option>1h</option><option>4h</option></select></Field><Field label="Application API key"><input type="password" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm" value={apiKey} onChange={e=>{setApiKey(e.target.value);localStorage.setItem("the-trader-api-key",e.target.value)}} /></Field></CardContent></Card><Card><CardHeader><CardTitle>Design language</CardTitle></CardHeader><CardContent className="text-sm leading-6 text-muted-foreground">The product uses local shadcn/ui primitives, restrained neutral surfaces, a single indigo action color, and semantic green/red only when financial state requires it.</CardContent></Card></div> }
function PageIntro({ icon:Icon, title, subtitle, actions }: any) { return <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><div className="mb-3 grid size-9 place-items-center rounded-lg border border-border bg-muted/20"><Icon className="size-4 text-muted-foreground" /></div><h1 className="text-2xl font-semibold tracking-tight">{title}</h1><p className="mt-1 text-sm text-muted-foreground">{subtitle}</p></div><div>{actions}</div></section> }
function Stat({ label, value }: { label:string; value:string }) { return <Card><CardContent className="p-4"><div className="text-xs text-muted-foreground">{label}</div><div className="mt-2 text-2xl font-semibold tracking-tight">{value}</div></CardContent></Card> }
function Field({ label, children }: { label:string; children:React.ReactNode }) { return <label className="space-y-2 text-sm"><div className="text-xs text-muted-foreground">{label}</div>{children}</label> }
function Empty({ text }: { text:string }) { return <div className="py-12 text-center text-sm text-muted-foreground">{text}</div> }

export default App
