"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Banknote,
  CalendarClock,
  FileText,
  GitBranch,
  LayoutDashboard,
  PlaneTakeoff,
  Ruler,
  Search,
  ShieldAlert,
  Users,
} from "lucide-react";

import { cn } from "@/lib/cn";

interface Tab {
  key: string;
  label: string;
  href: string;
  icon: React.ElementType;
}

function buildTabs(projectId: string): Tab[] {
  return [
    { key: "overview", label: "Overview", href: `/projects/${projectId}`, icon: LayoutDashboard },
    { key: "schedule", label: "Schedule", href: `/projects/${projectId}/schedule`, icon: CalendarClock },
    { key: "risks", label: "Risks", href: `/projects/${projectId}/risks`, icon: ShieldAlert },
    { key: "stage-gates", label: "Stage Gates", href: `/projects/${projectId}/stage-gates`, icon: GitBranch },
    { key: "commercial", label: "Commercial", href: `/projects/${projectId}/commercial`, icon: Banknote },
    { key: "design", label: "Design", href: `/projects/${projectId}/design`, icon: Ruler },
    { key: "documents", label: "Documents", href: `/projects/${projectId}/documents`, icon: FileText },
    { key: "meetings", label: "Meetings", href: `/projects/${projectId}/meetings`, icon: Users },
    { key: "orat", label: "ORAT", href: `/projects/${projectId}/orat`, icon: PlaneTakeoff },
    { key: "reporting", label: "Reporting", href: `/projects/${projectId}/reporting`, icon: BarChart3 },
    { key: "search", label: "Search", href: `/projects/${projectId}/search`, icon: Search },
  ];
}

export function ProjectNav({ projectId }: { projectId: string }) {
  const pathname = usePathname();
  const tabs = buildTabs(projectId);

  // Determine active tab: exact match for overview, startsWith for others
  function isActive(tab: Tab): boolean {
    if (tab.key === "overview") {
      return pathname === tab.href;
    }
    return pathname?.startsWith(tab.href) ?? false;
  }

  return (
    <nav className="bg-white border-b border-meridian-100 px-6 overflow-x-auto">
      <div className="flex gap-0 min-w-max">
        {tabs.map((tab) => {
          const active = isActive(tab);
          const Icon = tab.icon;
          return (
            <Link
              key={tab.key}
              href={tab.href}
              className={cn(
                "flex items-center gap-1.5 px-3 py-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors",
                active
                  ? "border-meridian-700 text-meridian-900"
                  : "border-transparent text-meridian-600 hover:text-meridian-900 hover:border-meridian-300"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
