import { Activity, BarChart3, Bot, CircleDollarSign, FlaskConical, Gauge, Settings2, ShieldCheck, Wallet } from "lucide-react"
import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarHeader, SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar"

const primary = [
  ["Overview", Gauge], ["Research", FlaskConical], ["Portfolio", Wallet], ["Execution", CircleDollarSign], ["Activity", Activity],
] as const

export function AppSidebar({ page, onPage }: { page: string; onPage: (page: string) => void }) {
  const { collapsed } = useSidebar()
  return <Sidebar>
    <SidebarHeader>
      <div className="flex items-center gap-3 px-1 py-1">
        <div className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground"><Bot className="size-4" /></div>
        {!collapsed && <div><div className="text-sm font-semibold tracking-tight">The-Trader</div><div className="text-[10px] text-muted-foreground">Trading intelligence</div></div>}
      </div>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>Workspace</SidebarGroupLabel>
        <SidebarMenu>{primary.map(([label, Icon]) => <SidebarMenuItem key={label}><SidebarMenuButton active={page === label} icon={<Icon className="size-4" />} onClick={() => onPage(label)}>{label}</SidebarMenuButton></SidebarMenuItem>)}</SidebarMenu>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel>Controls</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem><SidebarMenuButton active={page === "Risk & Safety"} icon={<ShieldCheck className="size-4" />} onClick={() => onPage("Risk & Safety")}>Risk & Safety</SidebarMenuButton></SidebarMenuItem>
          <SidebarMenuItem><SidebarMenuButton active={page === "Settings"} icon={<Settings2 className="size-4" />} onClick={() => onPage("Settings")}>Settings</SidebarMenuButton></SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      {!collapsed && <div className="rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground"><div className="font-medium text-foreground">Operator mode</div><div className="mt-1">Paper, sandbox and live are isolated at the execution boundary.</div></div>}
    </SidebarFooter>
  </Sidebar>
}
