// Design Management — project-level rollup of RIBA-stage design packages,
// deliverables, interface register, BIM coordination status, and the
// freeze-control surface. Rendered server-side; backend computes maturity,
// freeze variance, and critical-clash counts.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  BimItem,
  DesignDeliverable,
  DesignInterface,
  DesignPackage,
  DesignSummary,
  FreezeControlReport,
} from "@/lib/types";

function varianceColour(months: number): string {
  if (months <= 0) return "text-emerald-700";
  if (months <= 2) return "text-amber-700";
  return "text-rose-700";
}

function maturityColour(pct: number): string {
  if (pct >= 80) return "text-emerald-700";
  if (pct >= 50) return "text-amber-700";
  return "text-rose-700";
}

function KpiTile({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "positive" | "warning" | "critical";
}) {
  const toneClass =
    tone === "positive"
      ? "text-emerald-700"
      : tone === "warning"
        ? "text-amber-700"
        : tone === "critical"
          ? "text-rose-700"
          : "text-meridian-900";
  return (
    <div className="flex flex-col gap-1 rounded border border-meridian-100 bg-white px-4 py-3">
      <span className="text-xs uppercase tracking-wide text-meridian-600">
        {label}
      </span>
      <span className={`text-2xl font-semibold ${toneClass}`}>{value}</span>
      {hint ? (
        <span className="text-xs text-meridian-600">{hint}</span>
      ) : null}
    </div>
  );
}

