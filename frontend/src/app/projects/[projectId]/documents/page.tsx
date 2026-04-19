"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Doc = { id: string; number: string; title: string; discipline: string; document_type: string; revision: string; suitability: string; workflow_status: string; cde_stage: string; owner: string; due_month: number; metadata_pct: number; source: string };
type Rev = { id: string; reviewer: string; role: string; status: string; due_month: number };
type Tx = { id: string; ref: string; recipient: string; document_count: number; issue_month: number; status: string };

export default function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [revs, setRevs] = useState<Rev[]>([]);
  const [txs, setTxs] = useState<Tx[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [d, r, t] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/documents`, { headers: H }).then(x => x.json()),
          fetch(`${BACKEND}/projects/${projectId}/documents/reviews`, { headers: H }).then(x => x.json()),
          fetch(`${BACKEND}/projects/${projectId}/documents/transmittals`, { headers: H }).then(x => x.json()),
        ]);
        if (!c) { setDocs(d); setRevs(r); setTxs(t); }
      } catch (e) { if (!c) setErr((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Document Control</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({err})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${docs.length} controlled documents`} subtitle="ISO 19650‑aligned CDE." />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Number</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Rev</th><th className="px-5 py-3">Suitability</th><th className="px-5 py-3">CDE</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Owner</th></tr>
            </thead>
            <tbody>{docs.map(d => (
              <tr key={d.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{d.number}</td><td className="px-5 py-3">{d.title}</td><td className="px-5 py-3">{d.document_type}</td><td className="px-5 py-3 font-mono">{d.revision}</td><td className="px-5 py-3">{d.suitability}</td><td className="px-5 py-3">{d.cde_stage}</td><td className="px-5 py-3"><StatusBadge value={d.workflow_status} /></td><td className="px-5 py-3">{d.owner}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${revs.length} reviews`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Reviewer</th><th className="px-5 py-3">Role</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Due</th></tr>
            </thead>
            <tbody>{revs.map(r => (
              <tr key={r.id} className="border-t border-meridian-100"><td className="px-5 py-3">{r.reviewer}</td><td className="px-5 py-3">{r.role}</td><td className="px-5 py-3"><StatusBadge value={r.status} /></td><td className="px-5 py-3">M{r.due_month}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${txs.length} transmittals`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Recipient</th><th className="px-5 py-3">Docs</th><th className="px-5 py-3">Issue M</th><th className="px-5 py-3">Status</th></tr>
            </thead>
            <tbody>{txs.map(t => (
              <tr key={t.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{t.ref}</td><td className="px-5 py-3">{t.recipient}</td><td className="px-5 py-3">{t.document_count}</td><td className="px-5 py-3">M{t.issue_month}</td><td className="px-5 py-3"><StatusBadge value={t.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
