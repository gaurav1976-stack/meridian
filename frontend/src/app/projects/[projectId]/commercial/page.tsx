// Commercial / Cost & Change Control — programme rollup, Earned Value
// Management snapshot, change register, and contract notice tracker.
// Rendered server-side; backend computes BAC/EV/AC/PV/CPI/SPI.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  CommercialChange,
  CommercialNotice,
  CommercialSummary,
  EvmSummary,
  PackageCommercialExposure,
} from "@/lib/types";

// All monetary values arrive in minor units (e.g. pence). Convert and format
// with a compact GBP presentation for dashboards.
function formatMoneyMinor(minor: number): string {
  const major = minor / 100;
  if (Math.abs(major) >= 1_000_000)
    return `£${(major / 1_000_000).toFixed(2)}M`;
  if (Math.abs(major) >= 1_000) return `£${(major / 1_000).toFixed(1)}k`;
  return `£${major.toFixed(0)}`;
}

function indexColour(value: number): string {
  // Programme escalation: SPI/CPI < 0.85 amber, < 0.75 red.
  if (value >= 0.95) return "text-emerald-700";
  if (value >= 0.85) return "text-amber-700";
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

export default async function ProjectCommercialPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: CommercialSummary | null = null;
  let evm: EvmSummary | null = null;
  let exposure: PackageCommercialExposure[] = [];
  let changes: CommercialChange[] = [];
  let notices: CommercialNotice[] = [];

  try {
    [summary, evm, exposure, changes, notices] = await Promise.all([
      endpoints.commercialSummary(params.projectId),
      endpoints.evmSummary(params.projectId),
      endpoints.packageExposure(params.projectId),
      endpoints.listChanges(params.projectId),
      endpoints.listNotices(params.projectId),
    ]);
  } catch {
    /* fall through — render empty state */
  }

  const orderedChanges = [...changes].sort((a, b) =>
    a.ref.localeCompare(b.ref)
  );
  const orderedNotices = [...notices].sort((a, b) => {
    // Overdue first, then by due_days ascending.
    if (a.status === "Overdue" && b.status !== "Overdue") return -1;
    if (b.status === "Overdue" && a.status !== "Overdue") return 1;
    return a.due_days - b.due_days;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-meridian-900">
          Commercial &amp; Cost Control
        </h1>
        <p className="text-sm text-meridian-600">
          Budget &middot; Forecast &middot; Earned Value &middot; Change exposure.
        </p>
      </div>

      <Card>
        <CardHeader
          title="Programme Rollup"
          subtitle="Budget, committed, forecast and actual across all package cost controls."
        />
        <CardBody>
          {summary ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <KpiTile
                label="Budget"
                value={formatMoneyMinor(summary.budget_minor)}
              />
              <KpiTile
                label="Committed"
                value={formatMoneyMinor(summary.committed_minor)}
              />
              <KpiTile
                label="Forecast"
                value={formatMoneyMinor(summary.forecast_minor)}
              />
              <KpiTile
                label="Actual"
                value={formatMoneyMinor(summary.actual_minor)}
              />
              <KpiTile
                label="Forecast Variance"
                value={formatMoneyMinor(summary.forecast_variance_minor)}
                hint="Forecast − Budget"
                tone={
                  summary.forecast_variance_minor > 0 ? "critical" : "positive"
                }
              />
              <KpiTile
                label="Change Exposure"
                value={formatMoneyMinor(summary.change_exposure_minor)}
                hint="Open & approved changes"
                tone={summary.change_exposure_minor > 0 ? "warning" : "default"}
              />
              <KpiTile
                label="Notices"
                value={summary.notice_count}
                hint={`${summary.overdue_notice_count} overdue`}
                tone={
                  summary.overdue_notice_count > 0 ? "critical" : "default"
                }
              />
              <KpiTile
                label="Strong Entitlement"
                value={summary.strong_entitlement_count}
                hint="Changes with strong claim basis"
              />
            </div>
          ) : (
            <p className="text-sm text-meridian-600">
              No commercial data available for this project yet.
            </p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Earned Value (ANSI/EIA-748)"
          subtitle="BAC, PV, EV, AC with CPI / SPI performance indices."
        />
        <CardBody>
          {evm ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <KpiTile
                label="BAC"
                value={formatMoneyMinor(evm.bac_minor)}
                hint="Budget at Completion"
              />
              <KpiTile
                label="PV"
                value={formatMoneyMinor(evm.pv_minor)}
                hint="Planned Value"
              />
              <KpiTile
                label="EV"
                value={formatMoneyMinor(evm.ev_minor)}
                hint="Earned Value"
              />
              <KpiTile
                label="AC"
                value={formatMoneyMinor(evm.ac_minor)}
                hint="Actual Cost"
              />
              <div className="flex flex-col gap-1 rounded border border-meridian-100 bg-white px-4 py-3">
                <span className="text-xs uppercase tracking-wide text-meridian-600">
                  CPI
                </span>
                <span
                  className={`text-2xl font-semibold ${indexColour(evm.cpi)}`}
                >
                  {evm.cpi.toFixed(2)}
                </span>
                <span className="text-xs text-meridian-600">
                  EV / AC &mdash; cost performance
                </span>
              </div>
              <div className="flex flex-col gap-1 rounded border border-meridian-100 bg-white px-4 py-3">
                <span className="text-xs uppercase tracking-wide text-meridian-600">
                  SPI
                </span>
                <span
                  className={`text-2xl font-semibold ${indexColour(evm.spi)}`}
                >
                  {evm.spi.toFixed(2)}
                </span>
                <span className="text-xs text-meridian-600">
                  EV / PV &mdash; schedule performance
                </span>
              </div>
              <KpiTile
                label="CV"
                value={formatMoneyMinor(evm.cv_minor)}
                hint="Cost Variance (EV − AC)"
                tone={evm.cv_minor < 0 ? "critical" : "positive"}
              />
              <KpiTile
                label="SV"
                value={formatMoneyMinor(evm.sv_minor)}
                hint="Schedule Variance (EV − PV)"
                tone={evm.sv_minor < 0 ? "critical" : "positive"}
              />
            </div>
          ) : (
            <p className="text-sm text-meridian-600">No EVM data yet.</p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={`Package Exposure (${exposure.length})`}
          subtitle="Forecast, actual, change exposure and notice load by work package."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Package</th>
                <th className="px-5 py-3 font-medium text-right">Budget</th>
                <th className="px-5 py-3 font-medium text-right">Forecast</th>
                <th className="px-5 py-3 font-medium text-right">Actual</th>
                <th className="px-5 py-3 font-medium text-right">
                  Change Exposure
                </th>
                <th className="px-5 py-3 font-medium text-right">Notices</th>
              </tr>
            </thead>
            <tbody>
              {exposure.map((p) => (
                <tr
                  key={p.package_id}
                  className="border-t border-meridian-100 align-top"
                >
                  <td className="px-5 py-3 font-mono text-xs">
                    {p.package_code}
                  </td>
                  <td className="px-5 py-3 font-medium text-meridian-900">
                    {p.package_name}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {formatMoneyMinor(p.budget_minor)}
                  </td>
                  <td
                    className={`px-5 py-3 text-right ${
                      p.forecast_minor > p.budget_minor
                        ? "text-rose-700 font-medium"
                        : ""
                    }`}
                  >
                    {formatMoneyMinor(p.forecast_minor)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {formatMoneyMinor(p.actual_minor)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {p.change_exposure_minor > 0 ? (
                      <span className="text-amber-700 font-medium">
                        {formatMoneyMinor(p.change_exposure_minor)}
                      </span>
                    ) : (
                      <span className="text-meridian-500">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {p.notice_count}
                    {p.overdue_notice_count > 0 ? (
                      <span className="ml-2 inline-flex items-center rounded bg-rose-100 px-1.5 text-xs font-medium text-rose-700">
                        {p.overdue_notice_count} overdue
                      </span>
                    ) : null}
                  </td>
                </tr>
              ))}
              {exposure.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-5 py-8 text-center text-sm text-meridian-600"
                  >
                    No package cost controls configured yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={`Change Register (${orderedChanges.length})`}
          subtitle="Compensation Events, Variations and Claims with cost / time impact."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Ref</th>
                <th className="px-5 py-3 font-medium">Title</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Entitlement</th>
                <th className="px-5 py-3 font-medium text-right">Cost</th>
                <th className="px-5 py-3 font-medium text-right">Time (wks)</th>
                <th className="px-5 py-3 font-medium">Owner</th>
              </tr>
            </thead>
            <tbody>
              {orderedChanges.map((c) => (
                <tr
                  key={c.id}
                  className="border-t border-meridian-100 align-top"
                >
                  <td className="px-5 py-3 font-mono text-xs">{c.ref}</td>
                  <td className="px-5 py-3">
                    <div className="font-medium text-meridian-900">
                      {c.title}
                    </div>
                    <div className="text-xs text-meridian-600">{c.cause}</div>
                  </td>
                  <td className="px-5 py-3 text-xs">{c.change_type}</td>
                  <td className="px-5 py-3">
                    <StatusBadge value={c.status} />
                  </td>
                  <td className="px-5 py-3">
                    <StatusBadge value={c.entitlement} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    {formatMoneyMinor(c.cost_impact_minor)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {c.time_impact_weeks}
                  </td>
                  <td className="px-5 py-3 text-xs">{c.owner}</td>
                </tr>
              ))}
              {orderedChanges.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-5 py-8 text-center text-sm text-meridian-600"
                  >
                    No commercial changes raised yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={`Contract Notices (${orderedNotices.length})`}
          subtitle="EWN, Notice, CE Notification, Claim Notice — overdue first."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Ref</th>
                <th className="px-5 py-3 font-medium">Contract</th>
                <th className="px-5 py-3 font-medium">Kind</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium text-right">
                  Due (days)
                </th>
                <th className="px-5 py-3 font-medium">Owner</th>
              </tr>
            </thead>
            <tbody>
              {orderedNotices.map((n) => (
                <tr
                  key={n.id}
                  className="border-t border-meridian-100 align-top"
                >
                  <td className="px-5 py-3 font-mono text-xs">{n.ref}</td>
                  <td className="px-5 py-3 font-mono text-xs">
                    {n.contract_ref}
                  </td>
                  <td className="px-5 py-3 text-xs">{n.kind}</td>
                  <td className="px-5 py-3">
                    <StatusBadge value={n.status} />
                  </td>
                  <td
                    className={`px-5 py-3 text-right ${
                      n.status === "Overdue" ? "text-rose-700 font-semibold" : ""
                    }`}
                  >
                    {n.due_days}
                  </td>
                  <td className="px-5 py-3 text-xs">{n.owner}</td>
                </tr>
              ))}
              {orderedNotices.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-8 text-center text-sm text-meridian-600"
                  >
                    No contract notices logged yet.
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
