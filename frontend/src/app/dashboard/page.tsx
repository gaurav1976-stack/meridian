"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Project } from "@/lib/types";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";

// Basic Auth pass-through for the pilot demo. The frontend edge middleware
// already validated the user at the frontend origin; re-use the same shared
// secret to unlock the backend origin for cross-origin fetches.
const BASIC_AUTH_USER = process.env.NEXT_PUBLIC_BASIC_AUTH_USER || "meridian-demo";
const BASIC_AUTH_PW = process.env.NEXT_PUBLIC_BASIC_AUTH_PW || "uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw";
const AUTH_HEADER = "Basic " + btoa(`${BASIC_AUTH_USER}:${BASIC_AUTH_PW}`);

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects`, {
          headers: { Authorization: AUTH_HEADER },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data: Project[] = await r.json();
        if (!cancelled) {
          setProjects(data);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError((e as Error).message);
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const active = projects.filter((p) => p.status === "Active").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-meridian-900">Programme Dashboard</h1>
        <p className="text-sm text-meridian-700">
          High-level health across active airport programmes.
        </p>
      </div>

      {error ? (
        <Card>
          <CardBody className="text-amber-700 text-sm">
            Backend unreachable. ({error})
          </CardBody>
        </Card>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader title="Total projects" />
          <CardBody className="text-3xl font-semibold text-meridian-900">
            {loading ? "…" : projects.length}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Active" />
          <CardBody className="text-3xl font-semibold text-emerald-700">
            {loading ? "…" : active}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Stage Gate Status" subtitle="Pending wiring to governance module" />
          <CardBody className="text-sm text-meridian-700">
            See conversion playbook §A — governance domain not yet ported.
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Projects" subtitle="Click a row to open the project workspace." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr>
                <th className="px-5 py-3 font-medium">Code</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Location</th>
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td className="px-5 py-6 text-meridian-700" colSpan={5}>
                    Loading projects…
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td className="px-5 py-6 text-meridian-700" colSpan={5}>
                    No projects yet.
                  </td>
                </tr>
              ) : (
                projects.map((p) => (
                  <tr key={p.id} className="border-t border-meridian-100 hover:bg-meridian-50/60">
                    <td className="px-5 py-3 font-mono text-xs">{p.code}</td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/projects/${p.id}`}
                        className="text-meridian-700 hover:underline"
                      >
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-5 py-3">{p.location ?? "—"}</td>
                    <td className="px-5 py-3">{p.stage ?? "—"}</td>
                    <td className="px-5 py-3">
                      <StatusBadge value={p.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
