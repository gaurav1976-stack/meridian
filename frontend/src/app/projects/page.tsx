"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Project } from "@/lib/types";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH_HEADER = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects`, { headers: { Authorization: AUTH_HEADER } });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data: Project[] = await r.json();
        if (!cancelled) { setProjects(data); setLoading(false); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setLoading(false); }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-meridian-900">Projects</h1>
          <p className="text-sm text-meridian-700">
            All projects in your tenant. Drill into one to view the full workspace.
          </p>
        </div>
      </div>
      {error ? (
        <Card>
          <CardBody className="text-amber-700 text-sm">
            Backend unreachable. ({error})
          </CardBody>
        </Card>
      ) : null}
      <Card>
        <CardHeader title={loading ? "Loading…" : `${projects.length} project(s)`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id} className="border-t border-meridian-100 hover:bg-meridian-50/60">
                  <td className="px-5 py-3 font-mono text-xs">{p.code}</td>
                  <td className="px-5 py-3">
                    <Link href={`/projects/${p.id}`} className="text-meridian-700 hover:underline">
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3">{p.stage ?? "—"}</td>
                  <td className="px-5 py-3"><StatusBadge value={p.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
