"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Risk } from "@/lib/types";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH_HEADER = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");

function scoreColour(score: number): string {
  if (score >= 15) return "bg-rose-200 text-rose-900";
  if (score >= 9) return "bg-amber-200 text-amber-900";
  return "bg-emerald-100 text-emerald-800";
}

export default function ProjectRisksPage() {
  const params = useParams<{ projectId: string }>();
  const [risks, setRisks] = useState<Risk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects/${params.projectId}/risks`, {
          headers: { Authorization: AUTH_HEADER },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data: Risk[] = await r.json();
        if (!cancelled) { setRisks(data); setLoading(false); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setLoading(false); }
      }
    })();
    return () => { cancelled = true; };
  }, [params.projectId]);

  const top = [...risks].sort((a, b) => b.residual_score - a.residual_score).slice(0, 20);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Risk Register</h1>
      {error ? (
        <Card>
          <CardBody className="text-amber-700 text-sm">
            Backend unreachable. ({error})
          </CardBody>
        </Card>
      ) : null}
      <Card>
        <CardHeader
          title={loading ? "Loading risks…" : `${risks.length} risks`}
          subtitle="5×5 matrix; cells ≥ 12 require Programme Director escalation."
        />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Title</th>
                <th className="px-5 py-3 font-medium">Category</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">L</th>
                <th className="px-5 py-3 font-medium">I</th>
                <th className="px-5 py-3 font-medium">Score</th>
                <th className="px-5 py-3 font-medium">Owner</th>
              </tr>
            </thead>
            <tbody>
              {top.map((r) => (
                <tr key={r.id} className="border-t border-meridian-100">
                  <td className="px-5 py-3 font-mono text-xs">{r.code}</td>
                  <td className="px-5 py-3">{r.title}</td>
                  <td className="px-5 py-3">{r.category}</td>
                  <td className="px-5 py-3">
                    <StatusBadge value={r.status} />
                  </td>
                  <td className="px-5 py-3">{r.likelihood}</td>
                  <td className="px-5 py-3">{r.impact}</td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${scoreColour(
                        r.residual_score
                      )}`}
                    >
                      {r.residual_score}
                    </span>
                  </td>
                  <td className="px-5 py-3">{r.owner ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
