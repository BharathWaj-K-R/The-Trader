import { BrainCircuit, FlaskConical, ShieldCheck, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState, KeyValue, MetricCard, PageHeader, SectionCard } from "@/components/page-primitives"
import type { AIStrategyLabResult } from "@/lib/types"

const pct = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : "—"
const num = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "—"

export function AILabPage({ result, enabled, busy, onRun }: { result: AIStrategyLabResult | null; enabled: boolean; busy: boolean; onRun: () => void }) {
  const analysis = result?.analysis
  const proposal = result?.proposal
  const critic = result?.critic
  const baseline = result?.baseline?.analytics
  const candidate = result?.candidate?.analytics
  return <div>
    <PageHeader eyebrow="AI Strategy Lab" title="Let Grok research. Let the gates decide." description="Grok analyzes the evidence and proposes one bounded strategy change. The deterministic backtest, walk-forward, cost-stress and critic gates decide whether it can become active." actions={<Button onClick={onRun} disabled={busy || !enabled}><BrainCircuit className="size-4" />{busy ? "Running lab…" : "Run evolution cycle"}</Button>} />
    {!enabled ? <Card className="mb-4"><CardContent className="flex items-center gap-3 p-5"><ShieldCheck className="size-5 text-muted-foreground"/><div><div className="text-sm font-medium">Grok is not enabled</div><div className="text-xs text-muted-foreground">Set AI_ENABLED=true and XAI_API_KEY on the backend. The key never belongs in the browser.</div></div></CardContent></Card> : null}
    {result ? <>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Baseline return" value={pct(baseline?.return_pct)} detail="Current strategy" />
        <MetricCard label="Candidate return" value={pct(candidate?.return_pct)} detail="AI proposed strategy" />
        <MetricCard label="Excess" value={pct(candidate?.excess_return_pct)} detail="Vs benchmark" />
        <MetricCard label="Candidate drawdown" value={pct(candidate?.max_drawdown_pct)} detail="Peak-to-trough" />
        <MetricCard label="Promotion" value={result.promotion.promoted ? "PROMOTED" : "BLOCKED"} detail={result.promotion.reason} />
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <SectionCard title="Grok assessment" description="Evidence-backed diagnosis of the current strategy.">
          <div className="space-y-3"><div className="flex items-center gap-2"><Badge variant="outline">{analysis?.verdict ?? "—"}</Badge><Badge variant="outline">{analysis?.market_regime ?? "—"}</Badge><span className="text-xs text-muted-foreground">confidence {num(analysis?.confidence)}</span></div><KeyValue label="Strengths" value={analysis?.strengths?.join(" · ") || "—"}/><KeyValue label="Weaknesses" value={analysis?.weaknesses?.join(" · ") || "—"}/><KeyValue label="Next experiments" value={analysis?.next_experiments?.join(" · ") || "—"}/></div>
        </SectionCard>
        <SectionCard title="Proposed change" description="Exactly one bounded parameter experiment is generated per cycle.">
          {proposal ? <div className="grid gap-3 sm:grid-cols-2"><KeyValue label="Hypothesis" value={proposal.hypothesis}/><KeyValue label="Rationale" value={proposal.rationale}/><KeyValue label="Fast SMA" value={String(proposal.fast_window)}/><KeyValue label="Slow SMA" value={String(proposal.slow_window)}/><KeyValue label="RSI window" value={String(proposal.rsi_window)}/><KeyValue label="RSI entry / exit" value={`${proposal.rsi_entry} / ${proposal.rsi_exit}`}/></div> : <EmptyState title="No proposal" description="Run the AI lab to generate a bounded candidate."/>}
        </SectionCard>
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><FlaskConical className="size-4"/>Validation evidence</CardTitle></CardHeader><CardContent className="grid gap-2"><KeyValue label="Walk-forward" value={result.walk_forward.robust ? "Robust" : "Not robust"}/><KeyValue label="Positive folds" value={`${String(result.walk_forward.positive_folds ?? "—")} / ${String(result.walk_forward.folds_evaluated ?? "—")}`}/><KeyValue label="Cost stress" value={`${String(result.cost_stress.robust_scenarios ?? "—")} / ${String(result.cost_stress.scenarios ?? "—")} robust`}/><KeyValue label="Deterministic gate" value={result.promotion.deterministic_gate ? "Passed" : "Failed"}/></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Sparkles className="size-4"/>Adversarial critic</CardTitle></CardHeader><CardContent className="space-y-3"><div className="flex items-center gap-2"><Badge variant="outline">{critic?.verdict ?? "—"}</Badge><span className="text-xs text-muted-foreground">confidence {num(critic?.confidence)}</span></div><KeyValue label="Concerns" value={critic?.concerns?.join(" · ") || "—"}/><KeyValue label="Recommendation" value={critic?.recommendation || "—"}/></CardContent></Card>
      </div>
    </> : <Card><CardContent className="p-8"><EmptyState title="No AI research run yet" description="Run an evolution cycle after configuring Grok. The lab will never send orders to the exchange." /></CardContent></Card>}
  </div>
}
