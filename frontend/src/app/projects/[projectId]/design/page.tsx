"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Pkg = { id: string; code: string; name: string; lead_discipline: string; stage: string; maturity_pct: number; status: string; freeze_planned_month: number; freeze_current_month: number };
type Del = { id: string; ref: string; title: string; discipline: string; deliverable_type: string; stage: string; due_month: number; status: string; owner: string };
type Iface = { id: string; ref: string; title: string; owner: string; severity: number; status: string; due_month: number };

export default function DesignPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [pkgs, setPkgs] = useState<Pkg[]>([]);
  const [dels, setDels] = useState<Del[]>([]);
  const [ifaces, setIfaces] = useState<Iface[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [p, d, i] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/design/design-packages`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/design/deliverables`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/design/interfaces`, { headers: H }).then(r => r.json()),
        ]);
        if (!c) { setPkgs(p); setDels(d); setIfaces(i); }
      } catch (e) { if (!c) setErr((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Design Management</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({err})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${pkgs.length} design packages`} subtitle="RIBA‑stage design packages with maturity and freeze variance." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Code</th><th className="px-5 py-3">Name</th><th className="px-5 py-3">Discipline</th><th className="px-5 py-3">Stage</th><th className="px-5 py-3">Maturity</th><th className="px-5 py-3">Freeze (plan/now)</th><th className="px-5 py-3">Status</th></tr>
            </thead>
            <tbody>{pkgs.map(p => (
              <tr key={p.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{p.code}</td><td className="px-5 py-3">{p.name}</td><td className="px-5 py-3">{p.lead_discipline}</td><td className="px-5 py-3">{p.stage}</td><td className="px-5 py-3">{p.maturity_pct}%</td><td className="px-5 py-3">M{p.freeze_planned_month} / M{p.freeze_current_month}</td><td className="px-5 py-3"><StatusBadge value={p.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${dels.length} deliverables`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Due</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Owner</th></tr>
            </thead>
            <tbody>{dels.map(d => (
              <tr key={d.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{d.ref}</td><td className="px-5 py-3">{d.title}</td><td className="px-5 py-3">{d.deliverable_type}</td><td className="px-5 py-3">M{d.due_month}</td><td className="px-5 py-3"><StatusBadge value={d.status} /></td><td className="px-5 py-3">{d.owner}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${ifaces.length} interfaces`} subtitle="Cross‑discipline coordination items." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Severity</th><th className="px-5 py-3">Due</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Owner</th></tr>
            </thead>
            <tbody>{ifaces.map(i => (
              <tr key={i.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{i.ref}</td><td className="px-5 py-3">{i.title}</td><td className="px-5 py-3">{i.severity}</td><td className="px-5 py-3">M{i.due_month}</td><td className="px-5 py-3"><StatusBadge value={i.status} /></td><td className="px-5 py-3">{i.owner}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
