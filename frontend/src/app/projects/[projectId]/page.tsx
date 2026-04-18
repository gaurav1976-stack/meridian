import { notFound } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { endpoints } from "@/lib/api/endpoints";

export default async function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  let dashboard;
  try {
    dashboard = await endpoints.projectDashboard(params.projectId);
  } catch {
    notFound();
  }
  if (!dashboard) notFound();
  const { project, counts } = dashboard;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs text-meridian-700 font-mono">{project.code}</div>
        <h1 className="text-xl font-semibold text-meridian-900">{project.name}</h1>
        <div className="mt-1 text-sm text-meridian-700 flex items-center gap-3">
          <StatusBadge value={project.status} />
          <span>{project.location ?? "—"}</span>
          <span>•</span>
          <span>{project.stage ?? "Stage TBD"}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Stat label="Work Packages" value={counts.work_packages} />
        <Stat label="Contracts" value={counts.contracts} />
        <Stat label="Open Risks" value={counts.open_risks} tone={counts.open_risks > 5 ? "amber" : undefined} />
        <Stat label="Activities" value={counts.schedule_activities} />
        <Stat
          label="Critical Activities"
          value={counts.activities_critical}
          tone={counts.activities_critical > 0 ? "red" : undefined}
        />
      </div>

      <Card>
        <CardHeader
          title="Workspace"
          subtitle="Reference modules wired to the backend below. Other modules surfaced via the sidebar will activate as their domains are ported."
        />
        <CardBody>
          <ul className="text-sm text-meridian-700 list-disc pl-5 space-y-1">
            <li>Schedule — see /projects/{project.id}/schedule</li>
            <li>Risks — see /projects/{project.id}/risks</li>
          </ul>
        </CardBody>
      </Card>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "amber" | "red";
}) {
  const colour =
    tone === "red"
      ? "text-rose-700"
      : tone === "amber"
      ? "text-amber-700"
      : "text-meridian-900";
  return (
    <Card>
      <CardBody>
        <div className="text-xs text-meridian-700">{label}</div>
        <div className={`mt-1 text-2xl font-semibold ${colour}`}>{value}</div>
      </CardBody>
    </Card>
  );
}
