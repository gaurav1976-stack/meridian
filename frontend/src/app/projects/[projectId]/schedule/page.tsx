"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { ScheduleActivity } from "@/lib/types";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH_HEADER = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");

export default function ProjectSchedulePage() {
  const params = useParams<{ projectId: string }>();
  const [activities, setActivities] = useState<ScheduleActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects/${params.projectId}/schedule/activities`, {
          headers: { Authorization: AUTH_HEADER },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data: ScheduleActivity[] = await r.json();
        if (!cancelled) { setActivities(data); setLoading(false); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setLoading(false); }
      }
    })();
    return () => { cancelled = true; };
  }, [params.projectId]);

  const critical = activities.filter(a => a.is_critical).length;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Schedule — Activities</h1>
      {error ? (
        <Card>
          <CardBody className="text-amber-700 text-sm">
            Backend unreachable. ({error})
          </CardBody>
        </Card>
      ) : null}
      <Card>
        <CardHeader
          title={loading ? "Loading activities…" : `${activities.length} activities — ${critical} critical`}
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
                  <td className="px-5 py-3"><StatusBadge value={a.status} /></td>
                  <td className="px-5 py-3">{a.planned_start ?? "—"}</td>
                  <td className="px-5 py-3">{a.planned_finish ?? "—"}</td>
                  <td className="px-5 py-3">{a.percent_complete}%</td>
                  <td className="px-5 py-3">{a.total_float_days ?? "—"}</td>
                  <td className="px-5 py-3">{a.is_critical ? <span className="text-rose-700 text-xs font-semibold">CRITICAL</span> : <span className="text-meridian-700 text-xs">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
