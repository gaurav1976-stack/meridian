import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { RiskHeatmap } from "@/components/ui/RiskHeatmap";
import { endpoints } from "@/lib/api/endpoints";
import type { Risk } from "@/lib/types";

function scoreColour(score: number): string {
  if (score >= 15) return "bg-rose-200 text-rose-900";
  if (score >= 9) return "bg-amber-200 text-amber-900";
  if (score >= 6) return "bg-yellow-100 text-yellow-900";
  return "bg-emerald-100 text-emerald-800";
}

export default async function ProjectRisksPage({
  params,
}: {
  params: { projectId: string };
}) {
  let risks: Risk[] = [];
  try {
    risks = await endpoints.listRisks(params.projectId);
  } catch {
    /* fall through */
  }

  const sorted = [...risks].sort((a, b) => b.residual_score - a.residual_score);

  // Stats
  const critical = risks.filter((r) => r.residual_score >= 15).length;
  const high = risks.filter((r) => r.residual_score >= 9 && r.residual_score < 15).length;
  const open = risks.filter((r) => r.status !== "Closed").length;

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-meridian-900">Risk Register</h1>
        <p className="text-sm text-meridian-600">
          5×5 matrix · cells ≥ 15 require Programme Director escalation
        </p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatTile label="Total risks" value={risks.length} />
        <StatTile label="Open" value={open} tone={open > 0 ? "warning" : "positive"} />
        <StatTile label="Critical (≥15)" value={critical} tone={critical > 0 ? "critical" : "positive"} />
        <StatTile label="High (9–14)" value={high} tone={high > 0 ? "warning" : "positive"} />
      </div>

      {/* Heatmap + top risks side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Risk Heatmap" subtitle="Residual likelihood × impact" />
          <CardBody>
            {risks.length > 0 ? (
              <RiskHeatmap
                risks={risks.map((r) => ({
                  likelihood: r.likelihood,
                  impact: r.impact,
                  code: r.code,
                  title: r.title,
                }))}
              />
            ) : (
              <p className="text-sm text-meridian-600">No risks to display.</p>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Top 5 Risks" subtitle="Sorted by residual score" />
          <CardBody className="p-0">
            <table className="w-full text-sm">
              <thead className="bg-meridian-50 text-left text-meridian-700">
                <tr>
                  <th className="px-4 py-3 font-medium">Code</th>
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Owner</th>
                </tr>
              </thead>
              <tbody>
                {sorted.slice(0, 5).map((r) => (
                  <tr key={r.id} className="border-t border-meridian-100">
                    <td className="px-4 py-3 font-mono text-xs">{r.code}</td>
                    <td className="px-4 py-3 text-xs">{r.title}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${scoreColour(r.residual_score)}`}
                      >
                        {r.residual_score}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">{r.owner ?? "—"}</td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-sm text-meridian-600">
                      No risks yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardBody>
        </Card>
      </div>

      {/* Full register */}
      <Card>
        <CardHeader
          title={`Full Register (${risks.length})`}
          subtitle="All risks sorted by residual score descending."
        />
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-meridian-50 text-left text-meridian-700">
                <tr>
                  <th className="px-5 py-3 font-medium">Code</th>
                  <th className="px-5 py-3 font-medium">Title</th>
                  <th className="px-5 py-3 font-medium">Category</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium text-center">L</th>
                  <th className="px-5 py-3 font-medium text-center">I</th>
                  <th className="px-5 py-3 font-medium text-center">Gross</th>
                  <th className="px-5 py-3 font-medium text-center">Residual</th>
                  <th className="px-5 py-3 font-medium">Owner</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((r) => (
                  <tr key={r.id} className="border-t border-meridian-100 hover:bg-meridian-50/60">
                    <td className="px-5 py-3 font-mono text-xs">{r.code}</td>
                    <td className="px-5 py-3">{r.title}</td>
                    <td className="px-5 py-3 text-xs">{r.category}</td>
                    <td className="px-5 py-3">
                      <StatusBadge value={r.status} />
                    </td>
                    <td className="px-5 py-3 text-center tabular-nums">{r.likelihood}</td>
                    <td className="px-5 py-3 text-center tabular-nums">{r.impact}</td>
                    <td className="px-5 py-3 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${scoreColour(r.gross_score)}`}>
                        {r.gross_score}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${scoreColour(r.residual_score)}`}>
                        {r.residual_score}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs">{r.owner ?? "—"}</td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-5 py-8 text-center text-sm text-meridian-600">
                      No risks yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "positive" | "warning" | "critical";
}) {
  const colour =
    tone === "critical"
      ? "text-rose-700"
      : tone === "warning"
      ? "text-amber-700"
      : tone === "positive"
      ? "text-emerald-700"
      : "text-meridian-900";
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-meridian-100 bg-white px-4 py-3">
      <span className="text-xs text-meridian-600">{label}</span>
      <span className={`text-2xl font-semibold tabular-nums ${colour}`}>{value}</span>
    </div>
  );
}
