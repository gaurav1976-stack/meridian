"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/cn";
import type { ModuleRegistryEntry } from "@/lib/types";

const ICONS: Record<string, LucideIcon> = {
  LayoutDashboard,
  FolderKanban,
};

interface SidebarProps {
  modules: ModuleRegistryEntry[];
}

export function Sidebar({ modules }: SidebarProps) {
  const pathname = usePathname();

  // Always show at least Dashboard + Projects even if backend is offline
  const fallback: ModuleRegistryEntry[] = [
    { key: "dashboard", label: "Dashboard", icon: "LayoutDashboard", route: "/dashboard", is_enabled: true },
    { key: "projects",  label: "Projects",  icon: "FolderKanban",    route: "/projects",  is_enabled: true },
  ];
  const items = modules.length > 0 ? modules : fallback;

  return (
    <aside className="w-56 shrink-0 bg-meridian-900 text-white flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-meridian-700">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-accent-500 flex items-center justify-center text-white font-bold text-sm">
            M
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide leading-tight">Meridian</div>
            <div className="text-[10px] text-meridian-100/70 leading-tight">Airport PMO Suite</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {items.map((m) => {
          const Icon = ICONS[m.icon] ?? LayoutDashboard;
          const active = pathname?.startsWith(m.route);
          return (
            <Link
              key={m.key}
              href={m.route}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors",
                active
                  ? "bg-meridian-700 text-white font-medium"
                  : "text-meridian-100/75 hover:bg-meridian-700/50 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{m.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 text-[10px] text-meridian-100/50 border-t border-meridian-700">
        v0.1.0 · © GV Softwares
      </div>
    </aside>
  );
}
