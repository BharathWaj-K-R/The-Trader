import { ArrowDownRight, ArrowUpRight, Wallet } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MetricCard, PageHeader, SectionCard, KeyValue, EmptyState } from "@/components/page-primitives"
import type { MarketBar, RuntimeStatus, Trade } from "@/lib/types"

const money=(v:unknown)=>typeof v==="number"&&Number.isFinite(v)?`$${v.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`:"—"
const pct=(v:unknown)=>typeof v==="number"&&Number.isFinite(v)?`${(v*100).toFixed(2)}%`:"—"

export function PortfolioPage({status,trades,bars}:{status:RuntimeStatus|null;trades:Trade[];bars:MarketBar[]}){
 const a=status?.paper
 return <div>
  <PageHeader eyebrow="Portfolio" title="Know exactly where the account stands." description="Persistent balances, exposure, cost basis and trade history, without making you hunt for the numbers." />
  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
   <MetricCard label="Equity" value={money(a?.equity)} detail="Current marked value"/><MetricCard label="Cash" value={money(a?.cash)} detail="Available cash"/><MetricCard label="Asset" value={typeof a?.asset==="number"?a.asset.toFixed(6):"—"} detail="Base-asset quantity"/><MetricCard label="Realized P&L" value={money(a?.realized_pnl)} detail="Closed trades"/><MetricCard label="Drawdown" value={pct(a?.drawdown_pct)} detail="From high watermark"/>
  </div>
  <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
   <SectionCard title="Position" description="Current position and accounting state."><div className="space-y-1"><KeyValue label="Last price" value={money(a?.last_price)}/><KeyValue label="Average entry" value={money(a?.average_entry_price)}/><KeyValue label="Unrealized P&L" value={money(a?.unrealized_pnl)}/><KeyValue label="Holding bars" value={String(a?.holding_bars??0)}/><KeyValue label="Trading state" value={a?.trading_halted?"Halted":"Running"}/></div></SectionCard>
   <SectionCard title="Market snapshot" description="Latest validated bars used by the product.">{bars.length?<div className="space-y-1">{bars.slice(-6).reverse().map(b=><div key={b.time} className="flex items-center justify-between border-b border-border/70 py-2 last:border-0"><span className="text-xs text-muted-foreground">{new Date(b.time).toLocaleTimeString()}</span><span className="font-mono text-sm">{b.close.toFixed(2)}</span></div>)}</div>:<EmptyState title="No market data" description="Start the backend and refresh."/>}</SectionCard>
  </div>
  <div className="mt-4"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Wallet className="size-4"/>Transactions</CardTitle></CardHeader><CardContent>{trades.length?<div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b border-border text-xs text-muted-foreground"><th className="px-2 py-2 text-left font-medium">Time</th><th className="px-2 py-2 text-left font-medium">Side</th><th className="px-2 py-2 text-right font-medium">Price</th><th className="px-2 py-2 text-right font-medium">Quantity</th><th className="px-2 py-2 text-right font-medium">Fee</th><th className="px-2 py-2 text-right font-medium">P&L</th></tr></thead><tbody className="divide-y divide-border">{trades.slice(0,20).map((t,i)=><tr key={String(t.id??i)}><td className="px-2 py-2 text-muted-foreground">{new Date(t.timestamp).toLocaleString()}</td><td className="px-2 py-2"><span className="inline-flex items-center gap-1">{t.side==="BUY"?<ArrowUpRight className="size-3"/>:<ArrowDownRight className="size-3"/>}{t.side}</span></td><td className="px-2 py-2 text-right font-mono">{t.price.toFixed(2)}</td><td className="px-2 py-2 text-right font-mono">{t.quantity.toFixed(6)}</td><td className="px-2 py-2 text-right font-mono">{t.fee.toFixed(2)}</td><td className="px-2 py-2 text-right font-mono">{money(t.pnl)}</td></tr>)}</tbody></table></div>:<EmptyState title="No transactions" description="Trades will appear here when the account executes."/>}</CardContent></Card></div>
 </div>
}
