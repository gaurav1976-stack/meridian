import Link from "next/link";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { endpoints } from "@/lib/api/endpoints";
import type { Project } from "@/lib/types";

function statusDot(status: string) {
  const map: Record<string, string> = {
    Active: "bg-emerald-500",
    Planned: "bg-sky-400",
    "On Hold": "bg-amber-400",
    Closed: "bg-zinc-400",
  };
  return map[status] ?? "bg-zinc-300";
}

export default async function DashboardPage() {
  let projects: Project[] = [];
  let error: string | null = null;
  try {
    projects = await endpoints.listProjects();
  } catch (e) {
    error = (e as Error).message;
  }

  const active = projects.filter((p) => p.status === "Active").length;
  const planned = projects.filter((p) => p.status === "Planned").length;
  const onHold = projects.filter((p) => p.status === "On Hold").length;
  const closed = projects.filter((p) => p.status === "Closed").length;

  // Status distribution for mini bar chart
  const statusGroups = [
    { label: "Active", count: active, colour: "bg-emerald-500" },
    { label: "Planned", count: planned, colour: "bg-sky-400" },
    { label: "On Hold", count: onHold, colour: "bg-amber-400" },
    { label: "Closed", count: closed, colour: "bg-zinc-400" },
  ].filter((g) => g.count > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-meridian-900">Programme Dashboard</h1>
        <p className="text-sm text-meridian-600">
          High-level health across active airport programmes.
        </p>
      </div>

      {error ? (
        <Card>
          <CardBody className="text-amber-700 text-sm">
            Backend unreachable. Start the API with <code>docker compose up</code>. ({error})
          </CardBody>
        </Card>
      ) : null}

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="Total Projects"
          value={projects.length}
          sub="across all tenants"
        />
        <KpiCard
          label="Active"
          value={active}
          sub="currently in delivery"
          tone="positive"
        />
        <KpiCard
          label="Planned"
          value={planned}
          sub="pre-mobilisation"
          tone="neutral"
        />
        <KpiCard
          label="On Hold"
          value={onHold}
          sub="paused delivery"
          tone={onHold > 0 ? "warning" : "neutral"}
        />
      </div>

      {/* Status distribution */}
      {projects.length > 0 && (
        <Card>
          <CardHeader title="Portfolio Status Distribution" />
          <CardBody>
            <div className="space-y-3">
              {statusGroups.map((g) => (
                <div key={g.label} className="flex items-center gap-3">
                  <span className="w-20 text-xs text-meridian-700 text-right">{g.label}</span>
                  <div className="flex-1 h-5 bg-meridian-50 rounded overflow-hidden">
                    <div
                      className={`h-full ${g.colour} rounded transition-all duration-500`}
                      style={{ width: `${(g.count / projects.length) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-xs font-semibold text-meridian-900 tabular-nums">
                    {g.count}
                  </span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Projects table */}
      <Card>
        <CardHeader
          title="Projects"
          subtitle="Click a project name to open its workspace."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Location</th>
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {projects.length === 0 ? (
                <tr>
                  <td className="px-5 py-8 text-center text-meridian-600" colSpan={5}>
                    No projects yet. Run <code className="bg-meridian-100 px-1 rounded">docker compose up</code> to bootstrap demo data.
                  </td>
                </tr>
              ) : (
                projects.map((p) => (
                  <tr key={p.id} className="border-t border-meridian-100 hover:bg-meridian-50/60 transition-colors">
                    <td className="px-5 py-3 font-mono text-xs">{p.code}</td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/projects/${p.id}`}
                        className="font-medium text-meridian-700 hover:text-meridian-900 hover:underline"
                      >
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-meridian-600">{p.location ?? "—"}</td>
                    <td className="px-5 py-3">
                      {p.stage ? (
                        <span className="bg-meridian-100 text-meridian-700 px-2 py-0.5 rounded text-xs">
                          {p.stage}
                        </span>
                      ) : (
                        <span className="text-meridian-400">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${statusDot(p.status)}`} />
                        <StatusBadge value={p.status} />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}

function KpiCard({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: number;
  sub?: string;
  tone?: "positive" | "warning" | "critical" | "neutral";
}) {
  const colour =
    tone === "positive"
      ? "text-emerald-700"
      : tone === "warning"
      ? "text-amber-700"
      : tone === "critical"
      ? "text-rose-700"
      : "text-meridian-900";
  return (
    <Card>
      <CardBody className="py-4">
        <div className="text-xs text-meridian-600 font-medium uppercase tracking-wide">{label}</div>
        <div className={`mt-1 text-3xl font-semibold tabular-nums ${colour}`}>{value}</div>
        {sub && <div className="mt-1 text-xs text-meridian-500">{sub}</div>}
      </CardBody>
    </Card>
  );
}
