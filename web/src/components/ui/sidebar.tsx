import * as React from "react"
import { cn } from "@/lib/utils"

const SidebarContext = React.createContext<{ collapsed: boolean; toggle: () => void }>({ collapsed: false, toggle: () => {} })
export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = React.useState(false)
  const value = React.useMemo(() => ({ collapsed, toggle: () => setCollapsed(v => !v) }), [collapsed])
  return <SidebarContext.Provider value={value}><div className="min-h-svh">{children}</div></SidebarContext.Provider>
}
export function useSidebar() { return React.useContext(SidebarContext) }
export function Sidebar({ children }: { children: React.ReactNode }) { const { collapsed } = useSidebar(); return <aside className={cn("fixed inset-y-0 left-0 z-40 hidden border-r border-border bg-sidebar transition-[width] duration-200 lg:flex lg:flex-col", collapsed ? "w-[68px]" : "w-[228px]")}>{children}</aside> }
export function SidebarHeader({ children }: { children: React.ReactNode }) { return <div className="border-b border-border p-3">{children}</div> }
export function SidebarContent({ children }: { children: React.ReactNode }) { return <div className="flex-1 overflow-y-auto p-2">{children}</div> }
export function SidebarFooter({ children }: { children: React.ReactNode }) { return <div className="border-t border-border p-2">{children}</div> }
export function SidebarMenu({ children }: { children: React.ReactNode }) { return <nav className="space-y-1">{children}</nav> }
export function SidebarMenuItem({ children }: { children: React.ReactNode }) { return <div>{children}</div> }
export function SidebarMenuButton({ active, icon, children, onClick }: { active?: boolean; icon?: React.ReactNode; children?: React.ReactNode; onClick?: () => void }) { const { collapsed } = useSidebar(); return <button onClick={onClick} className={cn("flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground", active && "bg-accent text-foreground", collapsed && "justify-center px-2")}>{icon}<span className={cn(collapsed && "hidden")}>{children}</span></button> }
export function SidebarGroup({ children }: { children: React.ReactNode }) { return <section className="mb-5">{children}</section> }
export function SidebarGroupLabel({ children }: { children: React.ReactNode }) { const { collapsed } = useSidebar(); return <div className={cn("px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/60", collapsed && "hidden")}>{children}</div> }
export function SidebarTrigger() { const { toggle } = useSidebar(); return <button onClick={toggle} className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground" aria-label="Toggle sidebar">☰</button> }
