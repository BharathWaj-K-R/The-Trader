import { Activity } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState, PageHeader } from "@/components/page-primitives"
import type { Experiment, ResearchReport, Trade } from "@/lib/types"

const nice=(v:string)=>v.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())

type Item={kind:string;title:string;detail:string;time:string}
export function ActivityPage({trades,experiments,reports}:{trades:Trade[];experiments:Experiment[];reports:ResearchReport[]}){
 const items:Item[]=[...trades.map(t=>({kind:"Trade",title:`${t.side} ${nice(t.reason)}`,detail:`${t.quantity.toFixed(6)} @ ${t.price.toFixed(2)}`,time:t.timestamp})),...experiments.map(e=>({kind:"Experiment",title:e.accepted?"Candidate accepted":"Candidate rejected",detail:e.reason,time:e.created_at??""})),...reports.map(r=>({kind:"Research",title:nice(r.kind),detail:`${r.symbol} · ${r.timeframe}`,time:r.created_at??""}))].sort((a,b)=>b.time.localeCompare(a.time))
 return <div><PageHeader eyebrow="Activity" title="A readable record of what happened." description="Trades, experiments and research runs collected into one operational timeline."/><Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Activity className="size-4"/>Timeline</CardTitle></CardHeader><CardContent>{items.length?<div className="divide-y divide-border">{items.slice(0,60).map((x,i)=><div key={`${x.kind}-${x.time}-${i}`} className="flex gap-3 py-4"><div className="mt-1 size-2 shrink-0 rounded-full bg-foreground/70"/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="text-sm font-medium">{x.title}</span><Badge variant="outline">{x.kind}</Badge></div><div className="mt-1 text-xs text-muted-foreground">{x.detail}</div></div><time className="shrink-0 text-xs text-muted-foreground">{x.time?new Date(x.time).toLocaleString():"—"}</time></div>)}</div>:<EmptyState title="No activity yet" description="Activity will appear as research and execution events are persisted."/>}</CardContent></Card></div>
}
