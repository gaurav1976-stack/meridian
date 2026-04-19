"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH_HEADER = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");

type Gate = {
  id: string; code: string; name: string; purpose: string;
  target_month: number; status: string;
};

export default function StageGatesPage() {
  const params = useParams<{ projectId: string }>();
  const [gates, setGates] = useState<Gate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects/${params.projectId}/stage-gates`, {
          headers: { Authorization: AUTH_HEADER },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data: Gate[] = await r.json();
        if (!cancelled) { setGates(data); setLoading(false); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setLoading(false); }
      }
    })();
    return () => { cancelled = true; };
  }, [params.projectId]);

  const sorted = [...gates].sort((a, b) => a.target_month - b.target_month);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Stage Gates</h1>
      {error ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({error})</CardBody></Card> : null}
      <Card>
        <CardHeader title={loading ? "Loading gates…" : `${gates.length} gates`} subtitle="Gate‑by‑gate readiness across the programme lifecycle." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Purpose</th>
                <th className="px-5 py-3 font-medium">Target month</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((g) => (
                <tr key={g.id} className="border-t border-meridian-100">
                  <td className="px-5 py-3 font-mono text-xs">{g.code}</td>
                  <td className="px-5 py-3 font-medium">{g.name}</td>
                  <td className="px-5 py-3 text-meridian-700">{g.purpose}</td>
                  <td className="px-5 py-3">M{g.target_month >= 0 ? "+" + g.target_month : g.target_month}</td>
                  <td className="px-5 py-3"><StatusBadge value={g.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