export default async function ProjectDesignPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: DesignSummary | null = null;
  let packages: DesignPackage[] = [];
  let deliverables: DesignDeliverable[] = [];
  let interfaces: DesignInterface[] = [];
  let bim: BimItem[] = [];
  let freeze: FreezeControlReport | null = null;

  try {
    [summary, packages, deliverables, interfaces, bim, freeze] =
      await Promise.all([
        endpoints.designSummary(params.projectId),
        endpoints.listDesignPackages(params.projectId),
        endpoints.listDeliverables(params.projectId),
        endpoints.listInterfaces(params.projectId),
        endpoints.listBimItems(params.projectId),
        endpoints.freezeControl(params.projectId),
      ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-meridian-900">
          Design Management
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load design data for this project. Check that the backend
          is running and the project exists.
        </p>
      </div>
    );
  }

  const overdueDeliverables = deliverables
    .filter((d) => d.status === "Overdue")
    .sort((a, b) => a.due_month - b.due_month);

  const sortedInterfaces = [...interfaces].sort(
    (a, b) => b.severity - a.severity
  );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            Design Management
          </h1>
          <p className="text-sm text-meridian-700">
            RIBA Plan of Work tracking — maturity, deliverables, interfaces, BIM
            federation, and freeze control.
          </p>
        </div>
      </header>

      {/* Programme rollup */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-meridian-900">
            Programme rollup
          </h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile
              label="Design packages"
              value={summary.design_package_count}
            />
            <KpiTile
              label="Avg maturity"
              value={`${summary.average_maturity_pct}%`}
              tone={
                summary.average_maturity_pct >= 80
                  ? "positive"
                  : summary.average_maturity_pct >= 50
                    ? "warning"
                    : "critical"
              }
            />
            <KpiTile
              label="Frozen packages"
              value={summary.frozen_package_count}
              hint="Design baseline locked"
            />
            <KpiTile
              label="Avg freeze variance"
              value={`${summary.average_freeze_variance_months > 0 ? "+" : ""}${summary.average_freeze_variance_months} mo`}
              tone={
                summary.average_freeze_variance_months <= 0
                  ? "positive"
                  : summary.average_freeze_variance_months <= 2
                    ? "warning"
                    : "critical"
              }
              hint="Positive = slip"
            />
            <KpiTile
              label="Deliverables"
              value={summary.deliverable_count}
            />
            <KpiTile
              label="Overdue deliverables"
              value={summary.overdue_deliverable_count}
              tone={
                summary.overdue_deliverable_count === 0 ? "positive" : "critical"
              }
            />
            <KpiTile
              label="Escalated interfaces"
              value={summary.escalated_interface_count}
              tone={
                summary.escalated_interface_count === 0 ? "positive" : "critical"
              }
            />
            <KpiTile
              label="Critical clashes"
              value={summary.critical_clash_count}
              tone={
                summary.critical_clash_count === 0 ? "positive" : "critical"
              }
              hint="BIM federation"
            />
          </div>
        </CardBody>
      </Card>

      {/* Freeze control */}
      {freeze && freeze.entries.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Freeze control
            </h2>
            <p className="text-xs text-meridian-600">
              Planned vs current design-freeze month per package. Positive
              variance is slip.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Code</th>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">Stage</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Maturity</th>
                    <th className="px-3 py-2 text-right">Planned</th>
                    <th className="px-3 py-2 text-right">Current</th>
                    <th className="px-3 py-2 text-right">Variance</th>
                  </tr>
                </thead>
                <tbody>
                  {freeze.entries.map((e) => (
                    <tr
                      key={e.design_package_id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{e.code}</td>
                      <td className="px-3 py-2">{e.name}</td>
                      <td className="px-3 py-2">RIBA {e.stage}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={e.status} />
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${maturityColour(e.maturity_pct)}`}
                      >
                        {e.maturity_pct}%
                      </td>
                      <td className="px-3 py-2 text-right">
                        M{e.freeze_planned_month}
                      </td>
                      <td className="px-3 py-2 text-right">
                        M{e.freeze_current_month}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-semibold ${varianceColour(e.variance_months)}`}
                      >
                        {e.variance_months > 0 ? "+" : ""}
                        {e.variance_months} mo
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Overdue deliverables */}
      {overdueDeliverables.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Overdue deliverables
            </h2>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Discipline</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Stage</th>
                    <th className="px-3 py-2 text-right">Due month</th>
                    <th className="px-3 py-2">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {overdueDeliverables.map((d) => (
                    <tr
                      key={d.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{d.ref}</td>
                      <td className="px-3 py-2">{d.title}</td>
                      <td className="px-3 py-2">{d.discipline}</td>
                      <td className="px-3 py-2">{d.deliverable_type}</td>
                      <td className="px-3 py-2">RIBA {d.stage}</td>
                      <td className="px-3 py-2 text-right">M{d.due_month}</td>
                      <td className="px-3 py-2">{d.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Design interface register */}
      {sortedInterfaces.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Interface register
            </h2>
            <p className="text-xs text-meridian-600">
              Cross-package design interfaces, ordered by severity.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2 text-right">Severity</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due month</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedInterfaces.map((i) => (
                    <tr
                      key={i.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{i.ref}</td>
                      <td className="px-3 py-2">{i.title}</td>
                      <td className="px-3 py-2">{i.owner}</td>
                      <td className="px-3 py-2 text-right">{i.severity}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={i.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{i.due_month}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* BIM coordination */}
      {bim.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              BIM coordination
            </h2>
            <p className="text-xs text-meridian-600">
              Per-workstream federation readiness and clash position.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Workstream</th>
                    <th className="px-3 py-2">Model share</th>
                    <th className="px-3 py-2">Federation</th>
                    <th className="px-3 py-2 text-right">Clashes open</th>
                    <th className="px-3 py-2 text-right">Critical clashes</th>
                  </tr>
                </thead>
                <tbody>
                  {bim.map((b) => (
                    <tr
                      key={b.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2">{b.workstream}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={b.model_share_status} />
                      </td>
                      <td className="px-3 py-2">
                        {b.federation_ready ? "Ready" : "Not ready"}
                      </td>
                      <td className="px-3 py-2 text-right">{b.clash_open}</td>
                      <td
                        className={`px-3 py-2 text-right font-semibold ${b.clash_critical === 0 ? "text-emerald-700" : "text-rose-700"}`}
                      >
                        {b.clash_critical}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* All deliverables */}
      {deliverables.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              All deliverables ({deliverables.length})
            </h2>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Discipline</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Stage</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {deliverables.map((d) => (
                    <tr
                      key={d.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{d.ref}</td>
                      <td className="px-3 py-2">{d.title}</td>
                      <td className="px-3 py-2">{d.discipline}</td>
                      <td className="px-3 py-2">{d.deliverable_type}</td>
                      <td className="px-3 py-2">RIBA {d.stage}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={d.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{d.due_month}</td>
                      <td className="px-3 py-2">{d.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {packages.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No design packages yet. Add one via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/design/design-packages
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
