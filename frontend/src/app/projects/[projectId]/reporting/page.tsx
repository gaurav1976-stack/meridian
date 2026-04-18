// Reporting & Export — template catalogue, export job queue, archive register
// and template usage pressure. Server-rendered; backend provides the four
// telemetry rollups (template count, in-flight jobs, ready/failed terminals,
// average progress) and the per-template heat-map. Pattern mirrors orat/page.tsx.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  ArchiveRecord,
  ExportJob,
  ReportTemplate,
  ReportingSummary,
  TemplateUsagePressure,
} from "@/lib/types";

function progressColour(pct: number): string {
  if (pct >= 80) return "text-emerald-700";
  if (pct >= 50) return "text-amber-700";
  return "text-rose-700";
}

function progressTone(pct: number): "positive" | "warning" | "critical" {
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

export default async function ProjectReportingPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: ReportingSummary | null = null;
  let templates: ReportTemplate[] = [];
  let jobs: ExportJob[] = [];
  let archive: ArchiveRecord[] = [];
  let pressure: TemplateUsagePressure[] = [];

  try {
    [summary, templates, jobs, archive, pressure] = await Promise.all([
      endpoints.reportingSummary(params.projectId),
      endpoints.listReportTemplates(params.projectId),
      endpoints.listExportJobs(params.projectId),
      endpoints.listArchiveRecords(params.projectId),
      endpoints.templateUsagePressure(params.projectId),
    ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-meridian-900">
          Reporting & Export
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load reporting data for this project. Check that the backend
          is running and the project exists.
        </p>
      </div>
    );
  }

  // Templates — enabled first, then by name.
  const sortedTemplates = [...templates].sort((a, b) => {
    if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
    return a.name.localeCompare(b.name);
  });

  // Failed jobs surface first.
  const failedJobs = jobs
    .filter((j) => j.status === "Failed")
    .sort((a, b) => b.created_month - a.created_month);

  // Active queue: Queued + Generating.
  const activeJobs = jobs
    .filter((j) => j.status === "Queued" || j.status === "Generating")
    .sort((a, b) => {
      // Generating before Queued, then most recent first.
      if (a.status !== b.status) {
        return a.status === "Generating" ? -1 : 1;
      }
      return b.created_month - a.created_month;
    });

  // Other jobs (Ready / Draft) — most recent first.
  const otherJobs = jobs
    .filter(
      (j) =>
        j.status !== "Failed" &&
        j.status !== "Queued" &&
        j.status !== "Generating"
    )
    .sort((a, b) => b.created_month - a.created_month);

  const sortedArchive = [...archive].sort(
    (a, b) => b.generated_month - a.generated_month
  );

  // Pressure — failed first, then in-flight, then total job_count.
  const sortedPressure = [...pressure].sort((a, b) => {
    if (b.failed_count !== a.failed_count) {
      return b.failed_count - a.failed_count;
    }
    if (b.active_count !== a.active_count) {
      return b.active_count - a.active_count;
    }
    return b.job_count - a.job_count;
  });

  return (
    <div className="flex flex-col gap-6 p-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            Reporting & Export
          </h1>
          <p className="text-sm text-meridian-700">
            Template catalogue, export queue health, archived artefact register
            and per-template usage pressure — the spine of the PMO reporting
            pipeline.
          </p>
        </div>
      </header>

      {/* Reporting rollup */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-meridian-900">
            Reporting rollup
          </h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label="Templates" value={summary.template_count} />
            <KpiTile
              label="Enabled templates"
              value={summary.enabled_template_count}
              tone={
                summary.enabled_template_count > 0 ? "positive" : "default"
              }
              hint="Selectable when authoring a job"
            />
            <KpiTile label="Export jobs" value={summary.job_count} />
            <KpiTile
              label="Active queue"
              value={summary.active_job_count}
              tone={summary.active_job_count > 0 ? "warning" : "default"}
              hint="Queued + Generating"
            />
            <KpiTile
              label="Ready"
              value={summary.ready_job_count}
              tone={summary.ready_job_count > 0 ? "positive" : "default"}
            />
            <KpiTile
              label="Failed"
              value={summary.failed_job_count}
              tone={summary.failed_job_count === 0 ? "positive" : "critical"}
            />
            <KpiTile label="Archive entries" value={summary.archive_count} />
            <KpiTile
              label="Avg job progress"
              value={`${summary.average_job_progress_pct}%`}
              tone={progressTone(summary.average_job_progress_pct)}
            />
          </div>
        </CardBody>
      </Card>

      {/* Failed jobs — surface first */}
      {failedJobs.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Failed export jobs
            </h2>
            <p className="text-xs text-meridian-600">
              Investigate the error message and re-author or retry — failed jobs
              do not auto-retry.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Format</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2 text-right">Month</th>
                    <th className="px-3 py-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {failedJobs.map((j) => (
                    <tr key={j.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{j.ref}</td>
                      <td className="px-3 py-2">{j.title}</td>
                      <td className="px-3 py-2">{j.format}</td>
                      <td className="px-3 py-2">{j.created_by}</td>
                      <td className="px-3 py-2 text-right">M{j.created_month}</td>
                      <td className="px-3 py-2 text-xs text-rose-700">
                        {j.error_message ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Active queue */}
      {activeJobs.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Active queue ({activeJobs.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Generating ahead of Queued. Worker emits live progress.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Format</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {activeJobs.map((j) => (
                    <tr key={j.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{j.ref}</td>
                      <td className="px-3 py-2">{j.title}</td>
                      <td className="px-3 py-2">{j.format}</td>
                      <td className="px-3 py-2">{j.created_by}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={j.status} />
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${progressColour(j.progress_pct)}`}
                      >
                        {j.progress_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Other jobs — Ready / Draft */}
      {otherJobs.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Job log ({otherJobs.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Drafts and ready artefacts — most recent month first.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Format</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Month</th>
                    <th className="px-3 py-2">Artifact</th>
                  </tr>
                </thead>
                <tbody>
                  {otherJobs.map((j) => (
                    <tr key={j.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{j.ref}</td>
                      <td className="px-3 py-2">{j.title}</td>
                      <td className="px-3 py-2">{j.format}</td>
                      <td className="px-3 py-2">{j.created_by}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={j.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{j.created_month}</td>
                      <td className="px-3 py-2 text-xs">
                        {j.artifact_url ? (
                          <a
                            className="text-meridian-700 underline"
                            href={j.artifact_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open
                          </a>
                        ) : (
                          <span className="text-meridian-500">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Templates */}
      {sortedTemplates.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Template catalogue ({sortedTemplates.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Enabled templates first. Disabled templates remain on the register
              so historic jobs keep their reference intact.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Audience</th>
                    <th className="px-3 py-2">Default format</th>
                    <th className="px-3 py-2 text-right">Sections</th>
                    <th className="px-3 py-2">Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTemplates.map((t) => (
                    <tr key={t.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2">{t.name}</td>
                      <td className="px-3 py-2">{t.template_type}</td>
                      <td className="px-3 py-2">{t.audience}</td>
                      <td className="px-3 py-2">{t.default_format}</td>
                      <td className="px-3 py-2 text-right">
                        {t.section_count}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge
                          label={t.enabled ? "Enabled" : "Disabled"}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Archive register */}
      {sortedArchive.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Archive register ({sortedArchive.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Long-term register of issued artefacts. Tags drive search across
              the PMO information store.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Format</th>
                    <th className="px-3 py-2 text-right">Month</th>
                    <th className="px-3 py-2 text-right">Size (MB)</th>
                    <th className="px-3 py-2">Tags</th>
                    <th className="px-3 py-2">Artifact</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedArchive.map((a) => (
                    <tr key={a.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-mono text-xs">{a.ref}</td>
                      <td className="px-3 py-2">{a.title}</td>
                      <td className="px-3 py-2">{a.format}</td>
                      <td className="px-3 py-2 text-right">
                        M{a.generated_month}
                      </td>
                      <td className="px-3 py-2 text-right">{a.size_mb}</td>
                      <td className="px-3 py-2 text-xs text-meridian-700">
                        {a.tags.length > 0 ? a.tags.join(", ") : "—"}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {a.artifact_url ? (
                          <a
                            className="text-meridian-700 underline"
                            href={a.artifact_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open
                          </a>
                        ) : (
                          <span className="text-meridian-500">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Template usage pressure heat-map */}
      {sortedPressure.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Template usage pressure
            </h2>
            <p className="text-xs text-meridian-600">
              Per-template authoring volume. Templates with recurring failures
              surface as a data-quality signal to the PMO.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Template</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Enabled</th>
                    <th className="px-3 py-2 text-right">Jobs</th>
                    <th className="px-3 py-2 text-right">Active</th>
                    <th className="px-3 py-2 text-right">Ready</th>
                    <th className="px-3 py-2 text-right">Failed</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedPressure.map((p) => (
                    <tr
                      key={p.template_id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2">{p.template_name}</td>
                      <td className="px-3 py-2">{p.template_type}</td>
                      <td className="px-3 py-2">
                        <StatusBadge
                          label={p.enabled ? "Enabled" : "Disabled"}
                        />
                      </td>
                      <td className="px-3 py-2 text-right">{p.job_count}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.active_count === 0 ? "text-meridian-900" : "text-amber-700"}`}
                      >
                        {p.active_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.ready_count > 0 ? "text-emerald-700" : "text-meridian-900"}`}
                      >
                        {p.ready_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.failed_count === 0 ? "text-meridian-900" : "text-rose-700"}`}
                      >
                        {p.failed_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {templates.length === 0 &&
      jobs.length === 0 &&
      archive.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No reporting data yet. Seed via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/reporting/templates
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
