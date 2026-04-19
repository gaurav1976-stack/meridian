"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH_HEADER = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");

type Dashboard = {
  project: { id: string; code: string; name: string; status: string; location?: string; stage?: string };
  counts: {
    work_packages: number;
    contracts: number;
    open_risks: number;
    schedule_activities: number;
    activities_critical: number;
  };
};

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const [data, setData] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects/${params.projectId}/dashboard`, {
          headers: { Authorization: AUTH_HEADER },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d: Dashboard = await r.json();
        if (!cancelled) { setData(d); setLoading(false); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setLoading(false); }
      }
    })();
    return () => { cancelled = true; };
  }, [params.projectId]);

  if (loading) return <div className="text-sm text-meridian-700">Loading project…</div>;
  if (error || !data) return (
    <Card><CardBody className="text-amber-700 text-sm">Could not load project. ({error ?? "no data"})</CardBody></Card>
  );

  const { project, counts } = data;

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
          subtitle="Use the sidebar to drill into each module."
        />
        <CardBody>
          <ul className="text-sm text-meridian-700 list-disc pl-5 space-y-1">
            <li>Schedule — see /projects/{project.id}/schedule</li>
            <li>Risks — see /projects/{project.id}/risks</li>
            <li>Stage Gates — see /projects/{project.id}/stage-gates</li>
          </ul>
        </CardBody>
      </Card>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: "amber" | "red" }) {
  const colour = tone === "red" ? "text-rose-700" : tone === "amber" ? "text-amber-700" : "text-meridian-900";
  return (
    <Card>
      <CardBody>
        <div className="text-xs text-meridian-700">{label}</div>
        <div className={`mt-1 text-2xl font-semibold ${colour}`}>{value}</div>
      </CardBody>
    </Card>
  );
}
