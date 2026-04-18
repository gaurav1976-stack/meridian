// Meetings & Accountability — meeting register, action items, compliance
// items, and per-package action pressure. Server-rendered; backend computes
// open/overdue rollups, average closure evidence, and compliance posture.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  AccountabilitySummary,
  ActionItem,
  ComplianceItem,
  MeetingRecord,
  PackageActionPressure,
} from "@/lib/types";

function evidenceColour(pct: number): string {
  if (pct >= 80) return "text-emerald-700";
  if (pct >= 50) return "text-amber-700";
  return "text-rose-700";
}

function evidenceTone(pct: number): "positive" | "warning" | "critical" {
  if (pct >= 80) return "positive";
  if (pct >= 50) return "warning";
  return "critical";
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

export default async function ProjectMeetingsPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: AccountabilitySummary | null = null;
  let meetings: MeetingRecord[] = [];
  let actions: ActionItem[] = [];
  let compliance: ComplianceItem[] = [];
  let pressure: PackageActionPressure[] = [];

  try {
    [summary, meetings, actions, compliance, pressure] = await Promise.all([
      endpoints.accountabilitySummary(params.projectId),
      endpoints.listMeetings(params.projectId),
      endpoints.listActions(params.projectId),
      endpoints.listComplianceItems(params.projectId),
      endpoints.actionPressure(params.projectId),
    ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-meridian-900">
          Meetings & Accountability
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load meetings & accountability data for this project. Check
          that the backend is running and the project exists.
        </p>
      </div>
    );
  }

  const overdueActions = actions
    .filter((a) => a.status === "Overdue")
    .sort((a, b) => a.due_month - b.due_month);

  const criticalActions = actions
    .filter(
      (a) =>
        a.priority === "Critical" &&
        a.status !== "Closed" &&
        a.status !== "Overdue"
    )
    .sort((a, b) => a.due_month - b.due_month);

  const nonCompliant = compliance
    .filter(
      (c) => c.status === "Non-Compliant" || c.status === "Overdue"
    )
    .sort((a, b) => a.due_month - b.due_month);

  const compliantOrInProgress = compliance.filter(
    (c) => c.status !== "Non-Compliant" && c.status !== "Overdue"
  );

  const sortedMeetings = [...meetings].sort((a, b) => b.month - a.month);

  const sortedPressure = [...pressure].sort((a, b) => {
    if (b.overdue_count !== a.overdue_count) {
      return b.overdue_count - a.overdue_count;
    }
    if (b.critical_count !== a.critical_count) {
      return b.critical_count - a.critical_count;
    }
    return b.action_count - a.action_count;
  });

  return (
    <div className="flex flex-col gap-6 p-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            Meetings & Accountability
          </h1>
          <p className="text-sm text-meridian-700">
            Meeting cadence, action item closure, and compliance obligations
            tracked across packages and linked modules.
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
            <KpiTile label="Meetings" value={summary.meeting_count} />
            <KpiTile label="Actions" value={summary.action_count} />
            <KpiTile
              label="Compliance items"
              value={summary.compliance_count}
            />
            <KpiTile
              label="Open actions"
              value={summary.open_action_count}
              tone={summary.open_action_count === 0 ? "positive" : "warning"}
              hint="Open / In Progress / Awaiting Review"
            />
            <KpiTile
              label="Overdue actions"
              value={summary.overdue_action_count}
              tone={
                summary.overdue_action_count === 0 ? "positive" : "critical"
              }
            />
            <KpiTile
              label="Avg closure evidence"
              value={`${summary.average_closure_evidence_pct}%`}
              tone={evidenceTone(summary.average_closure_evidence_pct)}
              hint="Across all action items"
            />
            <KpiTile
              label="Compliant"
              value={summary.compliant_count}
              tone={summary.compliant_count > 0 ? "positive" : "default"}
            />
            <KpiTile
              label="Non-compliant"
              value={summary.non_compliant_count}
              tone={
                summary.non_compliant_count === 0 ? "positive" : "critical"
              }
              hint="Non-Compliant + Overdue"
            />
          </div>
        </CardBody>
      </Card>

      {/* Overdue actions */}
      {overdueActions.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Overdue actions
            </h2>
            <p className="text-xs text-meridian-600">
              Action items past their due month — escalate to owner and
              originating forum.
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
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Priority</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {overdueActions.map((a) => (
                    <tr key={a.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{a.ref}</td>
                      <td className="px-3 py-2">{a.title}</td>
                      <td className="px-3 py-2">{a.owner}</td>
                      <td className="px-3 py-2 text-xs">
                        {a.source_type} · {a.source_ref}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={a.priority} />
                      </td>
                      <td className="px-3 py-2 text-right">M{a.due_month}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(a.closure_evidence_pct)}`}
                      >
                        {a.closure_evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Critical-priority actions still open */}
      {criticalActions.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Critical-priority actions
            </h2>
            <p className="text-xs text-meridian-600">
              Open critical actions; closure required ahead of next governance
              forum.
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
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {criticalActions.map((a) => (
                    <tr key={a.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{a.ref}</td>
                      <td className="px-3 py-2">{a.title}</td>
                      <td className="px-3 py-2">{a.owner}</td>
                      <td className="px-3 py-2 text-xs">
                        {a.source_type} · {a.source_ref}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={a.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{a.due_month}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(a.closure_evidence_pct)}`}
                      >
                        {a.closure_evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Compliance register — non-compliant first */}
      {compliance.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Compliance register ({compliance.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Non-compliant and overdue obligations are listed first.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Domain</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {[...nonCompliant, ...compliantOrInProgress].map((c) => (
                    <tr key={c.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{c.ref}</td>
                      <td className="px-3 py-2">{c.title}</td>
                      <td className="px-3 py-2">{c.domain}</td>
                      <td className="px-3 py-2">{c.owner}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={c.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{c.due_month}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(c.evidence_pct)}`}
                      >
                        {c.evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Meeting register */}
      {sortedMeetings.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Meeting register ({sortedMeetings.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Meetings recorded against this programme, most recent month
              first.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Linked module</th>
                    <th className="px-3 py-2">Chair</th>
                    <th className="px-3 py-2 text-right">Attendees</th>
                    <th className="px-3 py-2 text-right">Month</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedMeetings.map((m) => (
                    <tr key={m.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{m.ref}</td>
                      <td className="px-3 py-2">{m.title}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={m.meeting_type} />
                      </td>
                      <td className="px-3 py-2">{m.linked_module}</td>
                      <td className="px-3 py-2">{m.chair}</td>
                      <td className="px-3 py-2 text-right">
                        {m.attendee_count}
                      </td>
                      <td className="px-3 py-2 text-right">M{m.month}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Package action pressure — heat map */}
      {sortedPressure.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Package action pressure
            </h2>
            <p className="text-xs text-meridian-600">
              Action load per package, ordered by overdue then critical
              exposure. Use to retarget governance attention.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Package</th>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2 text-right">Actions</th>
                    <th className="px-3 py-2 text-right">Overdue</th>
                    <th className="px-3 py-2 text-right">Critical</th>
                    <th className="px-3 py-2 text-right">Avg evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedPressure.map((p) => (
                    <tr
                      key={p.package_id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">
                        {p.package_code}
                      </td>
                      <td className="px-3 py-2">{p.package_name}</td>
                      <td className="px-3 py-2 text-right">
                        {p.action_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.overdue_count === 0 ? "text-meridian-900" : "text-rose-700"}`}
                      >
                        {p.overdue_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.critical_count === 0 ? "text-meridian-900" : "text-amber-700"}`}
                      >
                        {p.critical_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(p.average_closure_evidence_pct)}`}
                      >
                        {p.average_closure_evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {meetings.length === 0 &&
      actions.length === 0 &&
      compliance.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No meetings, actions, or compliance items yet. Add via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/meetings
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
