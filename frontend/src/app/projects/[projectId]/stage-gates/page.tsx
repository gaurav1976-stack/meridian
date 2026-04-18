// Stage Gate Governance — gate-by-gate readiness, approvals progress, and a
// project-level rollup. Rendered server-side; backend computes all maths.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  GateDefinition,
  GateReadinessSummary,
  GovernanceSummary,
} from "@/lib/types";

function readinessColour(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-400";
  return "bg-rose-500";
}

function ProgressBar({ value, label }: { value: number; label: string }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-meridian-700">
        <span>{label}</span>
        <span className="font-medium">{clamped}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded bg-meridian-100">
        <div
          className={`h-full ${readinessColour(clamped)}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-1 rounded border border-meridian-100 bg-white px-4 py-3">
      <span className="text-xs uppercase tracking-wide text-meridian-600">
        {label}
      </span>
      <span className="text-2xl font-semibold text-meridian-900">{value}</span>
    </div>
  );
}

export default async function ProjectStageGatesPage({
  params,
}: {
  params: { projectId: string };
}) {
  let gates: GateDefinition[] = [];
  let summary: GovernanceSummary | null = null;
  try {
    [gates, summary] = await Promise.all([
      endpoints.listGates(params.projectId),
      endpoints.governanceSummary(params.projectId),
    ]);
  } catch {
    /* fall through — render empty state */
  }

  // Pull readiness rollups for each gate in parallel; tolerate per-gate failure.
  const readinessSettled = await Promise.allSettled(
    gates.map((g) => endpoints.gateReadiness(params.projectId, g.id))
  );
  const readinessByGate = new Map<string, GateReadinessSummary>();
  readinessSettled.forEach((r, i) => {
    if (r.status === "fulfilled") readinessByGate.set(gates[i].id, r.value);
  });

  const orderedGates = [...gates].sort((a, b) => a.target_month - b.target_month);

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-meridian-900">
          Stage Gate Governance
        </h1>
        <p className="text-sm text-meridian-600">
          G0 → G8 readiness across the programme.
        </p>
      </div>

      <Card>
        <CardHeader
          title="Programme Rollup"
          subtitle="Average gate readiness, approvals raised, decisions logged."
        />
        <CardBody>
          {summary ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <KpiTile label="Gates" value={summary.gate_count} />
              <KpiTile label="Active" value={summary.active_gates} />
              <KpiTile label="Blocked" value={summary.blocked_gates} />
              <KpiTile
                label="Avg. Readiness"
                value={`${summary.average_readiness_score}%`}
              />
              <KpiTile label="Evidence Items" value={summary.evidence_count} />
              <KpiTile label="Approvals" value={summary.approval_count} />
              <KpiTile label="Decisions" value={summary.decision_count} />
            </div>
          ) : (
            <p className="text-sm text-meridian-600">
              No governance data available for this project yet.
            </p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={`${orderedGates.length} gate${orderedGates.length === 1 ? "" : "s"}`}
          subtitle="Readiness = weighted (Accepted 1.0 / Submitted 0.6) over required evidence."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Target Month</th>
                <th className="px-5 py-3 font-medium w-48">Readiness</th>
                <th className="px-5 py-3 font-medium w-48">Approvals</th>
                <th className="px-5 py-3 font-medium">Evidence</th>
                <th className="px-5 py-3 font-medium">Decisions</th>
              </tr>
            </thead>
            <tbody>
              {orderedGates.map((g) => {
                const r = readinessByGate.get(g.id);
                return (
                  <tr key={g.id} className="border-t border-meridian-100 align-top">
                    <td className="px-5 py-3 font-mono text-xs">{g.code}</td>
                    <td className="px-5 py-3">
                      <div className="font-medium text-meridian-900">{g.name}</div>
                      <div className="text-xs text-meridian-600">{g.purpose}</div>
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge value={g.status} />
                    </td>
                    <td className="px-5 py-3">M{g.target_month}</td>
                    <td className="px-5 py-3">
                      {r ? (
                        <ProgressBar
                          value={r.readiness_score}
                          label={`${r.accepted_evidence_count}/${r.required_evidence_count} accepted`}
                        />
                      ) : (
                        <span className="text-xs text-meridian-500">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {r ? (
                        <ProgressBar
                          value={r.approval_progress}
                          label={`${r.approval_count} raised`}
                        />
                      ) : (
                        <span className="text-xs text-meridian-500">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {r ? (
                        <span className="text-xs text-meridian-700">
                          {r.submitted_evidence_count} submitted ·{" "}
                          {r.blocker_count > 0 ? (
                            <span className="font-semibold text-rose-700">
                              {r.blocker_count} blocker
                              {r.blocker_count === 1 ? "" : "s"}
                            </span>
                          ) : (
                            <span className="text-emerald-700">no blockers</span>
                          )}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs text-meridian-700">
                      {r?.latest_decision ?? "—"}
                    </td>
                  </tr>
                );
              })}
              {orderedGates.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-5 py-8 text-center text-sm text-meridian-600"
                  >
                    No stage gates defined yet for this project.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
