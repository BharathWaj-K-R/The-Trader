import { Activity, FlaskConical, Shield, Wallet } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MetricCard, PageHeader, SectionCard, KeyValue, EmptyState } from "@/components/page-primitives"
import type { Analytics, MarketBar, ResearchReport, RuntimeStatus, Trade } from "@/lib/types"

const money = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? `$${v.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}` : "—"
const pct = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? `${(v*100).toFixed(2)}%` : "—"
const nice = (v: string) => v.replaceAll("_", " ").replace(/\b\w/g,c=>c.toUpperCase())

export function Overview({ status, analytics, bars, trades, report, onResearch, onPaper, busy, symbol, timeframe }: {
  status: RuntimeStatus | null; analytics: Analytics | null; bars: MarketBar[]; trades: Trade[]; report: Record<string, any> | null;
  onResearch: () => void; onPaper: () => void; busy: boolean; symbol: string; timeframe: string
}) {
  const account = status?.paper
  const latest = bars[bars.length - 1]
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="A clear view of the trading system."
        description="Portfolio, research quality, execution posture and market context in one calm workspace."
        actions={
          <>
            <Button variant="outline" onClick={onPaper} disabled={busy}>Paper tick</Button>
            <Button onClick={onResearch} disabled={busy}><FlaskConical className="size-4" />Run research</Button>
          </>
        }
      />
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Equity" value={money(account?.equity)} detail="Current account value" />
        <MetricCard label="Today's loss" value={pct(account?.daily_loss_pct)} detail="Risk budget consumed" />
        <MetricCard label="Drawdown" value={pct(account?.drawdown_pct)} detail="From high watermark" />
        <MetricCard label="Strategy return" value={pct(analytics?.return_pct)} detail={analytics ? `Benchmark ${pct(analytics.benchmark_return_pct)}` : "Latest research"} />
        <MetricCard label="Market" value={money(latest?.close)} detail={`${symbol} · ${timeframe}`} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <SectionCard title="Market context" description="Recent validated market observations.">
          {bars.length ? <MarketTable bars={bars} /> : <EmptyState title="No market data" description="Start the backend and refresh to load live market observations." />}
        </SectionCard>
        <SectionCard title="System posture" description="The controls that matter right now.">
          <div className="space-y-1">
            <KeyValue label="Mode" value={(status?.mode ?? "paper").toUpperCase()} />
            <KeyValue label="Environment" value={nice(status?.environment ?? "unknown")} />
            <KeyValue label="Execution" value={status?.execution?.armed ? "Armed" : "Disarmed"} />
            <KeyValue label="Kill switch" value={status?.execution?.kill_switch ? "Active" : "Clear"} />
            <KeyValue label="Trading halt" value={account?.trading_halted ? "Halted" : "Running"} />
          </div>
        </SectionCard>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Wallet className="size-4" />Portfolio</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            <KeyValue label="Cash" value={money(account?.cash)} />
            <KeyValue label="Asset" value={account ? account.asset.toFixed(6) : "—"} />
            <KeyValue label="Avg entry" value={money(account?.average_entry_price)} />
            <KeyValue label="Realized P&L" value={money(account?.realized_pnl)} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Shield className="size-4" />Research health</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            <KeyValue label="Latest run" value={report ? "Available" : "Not run"} />
            <KeyValue label="Score" value={typeof analytics?.score === "number" ? analytics.score.toFixed(2) : "—"} />
            <KeyValue label="Excess return" value={pct(analytics?.excess_return_pct)} />
            <KeyValue label="Trades" value={String(analytics?.trade_count ?? trades.length)} />
          </CardContent>
        </Card>
      </div>
      <div className="mt-4">
        <SectionCard title="Recent activity" description="Latest persisted trades from the account ledger.">
          {trades.length ? <div className="divide-y divide-border">{trades.slice(0,8).map((t)=><div key={String(t.id ?? t.timestamp)} className="flex items-center justify-between gap-4 py-3"><div className="flex items-center gap-3"><Activity className="size-4 text-muted-foreground"/><div><div className="text-sm font-medium">{t.side} {nice(t.reason)}</div><div className="text-xs text-muted-foreground">{new Date(t.timestamp).toLocaleString()}</div></div></div><div className="text-right"><div className="text-sm">{money(t.price)}</div><div className="text-xs text-muted-foreground">{t.quantity.toFixed(6)}</div></div></div>)}</div> : <EmptyState title="No trades yet" description="Paper activity will appear here after an execution tick." />}
        </SectionCard>
      </div>
    </div>
  )
}

function MarketTable({ bars }: { bars: MarketBar[] }) {
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs text-muted-foreground"><tr><th className="pb-2 font-medium">Time</th><th className="pb-2 text-right font-medium">Open</th><th className="pb-2 text-right font-medium">High</th><th className="pb-2 text-right font-medium">Low</th><th className="pb-2 text-right font-medium">Close</th></tr></thead><tbody className="divide-y divide-border">{bars.slice(-8).reverse().map(b=><tr key={b.time}><td className="py-2 text-muted-foreground">{new Date(b.time).toLocaleTimeString()}</td><td className="py-2 text-right">{b.open.toFixed(2)}</td><td className="py-2 text-right">{b.high.toFixed(2)}</td><td className="py-2 text-right">{b.low.toFixed(2)}</td><td className="py-2 text-right font-medium">{b.close.toFixed(2)}</td></tr>)}</tbody></table></div>
}
