"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Tmpl = { id: string; code?: string; name?: string; template_type?: string; format?: string; owner?: string };
type Job = { id: string; ref?: string; template_id?: string; status?: string; progress_pct?: number; requested_by?: string };

export default function ReportingPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [tmpls, setTmpls] = useState<Tmpl[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [t, j] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/reporting/templates`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/reporting/export-jobs`, { headers: H }).then(r => r.json()),
        ]);
        if (!c) { setTmpls(t); setJobs(j); }
      } catch (e) { if (!c) setErr((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Reporting & Export</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({err})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${tmpls.length} report templates`} subtitle="Catalogue of board/PMO/commercial/ORAT templates." />
        <CardBody className="p-0">
          {tmpls.length === 0 ? <p className="p-5 text-sm text-meridian-700">No templates yet. The backend’s reporting domain is wired; apply the expanded seed to populate.</p> : (
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Code</th><th className="px-5 py-3">Name</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Format</th><th className="px-5 py-3">Owner</th></tr></thead>
            <tbody>{tmpls.map(t => (
              <tr key={t.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{t.code ?? "—"}</td><td className="px-5 py-3">{t.name ?? "—"}</td><td className="px-5 py-3">{t.template_type ?? "—"}</td><td className="px-5 py-3">{t.format ?? "—"}</td><td className="px-5 py-3">{t.owner ?? "—"}</td></tr>
            ))}</tbody>
          </table>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${jobs.length} export jobs`} />
        <CardBody className="p-0">
          {jobs.length === 0 ? <p className="p-5 text-sm text-meridian-700">No export jobs. Trigger a template to render a PDF/XLSX export.</p> : (
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Progress</th><th className="px-5 py-3">Requested by</th></tr></thead>
            <tbody>{jobs.map(j => (
              <tr key={j.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{j.ref ?? "—"}</td><td className="px-5 py-3"><StatusBadge value={j.status ?? "—"} /></td><td className="px-5 py-3">{j.progress_pct ?? 0}%</td><td className="px-5 py-3">{j.requested_by ?? "—"}</td></tr>
            ))}</tbody>
          </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
