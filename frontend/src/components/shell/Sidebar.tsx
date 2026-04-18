"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Banknote,
  CalendarClock,
  FileText,
  FolderKanban,
  GitBranch,
  LayoutDashboard,
  PlaneTakeoff,
  Ruler,
  Search,
  Settings2,
  ShieldAlert,
  Users,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/cn";
import type { ModuleRegistryEntry } from "@/lib/types";

// Map the backend-supplied icon string to a real Lucide component. Keeping the
// map here (vs. on the server) means the backend registry stays JSON-only.
const ICONS: Record<string, LucideIcon> = {
  LayoutDashboard,
  FolderKanban,
  Settings2,
  CalendarClock,
  ShieldAlert,
  GitBranch,
  Banknote,
  Ruler,
  FileText,
  Users,
  PlaneTakeoff,
  BarChart3,
  Search,
};

interface SidebarProps {
  modules: ModuleRegistryEntry[];
}

export function Sidebar({ modules }: SidebarProps) {
  const pathname = usePathname();
  return (
    <aside className="w-64 shrink-0 bg-meridian-900 text-white flex flex-col">
      <div className="px-5 py-5 border-b border-meridian-700">
        <div className="text-lg font-semibold tracking-wide">Meridian</div>
        <div className="text-xs text-meridian-100/80 mt-1">
          Airport Programme PMIS
        </div>
      </div>
      <nav className="flex-1 py-3">
        {modules.map((m) => {
          const Icon = ICONS[m.icon] ?? LayoutDashboard;
          const active = pathname?.startsWith(m.route);
          const classes = cn(
            "flex items-center gap-3 px-5 py-2.5 text-sm",
            active
              ? "bg-meridian-700 text-white"
              : "text-meridian-100/80 hover:bg-meridian-700/60 hover:text-white",
            !m.is_enabled && "opacity-40 cursor-not-allowed"
          );
          if (!m.is_enabled) {
            return (
              <div key={m.key} className={classes} title="Module pending port">
                <Icon className="w-4 h-4" />
                <span>{m.label}</span>
              </div>
            );
          }
          return (
            <Link key={m.key} href={m.route} className={classes}>
              <Icon className="w-4 h-4" />
              <span>{m.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-3 text-[11px] text-meridian-100/60 border-t border-meridian-700">
        v0.1.0 • dev
      </div>
    </aside>
  );
}
