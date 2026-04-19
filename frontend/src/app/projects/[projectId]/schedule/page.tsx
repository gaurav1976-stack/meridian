import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { GanttBar } from "@/components/ui/GanttBar";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { endpoints } from "@/lib/api/endpoints";
import type { ScheduleActivity } from "@/lib/types";

export default async function ProjectSchedulePage({
  params,
}: {
  params: { projectId: string };
}) {
  let activities: ScheduleActivity[] = [];
  try {
    activities = await endpoints.listActivities(params.projectId);
  } catch {
    /* fall through */
  }

  const critical = activities.filter((a) => a.is_critical);
  const inProgress = activities.filter((a) => a.status === "In Progress");
  const completed = activities.filter((a) => a.status === "Completed");
  const avgComplete =
    activities.length > 0
      ? Math.round(activities.reduce((s, a) => s + a.percent_complete, 0) / activities.length)
      : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-meridian-900">Schedule — Activities</h1>
        <p className="text-sm text-meridian-600">Activity-based logic network</p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatTile label="Total activities" value={activities.length} />
        <StatTile label="In progress" value={inProgress.length} tone="neutral" />
        <StatTile label="Completed" value={completed.length} tone="positive" />
        <StatTile
          label="Critical path"
          value={critical.length}
          tone={critical.length > 0 ? "critical" : "positive"}
        />
      </div>

      {/* Overall progress */}
      <Card>
        <CardHeader title="Overall Programme Progress" />
        <CardBody>
          <ProgressBar value={avgComplete} size="lg" label="Average % complete across all activities" />
        </CardBody>
      </Card>

      {/* Gantt chart */}
      <Card>
        <CardHeader
          title="Gantt View"
          subtitle="Critical path activities shown in red. Blue = normal. Today line in amber."
        />
        <CardBody>
          <GanttBar
            activities={activities.map((a) => ({
              id: a.id,
              name: a.name,
              start: a.planned_start,
              finish: a.planned_finish,
              percentComplete: a.percent_complete,
              isCritical: a.is_critical,
              status: a.status,
            }))}
          />
        </CardBody>
      </Card>

      {/* Activity table */}
      <Card>
        <CardHeader
          title={`${activities.length} activities`}
          subtitle="Critical path activities are flagged. Float = 0 days means no schedule buffer."
        />
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-meridian-50 text-left text-meridian-700">
                <tr>
                  <th className="px-5 py-3 font-medium">ID</th>
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Planned start</th>
                  <th className="px-5 py-3 font-medium">Planned finish</th>
                  <th className="px-5 py-3 font-medium w-36">Progress</th>
                  <th className="px-5 py-3 font-medium text-center">Float</th>
                  <th className="px-5 py-3 font-medium">Critical</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((a) => (
                  <tr
                    key={a.id}
                    className={`border-t border-meridian-100 hover:bg-meridian-50/60 ${
                      a.is_critical ? "bg-rose-50/30" : ""
                    }`}
                  >
                    <td className="px-5 py-3 font-mono text-xs">{a.activity_id_external}</td>
                    <td className="px-5 py-3 font-medium">{a.name}</td>
                    <td className="px-5 py-3">
                      <StatusBadge value={a.status} />
                    </td>
                    <td className="px-5 py-3 text-xs tabular-nums">{a.planned_start ?? "—"}</td>
                    <td className="px-5 py-3 text-xs tabular-nums">{a.planned_finish ?? "—"}</td>
                    <td className="px-5 py-3">
                      <ProgressBar
                        value={a.percent_complete}
                        showValue={true}
                        size="sm"
                        tone={a.is_critical ? "critical" : "auto"}
                      />
                    </td>
                    <td className="px-5 py-3 text-center tabular-nums text-xs">
                      {a.total_float_days !== null ? (
                        <span
                          className={
                            a.total_float_days === 0
                              ? "text-rose-700 font-semibold"
                              : a.total_float_days <= 5
                              ? "text-amber-700"
                              : "text-meridian-700"
                          }
                        >
                          {a.total_float_days}d
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {a.is_critical ? (
                        <span className="text-rose-700 text-xs font-semibold">CRITICAL</span>
                      ) : (
                        <span className="text-meridian-400 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {activities.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-5 py-8 text-center text-sm text-meridian-600">
                      No activities yet.
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
  tone?: "positive" | "warning" | "critical" | "neutral";
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
