import type { LucideIcon } from "lucide-react"
import { Activity, FlaskConical, LayoutDashboard, Settings, Shield, Wallet, Zap } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { RuntimeStatus } from "@/lib/types"

export type RouteId = "overview" | "research" | "portfolio" | "execution" | "activity" | "risk" | "settings"

type NavItem = { id: RouteId; label: string; icon: LucideIcon; group: string }

const nav: NavItem[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, group: "Workspace" },
  { id: "research", label: "Research", icon: FlaskConical, group: "Workspace" },
  { id: "portfolio", label: "Portfolio", icon: Wallet, group: "Workspace" },
  { id: "execution", label: "Execution", icon: Zap, group: "Workspace" },
  { id: "activity", label: "Activity", icon: Activity, group: "Workspace" },
  { id: "risk", label: "Risk & Safety", icon: Shield, group: "Control" },
  { id: "settings", label: "Settings", icon: Settings, group: "Control" },
]

export function AppShell({ route, status, notice, busy, onNavigate, onRefresh, children }: {
  route: RouteId
  status: RuntimeStatus | null
  notice: string
  busy: boolean
  onNavigate: (route: RouteId) => void
  onRefresh: () => void
  children: React.ReactNode
}) {
  const current = nav.find((item) => item.id === route)?.label ?? "Overview"

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-8 items-center justify-center rounded-md border border-border bg-secondary text-foreground">
              <TrendingGlyph />
            </div>
            <button onClick={() => onNavigate("overview")} className="text-left">
              <div className="text-sm font-semibold tracking-tight">The-Trader</div>
              <div className="text-[11px] text-muted-foreground">{current}</div>
            </button>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{(status?.mode ?? "paper").toUpperCase()}</Badge>
            <span className="hidden max-w-[260px] truncate rounded-md border border-border bg-secondary/40 px-3 py-1.5 text-xs text-muted-foreground md:block">{notice}</span>
            <Button size="icon" variant="ghost" onClick={onRefresh} disabled={busy} aria-label="Refresh data">
              <span className={busy ? "animate-spin" : ""}>↻</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px]">
        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-56 shrink-0 border-r border-border/70 p-4 lg:block">
          <nav className="space-y-6">
            {(["Workspace", "Control"] as const).map((group) => (
              <div key={group}>
                <div className="mb-2 px-2 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">{group}</div>
                <div className="space-y-1">
                  {nav.filter((item) => item.group === group).map((item) => {
                    const Icon = item.icon
                    const active = item.id === route
                    return (
                      <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}
                      >
                        <Icon className="size-4" />
                        <span>{item.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  )
}

function TrendingGlyph() {
  return <span className="text-sm font-semibold">T</span>
}
