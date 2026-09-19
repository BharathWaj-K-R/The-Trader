import { useState } from "react"
import { AlertTriangle, Check, KeyRound, RefreshCw, Shield, Siren } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { KeyValue, PageHeader, SectionCard, EmptyState } from "@/components/page-primitives"
import type { ApiConfig, ExecutionState, RuntimeStatus } from "@/lib/types"

export function ExecutionPage({ status, config, apiKey, setApiKey, busy, onPreflight, onArm, onDisarm, onKill, onReconcile }:{
 status:RuntimeStatus|null; config:ApiConfig|null; apiKey:string; setApiKey:(v:string)=>void; busy:boolean; onPreflight:()=>void; onArm:()=>void; onDisarm:()=>void; onKill:()=>void; onReconcile:()=>void
}){
 const e=status?.execution
 const live=e?.mode==="live"
 const [showKey,setShowKey]=useState(false)
 return <div>
  <PageHeader eyebrow="Execution" title="Control execution deliberately." description="Research decides. Risk validates. This surface decides whether anything may reach the exchange." />
  <Card className="mb-4 border-border bg-card"><CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between"><div><div className="text-xs text-muted-foreground">Current environment</div><div className="mt-1 text-2xl font-semibold tracking-tight">{(status?.mode??"paper").toUpperCase()}</div><div className="mt-1 text-sm text-muted-foreground">{status?.environment??"unknown"} · {e?.exchange??config?.exchange_id??"exchange unavailable"}</div></div><Badge variant="outline">{e?.armed?"ARMED":"DISARMED"}</Badge></CardContent></Card>
  <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
   <SectionCard title="Preflight" description="Validate connection and execution prerequisites before acting."><div className="space-y-1"><KeyValue label="Connected" value={e?.connected?"Yes":"No / unknown"}/><KeyValue label="Kill switch" value={e?.kill_switch?"Active":"Clear"}/><KeyValue label="Orders today" value={`${e?.orders_today??0} / ${e?.max_orders_per_day??config?.max_live_orders_per_day??"—"}`}/><KeyValue label="Last reconcile" value={e?.last_reconcile?new Date(e.last_reconcile).toLocaleString():"Not available"}/></div><Button className="mt-4" variant="outline" onClick={onPreflight} disabled={busy}><Check className="size-4"/>Run preflight</Button></SectionCard>
   <SectionCard title="Operator controls" description="Consequential controls are intentionally separated from research actions."><div className="grid gap-2 sm:grid-cols-2"><Button variant="outline" onClick={onArm} disabled={busy || !!e?.kill_switch}><Shield className="size-4"/>Arm</Button><Button variant="outline" onClick={onDisarm} disabled={busy}><RefreshCw className="size-4"/>Disarm</Button><Button variant="outline" onClick={onReconcile} disabled={busy}><RefreshCw className="size-4"/>Reconcile</Button><Button variant="destructive" onClick={onKill} disabled={busy}><Siren className="size-4"/>Kill switch</Button></div>{live&&<div className="mt-4 rounded-md border border-border bg-secondary/30 p-3 text-xs leading-5 text-muted-foreground">Live mode is enabled for the server. Orders should only be submitted after successful preflight and deliberate operator arming.</div>}</SectionCard>
  </div>
  <Card className="mt-4"><CardHeader><CardTitle className="text-sm">Application access</CardTitle></CardHeader><CardContent><div className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><KeyRound className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground"/><input value={apiKey} onChange={e=>setApiKey(e.target.value)} type={showKey?"text":"password"} placeholder="X-API-Key" className="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm"/></div><Button variant="outline" onClick={()=>setShowKey(v=>!v)}>{showKey?"Hide":"Show"}</Button></div><p className="mt-3 text-xs text-muted-foreground">The application API key is client access, not an exchange secret. Exchange credentials remain server-side.</p></CardContent></Card>
  <div className="mt-4"><EmptyState title="Manual order ticket is intentionally not implicit" description="Use the backend execution contract and risk/preflight gates before adding a money-moving ticket to the customer UI."/></div>
 </div>
}
