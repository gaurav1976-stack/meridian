// Document Control — ISO 19650-aligned controlled documents, review workflow,
// transmittal register, and repository linking. Rendered server-side; backend
// computes metadata completeness, overdue counts, and sync-issue rollups.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  ControlledDocument,
  DocumentControlSummary,
  DocumentReview,
  RepositoryLink,
  TransmittalRecord,
} from "@/lib/types";

function metadataColour(pct: number): string {
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

export default async function ProjectDocumentsPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: DocumentControlSummary | null = null;
  let documents: ControlledDocument[] = [];
  let reviews: DocumentReview[] = [];
  let transmittals: TransmittalRecord[] = [];
  let links: RepositoryLink[] = [];

  try {
    [summary, documents, reviews, transmittals, links] = await Promise.all([
      endpoints.documentControlSummary(params.projectId),
      endpoints.listDocuments(params.projectId),
      endpoints.listDocumentReviews(params.projectId),
      endpoints.listTransmittals(params.projectId),
      endpoints.listRepositoryLinks(params.projectId),
    ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-meridian-900">
          Document Control
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load document control data for this project. Check that the
          backend is running and the project exists.
        </p>
      </div>
    );
  }

  const overdueDocuments = documents
    .filter((d) => d.workflow_status === "Overdue")
    .sort((a, b) => a.due_month - b.due_month);

  const openReviews = reviews
    .filter((r) => r.status === "Pending" || r.status === "In Review")
    .sort((a, b) => a.due_month - b.due_month);

  const sortedTransmittals = [...transmittals].sort(
    (a, b) => b.issue_month - a.issue_month
  );

  const syncIssues = links.filter((l) => l.sync_status !== "Linked");

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            Document Control
          </h1>
          <p className="text-sm text-meridian-700">
            ISO 19650-aligned document register — workflow state, review
            actions, transmittal issuance, and repository linking.
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
              label="Documents"
              value={summary.document_count}
            />
            <KpiTile
              label="Avg metadata"
              value={`${summary.average_metadata_pct}%`}
              tone={
                summary.average_metadata_pct >= 80
                  ? "positive"
                  : summary.average_metadata_pct >= 50
                    ? "warning"
                    : "critical"
              }
              hint="ISO 19650 completeness"
            />
            <KpiTile
              label="Published"
              value={summary.published_document_count}
              hint="CDE — Published stage"
            />
            <KpiTile
              label="Overdue"
              value={summary.overdue_document_count}
              tone={
                summary.overdue_document_count === 0 ? "positive" : "critical"
              }
            />
            <KpiTile
              label="Pending reviews"
              value={summary.pending_review_count}
              tone={
                summary.pending_review_count === 0 ? "positive" : "warning"
              }
            />
            <KpiTile
              label="Transmittals"
              value={summary.transmittal_count}
            />
            <KpiTile
              label="Issued transmittals"
              value={summary.issued_transmittal_count}
              hint="Awaiting acknowledgement"
            />
            <KpiTile
              label="Sync issues"
              value={summary.sync_issue_count}
              tone={summary.sync_issue_count === 0 ? "positive" : "critical"}
              hint="Repository drift"
            />
          </div>
        </CardBody>
      </Card>

      {/* Overdue documents */}
      {overdueDocuments.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Overdue documents
            </h2>
            <p className="text-xs text-meridian-600">
              Documents flagged overdue in the workflow; contractual SLA is at
              risk.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Number</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Discipline</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Rev</th>
                    <th className="px-3 py-2">Suitability</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {overdueDocuments.map((d) => (
                    <tr
                      key={d.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.number}
                      </td>
                      <td className="px-3 py-2">{d.title}</td>
                      <td className="px-3 py-2">{d.discipline}</td>
                      <td className="px-3 py-2">{d.document_type}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.revision}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.suitability}
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

      {/* Pending reviews */}
      {openReviews.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Pending reviews
            </h2>
            <p className="text-xs text-meridian-600">
              Reviews open against controlled documents, ordered by due month.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Reviewer</th>
                    <th className="px-3 py-2">Role</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Due</th>
                  </tr>
                </thead>
                <tbody>
                  {openReviews.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2">{r.reviewer}</td>
                      <td className="px-3 py-2">{r.role}</td>
                      <td className="px-3 py-2">
                        <StatusBadge label={r.status} />
                      </td>
                      <td className="px-3 py-2 text-right">M{r.due_month}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Transmittal register */}
      {sortedTransmittals.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Transmittal register
            </h2>
            <p className="text-xs text-meridian-600">
              Formal issuance of document bundles to external parties, most
              recent first.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Ref</th>
                    <th className="px-3 py-2">Recipient</th>
                    <th className="px-3 py-2 text-right">Docs</th>
                    <th className="px-3 py-2 text-right">Issued</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTransmittals.map((t) => (
                    <tr
                      key={t.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{t.ref}</td>
                      <td className="px-3 py-2">{t.recipient}</td>
                      <td className="px-3 py-2 text-right">
                        {t.document_count}
                      </td>
                      <td className="px-3 py-2 text-right">
                        M{t.issue_month}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={t.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* Repository links */}
      {links.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Repository links
            </h2>
            <p className="text-xs text-meridian-600">
              Links from controlled documents to source repositories (BIM360,
              SharePoint, Meridian CDE). Sync drift highlighted.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Repository</th>
                    <th className="px-3 py-2">Path</th>
                    <th className="px-3 py-2">Sync status</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Sync issues first, then linked */}
                  {[...syncIssues, ...links.filter((l) => l.sync_status === "Linked")].map(
                    (l) => (
                      <tr
                        key={l.id}
                        className="border-t border-meridian-100"
                      >
                        <td className="px-3 py-2">{l.repository}</td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {l.path}
                        </td>
                        <td className="px-3 py-2">
                          <StatusBadge label={l.sync_status} />
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {/* All documents */}
      {documents.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Controlled documents ({documents.length})
            </h2>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Number</th>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Discipline</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Rev</th>
                    <th className="px-3 py-2">Suitability</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">CDE</th>
                    <th className="px-3 py-2 text-right">Metadata</th>
                    <th className="px-3 py-2 text-right">Due</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((d) => (
                    <tr
                      key={d.id}
                      className="border-t border-meridian-100"
                    >
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.number}
                      </td>
                      <td className="px-3 py-2">{d.title}</td>
                      <td className="px-3 py-2">{d.discipline}</td>
                      <td className="px-3 py-2">{d.document_type}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.revision}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {d.suitability}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={d.workflow_status} />
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={d.cde_stage} />
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${metadataColour(d.metadata_pct)}`}
                      >
                        {d.metadata_pct}%
                      </td>
                      <td className="px-3 py-2 text-right">M{d.due_month}</td>
                      <td className="px-3 py-2">{d.source}</td>
                      <td className="px-3 py-2">{d.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {documents.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No controlled documents yet. Add one via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/documents
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
