"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const AUTH = "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw");
const H = { Authorization: AUTH };

type Cost = { id: string; package_id: string; budget_minor: number; committed_minor: number; forecast_minor: number; actual_minor: number; percent_complete: number };
type Change = { id: string; ref: string; title: string; change_type: string; status: string; cost_impact_minor: number; time_impact_weeks: number; owner: string };
type Notice = { id: string; ref: string; contract_ref: string; kind: string; due_days: number; status: string; owner: string };

const money = (n: number) => "$" + (n / 100).toLocaleString(undefined, { maximumFractionDigits: 0 });

export default function CommercialPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [costs, setCosts] = useState<Cost[]>([]);
  const [changes, setChanges] = useState<Change[]>([]);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [a, b, d] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/commercial/cost-controls`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/commercial/changes`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/commercial/notices`, { headers: H }).then(r => r.json()),
        ]);
        if (!c) { setCosts(a); setChanges(b); setNotices(d); }
      } catch (e) { if (!c) setError((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Commercial — Cost & Change</h1>
      {error ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({error})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${costs.length} package cost controls`} subtitle="Budget / committed / forecast / actual per work package." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Budget</th><th className="px-5 py-3">Committed</th><th className="px-5 py-3">Forecast</th><th className="px-5 py-3">Actual</th><th className="px-5 py-3">%</th></tr>
            </thead>
            <tbody>{costs.map(c => (
              <tr key={c.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono">{money(c.budget_minor)}</td><td className="px-5 py-3 font-mono">{money(c.committed_minor)}</td><td className="px-5 py-3 font-mono">{money(c.forecast_minor)}</td><td className="px-5 py-3 font-mono">{money(c.actual_minor)}</td><td className="px-5 py-3">{c.percent_complete}%</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${changes.length} change items (CE / VO / claim)`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Cost</th><th className="px-5 py-3">Weeks</th><th className="px-5 py-3">Owner</th></tr>
            </thead>
            <tbody>{changes.map(c => (
              <tr key={c.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{c.ref}</td><td className="px-5 py-3">{c.title}</td><td className="px-5 py-3">{c.change_type}</td><td className="px-5 py-3"><StatusBadge value={c.status} /></td><td className="px-5 py-3 font-mono">{money(c.cost_impact_minor)}</td><td className="px-5 py-3">{c.time_impact_weeks}</td><td className="px-5 py-3">{c.owner}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${notices.length} contract notices`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Contract</th><th className="px-5 py-3">Kind</th><th className="px-5 py-3">Due (d)</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Owner</th></tr>
            </thead>
            <tbody>{notices.map(n => (
              <tr key={n.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{n.ref}</td><td className="px-5 py-3 font-mono">{n.contract_ref}</td><td className="px-5 py-3">{n.kind}</td><td className="px-5 py-3">{n.due_days}</td><td className="px-5 py-3"><StatusBadge value={n.status} /></td><td className="px-5 py-3">{n.owner}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
