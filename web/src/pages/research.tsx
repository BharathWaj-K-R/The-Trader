import { BarChart3, FlaskConical, GitCompare, Play, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MetricCard, PageHeader, SectionCard, KeyValue, EmptyState } from "@/components/page-primitives"
import type { Analytics, Experiment, ResearchReport, RuntimeStatus } from "@/lib/types"

const pct=(v:unknown)=>typeof v==="number"?`${(v*100).toFixed(2)}%`:"—"
const nice=(v:string)=>v.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())

export function ResearchPage({ status, analytics, reports, experiments, busy, onBacktest, onWalk, onFull }: {
  status: RuntimeStatus|null; analytics: Analytics|null; reports: ResearchReport[]; experiments: Experiment[]; busy:boolean
  onBacktest:()=>void; onWalk:()=>void; onFull:()=>void
}) {
  return <div>
    <PageHeader eyebrow="Research" title="Test ideas before trusting them." description="Backtest, improve, validate out of sample, stress execution costs, and keep an auditable experiment trail." actions={<><Button variant="outline" onClick={onBacktest} disabled={busy}><Play className="size-4"/>Backtest</Button><Button variant="outline" onClick={onWalk} disabled={busy}><GitCompare className="size-4"/>Walk-forward</Button><Button onClick={onFull} disabled={busy}><FlaskConical className="size-4"/>Full research</Button></>} />
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <MetricCard label="Return" value={pct(analytics?.return_pct)} detail="Latest strategy result"/>
      <MetricCard label="Benchmark" value={pct(analytics?.benchmark_return_pct)} detail="Buy-and-hold result"/>
      <MetricCard label="Excess" value={pct(analytics?.excess_return_pct)} detail="Strategy minus benchmark"/>
      <MetricCard label="Drawdown" value={pct(analytics?.max_drawdown_pct)} detail="Peak-to-trough"/>
      <MetricCard label="Score" value={typeof analytics?.score==="number"?analytics.score.toFixed(2):"—"} detail="Promotion score"/>
    </div>
    <div className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
      <SectionCard title="Current strategy" description="The strategy version currently active in the runtime.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Param name="Fast SMA" value={String(status?.strategy.fast_window ?? "—")}/><Param name="Slow SMA" value={String(status?.strategy.slow_window ?? "—")}/><Param name="RSI entry" value={String(status?.strategy.rsi_entry ?? "—")}/><Param name="RSI exit" value={String(status?.strategy.rsi_exit ?? "—")}/></div>
      </SectionCard>
      <SectionCard title="Research posture" description="What the latest evidence says.">
        <div className="space-y-1"><KeyValue label="Reports" value={String(reports.length)}/><KeyValue label="Experiments" value={String(experiments.length)}/><KeyValue label="Latest report" value={reports[0]?nice(reports[0].kind):"Not available"}/><KeyValue label="Evidence" value={analytics?"Available":"Needs research"}/></div>
      </SectionCard>
    </div>
    <div className="mt-4 grid gap-4 xl:grid-cols-2">
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><BarChart3 className="size-4"/>Experiment ledger</CardTitle></CardHeader><CardContent>{experiments.length?<div className="divide-y divide-border">{experiments.slice(0,10).map((e,i)=><div key={String(e.id??i)} className="flex items-center justify-between gap-4 py-3"><div><div className="text-sm font-medium">{e.accepted?"Candidate accepted":"Candidate rejected"}</div><div className="mt-1 text-xs text-muted-foreground">{e.reason}</div></div><div className="text-right"><Badge variant="outline">{e.candidate_score.toFixed(2)}</Badge><div className="mt-1 text-[11px] text-muted-foreground">from {e.baseline_score.toFixed(2)}</div></div></div>)}</div>:<EmptyState title="No experiments" description="Run self-improvement to create the first controlled experiment."/>}</CardContent></Card>
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><ShieldCheck className="size-4"/>Research standard</CardTitle></CardHeader><CardContent className="space-y-1"><KeyValue label="In-sample" value="Backtested"/><KeyValue label="Out-of-sample" value="Walk-forward gate"/><KeyValue label="Execution costs" value="Stress tested"/><KeyValue label="Benchmark" value="Included"/></CardContent></Card>
    </div>
  </div>
}
function Param({name,value}:{name:string;value:string}){return <div className="rounded-md border border-border bg-secondary/30 p-3"><div className="text-[11px] text-muted-foreground">{name}</div><div className="mt-1 font-mono text-sm">{value}</div></div>}
