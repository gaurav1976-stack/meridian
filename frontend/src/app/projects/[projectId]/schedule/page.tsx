import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
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
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Schedule — Activities</h1>
      <Card>
        <CardHeader
          title={`${activities.length} activities`}
          subtitle="Activity-based logic network. Critical path activities are flagged."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">ID</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Planned start</th>
                <th className="px-5 py-3 font-medium">Planned finish</th>
                <th className="px-5 py-3 font-medium">% complete</th>
                <th className="px-5 py-3 font-medium">Float</th>
                <th className="px-5 py-3 font-medium">Critical</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => (
                <tr key={a.id} className="border-t border-meridian-100">
                  <td className="px-5 py-3 font-mono text-xs">{a.activity_id_external}</td>
                  <td className="px-5 py-3">{a.name}</td>
                  <td className="px-5 py-3">
                    <StatusBadge value={a.status} />
                  </td>
                  <td className="px-5 py-3">{a.planned_start ?? "—"}</td>
                  <td className="px-5 py-3">{a.planned_finish ?? "—"}</td>
                  <td className="px-5 py-3">{a.percent_complete}%</td>
                  <td className="px-5 py-3">{a.total_float_days ?? "—"}</td>
                  <td className="px-5 py-3">
                    {a.is_critical ? (
                      <span className="text-rose-700 text-xs font-semibold">CRITICAL</span>
                    ) : (
                      <span className="text-meridian-700 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
