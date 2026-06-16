import { NavLink } from "react-router-dom";
import { Languages, BookText, Inbox, History, LayoutDashboard, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Playground", icon: Languages, end: true },
  { to: "/termbase", label: "Termbase", icon: BookText },
  { to: "/review", label: "Review Queue", icon: Inbox },
  { to: "/corrections", label: "Corrections", icon: History },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin", label: "Profile Admin", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-line bg-surface flex flex-col">
      <div className="h-14 flex items-center px-4 border-b border-line">
        <span className="font-mono font-semibold text-primary">ZH→VI</span>
        <span className="ml-2 text-sm text-muted">Translate · QC</span>
      </div>
      <nav className="p-2 flex flex-col gap-1">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive ? "bg-primary/10 text-primary font-medium" : "text-ink hover:bg-bg",
              )
            }
          >
            <Icon size={18} aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
