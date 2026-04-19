import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Banknote,
  BarChart3,
  CalendarClock,
  FileText,
  GitBranch,
  PlaneTakeoff,
  Ruler,
  Search,
  ShieldAlert,
  Users,
} from "lucide-react";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DonutRing } from "@/components/ui/DonutRing";
import { endpoints } from "@/lib/api/endpoints";

export default async function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  let dashboard;
  try {
    dashboard = await endpoints.projectDashboard(params.projectId);
  } catch {
    notFound();
  }
  if (!dashboard) notFound();
  const { project, counts } = dashboard;

  const modules = [
    {
      key: "schedule",
      label: "Schedule",
      icon: CalendarClock,
      href: `/projects/${project.id}/schedule`,
      stat: `${counts.schedule_activities} activities`,
      alert: counts.activities_critical > 0 ? `${counts.activities_critical} critical` : null,
      alertTone: "critical" as const,
    },
    {
      key: "risks",
      label: "Risks",
      icon: ShieldAlert,
      href: `/projects/${project.id}/risks`,
      stat: `${counts.open_risks} open risks`,
      alert: counts.open_risks > 5 ? "High exposure" : null,
      alertTone: "warning" as const,
    },
    {
      key: "stage-gates",
      label: "Stage Gates",
      icon: GitBranch,
      href: `/projects/${project.id}/stage-gates`,
      stat: "Governance",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "commercial",
      label: "Commercial",
      icon: Banknote,
      href: `/projects/${project.id}/commercial`,
      stat: `${counts.contracts} contracts`,
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "design",
      label: "Design",
      icon: Ruler,
      href: `/projects/${project.id}/design`,
      stat: "RIBA tracking",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "documents",
      label: "Documents",
      icon: FileText,
      href: `/projects/${project.id}/documents`,
      stat: "Document control",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "meetings",
      label: "Meetings",
      icon: Users,
      href: `/projects/${project.id}/meetings`,
      stat: "Actions & compliance",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "orat",
      label: "ORAT",
      icon: PlaneTakeoff,
      href: `/projects/${project.id}/orat`,
      stat: "Readiness & handover",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "reporting",
      label: "Reporting",
      icon: BarChart3,
      href: `/projects/${project.id}/reporting`,
      stat: "Export & archive",
      alert: null,
      alertTone: "neutral" as const,
    },
    {
      key: "search",
      label: "Search",
      icon: Search,
      href: `/projects/${project.id}/search`,
      stat: "Enterprise retrieval",
      alert: null,
      alertTone: "neutral" as const,
    },
  ];

  // Compute a rough overall health score for the donut
  const healthScore = Math.max(
    0,
    100 -
      counts.activities_critical * 10 -
      Math.min(counts.open_risks, 5) * 5
  );

  return (
    <div className="space-y-6">
      {/* Project header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs text-meridian-600 font-mono mb-1">{project.code}</div>
          <h1 className="text-2xl font-semibold text-meridian-900">{project.name}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-meridian-700">
            <StatusBadge value={project.status} />
            {project.location && <span>📍 {project.location}</span>}
            {project.stage && (
              <span className="bg-meridian-100 text-meridian-700 px-2 py-0.5 rounded text-xs font-medium">
                {project.stage}
              </span>
            )}
          </div>
          {project.description && (
            <p className="mt-2 text-sm text-meridian-600 max-w-2xl">{project.description}</p>
          )}
        </div>
        <DonutRing value={healthScore} size={72} label="Health" />
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Work Packages" value={counts.work_packages} />
        <StatCard label="Contracts" value={counts.contracts} />
        <StatCard
          label="Open Risks"
          value={counts.open_risks}
          tone={counts.open_risks > 5 ? "amber" : undefined}
        />
        <StatCard label="Activities" value={counts.schedule_activities} />
        <StatCard
          label="Critical Path"
          value={counts.activities_critical}
          tone={counts.activities_critical > 0 ? "red" : undefined}
        />
      </div>

      {/* Module grid */}
      <div>
        <h2 className="text-sm font-semibold text-meridian-700 uppercase tracking-wide mb-3">
          Workspace Modules
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <Link
                key={m.key}
                href={m.href}
                className="group flex flex-col gap-2 rounded-lg border border-meridian-100 bg-white p-4 hover:border-meridian-500 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-md bg-meridian-50 flex items-center justify-center group-hover:bg-meridian-100 transition-colors">
                    <Icon className="w-4 h-4 text-meridian-700" />
                  </div>
                  {m.alert && (
                    <span
                      className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        m.alertTone === "critical"
                          ? "bg-rose-100 text-rose-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {m.alert}
                    </span>
                  )}
                </div>
                <div>
                  <div className="text-sm font-semibold text-meridian-900 group-hover:text-meridian-700">
                    {m.label}
                  </div>
                  <div className="text-xs text-meridian-600 mt-0.5">{m.stat}</div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "amber" | "red";
}) {
  const colour =
    tone === "red"
      ? "text-rose-700"
      : tone === "amber"
      ? "text-amber-700"
      : "text-meridian-900";
  return (
    <Card>
      <CardBody className="py-3">
        <div className="text-xs text-meridian-600">{label}</div>
        <div className={`mt-1 text-2xl font-semibold tabular-nums ${colour}`}>{value}</div>
      </CardBody>
    </Card>
  );
}
