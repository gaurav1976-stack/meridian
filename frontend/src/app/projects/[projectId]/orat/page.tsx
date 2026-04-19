// ORAT Readiness & Handover — workstreams, trials, training groups, handover
// items, and per-package handover pressure. Server-rendered; backend computes
// at-risk, passed-trial, training-completion and accepted/blocked handover
// rollups. Pattern mirrors meetings/page.tsx.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  HandoverItem,
  OratReadinessSummary,
  OratTrial,
  OratWorkstream,
  PackageHandoverPressure,
  TrainingGroup,
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

function trainingRatio(g: TrainingGroup): number {
  if (g.target_headcount === 0) return 0;
  return Math.round((g.trained_headcount / g.target_headcount) * 100);
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

export default async function ProjectOratPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: OratReadinessSummary | null = null;
  let workstreams: OratWorkstream[] = [];
  let trials: OratTrial[] = [];
  let training: TrainingGroup[] = [];
  let handover: HandoverItem[] = [];
  let pressure: PackageHandoverPressure[] = [];

  try {
    [summary, workstreams, trials, training, handover, pressure] =
      await Promise.all([
        endpoints.oratReadinessSummary(params.projectId),
        endpoints.listOratWorkstreams(params.projectId),
        endpoints.listOratTrials(params.projectId),
        endpoints.listTrainingGroups(params.projectId),
        endpoints.listHandoverItems(params.projectId),
        endpoints.handoverPressure(params.projectId),
      ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-meridian-900">
          ORAT Readiness & Handover
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load ORAT data for this project. Check that the backend is
          running and the project exists.
        </p>
      </div>
    );
  }

  const sortedWorkstreams = [...workstreams].sort((a, b) => {
    const rank: Record<string, number> = {
      "At Risk": 0,
      "In Progress": 1,
      "Not Started": 2,
      Ready: 3,
    };
    const ra = rank[a.status] ?? 99;
    const rb = rank[b.status] ?? 99;
    if (ra !== rb) return ra - rb;
    return a.due_month - b.due_month;
  });

  const failedTrials = trials
    .filter((t) => t.status === "Failed")
    .sort((a, b) => a.month - b.month);

  const otherTrials = trials
    .filter((t) => t.status !== "Failed")
    .sort((a, b) => {
      // upcoming first then completed
      const order: Record<string, number> = {
        Planned: 0,
        Prepared: 1,
        Executed: 2,
        Passed: 3,
      };
      const oa = order[a.status] ?? 99;
      const ob = order[b.status] ?? 99;
      if (oa !== ob) return oa - ob;
      return a.month - b.month;
    });

  const sortedTraining = [...training].sort(
    (a, b) => trainingRatio(a) - trainingRatio(b)
  );

  const blockedHandover = handover
    .filter((h) => h.status === "Blocked")
    .sort((a, b) => a.evidence_pct - b.evidence_pct);

  const otherHandover = handover
    .filter((h) => h.status !== "Blocked")
    .sort((a, b) => {
      const order: Record<string, number> = {
        Pending: 0,
        "In Verification": 1,
        Accepted: 2,
      };
      const oa = order[a.status] ?? 99;
      const ob = order[b.status] ?? 99;
      if (oa !== ob) return oa - ob;
      return a.ref.localeCompare(b.ref);
    });

  const sortedPressure = [...pressure].sort((a, b) => {
    if (b.blocked_count !== a.blocked_count) {
      return b.blocked_count - a.blocked_count;
    }
    if (b.pending_count !== a.pending_count) {
      return b.pending_count - a.pending_count;
    }
    return b.handover_count - a.handover_count;
  });

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            ORAT Readiness & Handover
          </h1>
          <p className="text-sm text-meridian-700">
            Workstream progress, trial outcomes, training completion and asset
            handover posture — the four telemetry pillars feeding go-live
            readiness.
          </p>
        </div>
      </header>

      {/* Readiness rollup */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-meridian-900">
            Readiness rollup
          </h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label="Workstreams" value={summary.workstream_count} />
            <KpiTile label="Trials" value={summary.trial_count} />
            <KpiTile
              label="Training groups"
              value={summary.training_group_count}
            />
            <KpiTile
              label="Handover items"
              value={summary.handover_item_count}
            />
            <KpiTile
              label="Avg workstream progress"
              value={`${summary.average_workstream_progress_pct}%`}
              tone={evidenceTone(summary.average_workstream_progress_pct)}
            />
            <KpiTile
              label="At-risk workstreams"
              value={summary.at_risk_workstream_count}
              tone={
                summary.at_risk_workstream_count === 0 ? "positive" : "critical"
              }
            />
            <KpiTile
              label="Passed trials"
              value={summary.passed_trial_count}
              tone={summary.passed_trial_count > 0 ? "positive" : "default"}
            />
            <KpiTile
              label="Training completion"
              value={`${summary.training_completion_pct}%`}
              tone={evidenceTone(summary.training_completion_pct)}
              hint="Sum trained / sum target"
            />
            <KpiTile
              label="Accepted handovers"
              value={summary.accepted_handover_count}
              tone={
                summary.accepted_handover_count > 0 ? "positive" : "default"
              }
            />
            <KpiTile
              label="Blocked handovers"
              value={summary.blocked_handover_count}
              tone={
                summary.blocked_handover_count === 0 ? "positive" : "critical"
              }
            />
          </div>
        </CardBody>
      </Card>

      {/* Workstreams */}
      {sortedWorkstreams.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              ORAT workstreams ({sortedWorkstreams.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Ordered by readiness posture — at-risk first, ready last.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Workstream</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2 text-right">Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedWorkstreams.map((w) => (
                    <tr key={w.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2">{w.name}</td>
                      <td className="px-3 py-2">{w.owner}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={w.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{w.due_month}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(w.progress_pct)}`}
                      >
                        {w.progress_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Failed trials — surface first */}
      {failedTrials.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Failed trials
            </h2>
            <p className="text-xs text-meridian-600">
              Failed trials must feed the snag list and a rerun before the next
              ORAT governance forum.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2 text-right">Participants</th>
                    <th className="px-3 py-2 text-right">Month</th>
                    <th className="px-3 py-2">Observations</th>
                  </tr>
                </thead>
                <tbody>
                  {failedTrials.map((t) => (
                    <tr key={t.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{t.ref}</td>
                      <td className="px-3 py-2">{t.title}</td>
                      <td className="px-3 py-2 text-right">
                        {t.participants}
                      </td>
                      <td className="px-3 py-2 text-right">M{t.month}</td>
                      <td className="px-3 py-2 text-xs text-meridian-700">
                        {t.observations}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Trial log */}
      {otherTrials.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Trial log ({otherTrials.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Upcoming trials first, then executed and passed.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Participants</th>
                    <th className="px-3 py-2 text-right">Month</th>
                  </tr>
                </thead>
                <tbody>
                  {otherTrials.map((t) => (
                    <tr key={t.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{t.ref}</td>
                      <td className="px-3 py-2">{t.title}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={t.status} />
                      </td>
                      <td className="px-3 py-2 text-right">
                        {t.participants}
                      </td>
                      <td className="px-3 py-2 text-right">M{t.month}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Training groups */}
      {sortedTraining.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Training groups ({sortedTraining.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Sorted by completion ratio — least-trained cohorts first.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Function</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Trained</th>
                    <th className="px-3 py-2 text-right">Target</th>
                    <th className="px-3 py-2 text-right">Ratio</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTraining.map((g) => {
                    const ratio = trainingRatio(g);
                    return (
                      <tr key={g.id} className="border-t border-meridian-100">
                        <td className="px-3 py-2">{g.function_name}</td>
                        <td className="px-3 py-2">{g.owner}</td>
                        <td className="px-3 py-2">
                          <StatusBadge label={g.status} />
                        </td>
                        <td className="px-3 py-2 text-right">
                          {g.trained_headcount}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {g.target_headcount}
                        </td>
                        <td
                          className={`px-3 py-2 text-right font-medium ${evidenceColour(ratio)}`}
                        >
                          {ratio}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Handover register — blocked first */}
      {handover.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Handover register ({handover.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Blocked items are listed first and will defer go-live until
              cleared.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Asset group</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {[...blockedHandover, ...otherHandover].map((h) => (
                    <tr key={h.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{h.ref}</td>
                      <td className="px-3 py-2">{h.asset_group}</td>
                      <td className="px-3 py-2">{h.owner}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={h.status} />
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(h.evidence_pct)}`}
                      >
                        {h.evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Handover pressure heat-map */}
      {sortedPressure.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Package handover pressure
            </h2>
            <p className="text-xs text-meridian-600">
              Handover load per package, ordered by blocked then pending
              exposure. Use to target ORAT focus ahead of go-live.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Package</th>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2 text-right">Items</th>
                    <th className="px-3 py-2 text-right">Accepted</th>
                    <th className="px-3 py-2 text-right">Pending</th>
                    <th className="px-3 py-2 text-right">Blocked</th>
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
                        {p.handover_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.accepted_count > 0 ? "text-emerald-700" : "text-meridian-900"}`}
                      >
                        {p.accepted_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.pending_count === 0 ? "text-meridian-900" : "text-amber-700"}`}
                      >
                        {p.pending_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.blocked_count === 0 ? "text-meridian-900" : "text-rose-700"}`}
                      >
                        {p.blocked_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${evidenceColour(p.average_evidence_pct)}`}
                      >
                        {p.average_evidence_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {workstreams.length === 0 &&
      trials.length === 0 &&
      training.length === 0 &&
      handover.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No ORAT data yet. Seed via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/orat/workstreams
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
