// Enterprise Search & Retrieval — index register, saved searches, connector
// references, project rollup and per-source connector health heat-map. Server-
// rendered; backend provides the rollup (record / saved search / connector
// counts, indexed vs stale, type & source histograms) and the per-source
// pressure breakdown. Pattern mirrors reporting/page.tsx.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";
import type {
  ConnectorReference,
  ConnectorSourcePressure,
  SavedSearch,
  SearchIndexRecord,
  SearchSummary,
} from "@/lib/types";

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

export default async function ProjectSearchPage({
  params,
}: {
  params: { projectId: string };
}) {
  let summary: SearchSummary | null = null;
  let records: SearchIndexRecord[] = [];
  let savedSearches: SavedSearch[] = [];
  let connectors: ConnectorReference[] = [];
  let pressure: ConnectorSourcePressure[] = [];

  try {
    [summary, records, savedSearches, connectors, pressure] =
      await Promise.all([
        endpoints.searchSummary(params.projectId),
        endpoints.listSearchIndex(params.projectId),
        endpoints.listSavedSearches(params.projectId),
        endpoints.listConnectorReferences(params.projectId),
        endpoints.connectorSourcePressure(params.projectId),
      ]);
  } catch {
    /* fall through — render empty state */
  }

  if (!summary) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-meridian-900">
          Enterprise Search & Retrieval
        </h1>
        <p className="mt-3 text-meridian-700">
          Unable to load search data for this project. Check that the backend is
          running and the project exists.
        </p>
      </div>
    );
  }

  // Index records — newest first by updated_at.
  const sortedRecords = [...records].sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at)
  );

  // Saved searches — alphabetical by name.
  const sortedSavedSearches = [...savedSearches].sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  // Connectors — failed first, then stale, then pending, then indexed.
  const statusOrder: Record<string, number> = {
    Failed: 0,
    Stale: 1,
    Pending: 2,
    Indexed: 3,
  };
  const sortedConnectors = [...connectors].sort((a, b) => {
    const oa = statusOrder[a.sync_status] ?? 99;
    const ob = statusOrder[b.sync_status] ?? 99;
    if (oa !== ob) return oa - ob;
    return a.external_ref.localeCompare(b.external_ref);
  });

  // Pressure heat-map — failed first, then stale, then total.
  const sortedPressure = [...pressure].sort((a, b) => {
    if (b.failed_count !== a.failed_count) {
      return b.failed_count - a.failed_count;
    }
    if (b.stale_count !== a.stale_count) {
      return b.stale_count - a.stale_count;
    }
    return b.total_count - a.total_count;
  });

  // Type / source histograms — render as sorted entries (descending).
  const typeEntries = Object.entries(summary.records_by_type).sort(
    (a, b) => b[1] - a[1]
  );
  const sourceEntries = Object.entries(summary.records_by_source).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-meridian-900">
            Enterprise Search & Retrieval
          </h1>
          <p className="text-sm text-meridian-700">
            Cross-module search index, saved query register, connector reference
            health and project-wide retrieval rollup — the entry point for the
            PMO information store.
          </p>
        </div>
      </header>

      {/* Search rollup */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-meridian-900">
            Search rollup
          </h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile
              label="Indexed records"
              value={summary.indexed_record_count}
              tone={
                summary.indexed_record_count > 0 ? "positive" : "default"
              }
            />
            <KpiTile
              label="Saved searches"
              value={summary.saved_search_count}
            />
            <KpiTile
              label="Connector references"
              value={summary.connector_reference_count}
            />
            <KpiTile
              label="Indexed connectors"
              value={summary.indexed_connector_count}
              tone={
                summary.indexed_connector_count > 0
                  ? "positive"
                  : "default"
              }
              hint="Current and searchable"
            />
            <KpiTile
              label="Stale / failed"
              value={summary.stale_connector_count}
              tone={
                summary.stale_connector_count === 0 ? "positive" : "critical"
              }
              hint="Re-ingestion candidates"
            />
          </div>
        </CardBody>
      </Card>

      {/* Type + source histograms */}
      {typeEntries.length > 0 || sourceEntries.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {typeEntries.length > 0 ? (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-meridian-900">
                  Records by entity type
                </h2>
                <p className="text-xs text-meridian-600">
                  Distribution of the index across the eleven entity types the
                  PMO catalogues.
                </p>
              </CardHeader>
              <CardBody>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                      <tr>
                        <th className="px-3 py-2">Entity type</th>
                        <th className="px-3 py-2 text-right">Records</th>
                      </tr>
                    </thead>
                    <tbody>
                      {typeEntries.map(([type, count]) => (
                        <tr
                          key={type}
                          className="border-t border-meridian-100"
                        >
                          <td className="px-3 py-2">{type}</td>
                          <td className="px-3 py-2 text-right font-medium">
                            {count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          ) : null}

          {sourceEntries.length > 0 ? (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-meridian-900">
                  Records by source
                </h2>
                <p className="text-xs text-meridian-600">
                  Origin system breakdown — Meridian-native versus external
                  connectors (BIM360, SharePoint, Teams).
                </p>
              </CardHeader>
              <CardBody>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                      <tr>
                        <th className="px-3 py-2">Source</th>
                        <th className="px-3 py-2 text-right">Records</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sourceEntries.map(([source, count]) => (
                        <tr
                          key={source}
                          className="border-t border-meridian-100"
                        >
                          <td className="px-3 py-2">{source}</td>
                          <td className="px-3 py-2 text-right font-medium">
                            {count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          ) : null}
        </div>
      ) : null}

      {/* Connector pressure heat-map */}
      {sortedPressure.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Connector source pressure
            </h2>
            <p className="text-xs text-meridian-600">
              Per-source health. Sources with a high stale or failed count
              surface as a data-quality signal — either the connector has broken
              or the ingestion cadence needs to be raised.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2 text-right">Total</th>
                    <th className="px-3 py-2 text-right">Indexed</th>
                    <th className="px-3 py-2 text-right">Pending</th>
                    <th className="px-3 py-2 text-right">Stale</th>
                    <th className="px-3 py-2 text-right">Failed</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedPressure.map((p) => (
                    <tr key={p.source} className="border-t border-meridian-100">
                      <td className="px-3 py-2 font-medium">{p.source}</td>
                      <td className="px-3 py-2 text-right">{p.total_count}</td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.indexed_count > 0 ? "text-emerald-700" : "text-meridian-900"}`}
                      >
                        {p.indexed_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.pending_count === 0 ? "text-meridian-900" : "text-amber-700"}`}
                      >
                        {p.pending_count}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-medium ${p.stale_count === 0 ? "text-meridian-900" : "text-amber-700"}`}
                      >
                        {p.stale_count}
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

      {/* Connector references */}
      {sortedConnectors.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Connector references ({sortedConnectors.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Failed and stale references surface first — these are the
              re-ingestion priorities for the data team.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">External ref</th>
                    <th className="px-3 py-2">Path</th>
                    <th className="px-3 py-2">Sync status</th>
                    <th className="px-3 py-2">Index link</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedConnectors.map((c) => (
                    <tr key={c.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2">{c.source}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {c.external_ref}
                      </td>
                      <td className="px-3 py-2 text-xs text-meridian-700">
                        {c.path}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge label={c.sync_status} />
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {c.index_record_id ? (
                          <span className="font-mono text-meridian-700">
                            {c.index_record_id.slice(0, 8)}…
                          </span>
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

      {/* Saved searches */}
      {sortedSavedSearches.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Saved searches ({sortedSavedSearches.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Per-user query register. Scoped queries replay the same filter
              context across the project.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">Owner</th>
                    <th className="px-3 py-2">Query</th>
                    <th className="px-3 py-2">Scope</th>
                    <th className="px-3 py-2">Filters</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedSavedSearches.map((s) => {
                    const filters = [
                      s.type_filter ? `type:${s.type_filter}` : null,
                      s.source_filter ? `source:${s.source_filter}` : null,
                      s.package_filter ? `pkg:${s.package_filter}` : null,
                    ]
                      .filter((x): x is string => x !== null)
                      .join(" · ");
                    return (
                      <tr key={s.id} className="border-t border-meridian-100">
                        <td className="px-3 py-2 font-medium">{s.name}</td>
                        <td className="px-3 py-2 text-xs">{s.user_email}</td>
                        <td className="px-3 py-2 text-xs">
                          <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                            {s.query_text}
                          </code>
                        </td>
                        <td className="px-3 py-2">
                          <StatusBadge label={s.scope} />
                        </td>
                        <td className="px-3 py-2 text-xs text-meridian-700">
                          {filters || "—"}
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

      {/* Index register */}
      {sortedRecords.length > 0 ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-meridian-900">
              Index register ({sortedRecords.length})
            </h2>
            <p className="text-xs text-meridian-600">
              Most recently updated records first. Tags drive cross-module
              retrieval; permission scope governs visibility.
            </p>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-meridian-50 text-left text-xs uppercase tracking-wide text-meridian-700">
                  <tr>
                    <th className="px-3 py-2">Title</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Group</th>
                    <th className="px-3 py-2">Package</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Tags</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRecords.map((r) => (
                    <tr key={r.id} className="border-t border-meridian-100">
                      <td className="px-3 py-2">
                        <div className="font-medium">{r.title}</div>
                        <div className="font-mono text-xs text-meridian-600">
                          {r.entity_ref}
                        </div>
                      </td>
                      <td className="px-3 py-2">{r.entity_type}</td>
                      <td className="px-3 py-2">{r.source}</td>
                      <td className="px-3 py-2">{r.group_name}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {r.package_code ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {r.status_text ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-xs text-meridian-700">
                        {r.tags.length > 0 ? r.tags.join(", ") : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      ) : null}

      {records.length === 0 &&
      savedSearches.length === 0 &&
      connectors.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-sm text-meridian-700">
              No search data yet. Seed via the API at{" "}
              <code className="rounded bg-meridian-50 px-1 py-0.5 font-mono text-xs">
                POST /projects/{params.projectId}/search/index
              </code>
              .
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
