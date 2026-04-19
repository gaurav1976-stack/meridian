"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Ws = { id: string; name: string; owner: string; progress_pct: number; status: string; due_month: number };
type Tr = { id: string; ref: string; title: string; month: number; participants: number; status: string; observations: string };
type Tg = { id: string; function_name: string; target_headcount: number; trained_headcount: number; status: string; owner: string };
type Ho = { id: string; ref: string; asset_group: string; status: string; evidence_pct: number; owner: string };

export default function OratPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [ws, setWs] = useState<Ws[]>([]);
  const [tr, setTr] = useState<Tr[]>([]);
  const [tg, setTg] = useState<Tg[]>([]);
  const [ho, setHo] = useState<Ho[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [a, b, d, e] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/orat/workstreams`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/orat/trials`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/orat/training-groups`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/orat/handover-items`, { headers: H }).then(r => r.json()),
        ]);
        if (!c) { setWs(a); setTr(b); setTg(d); setHo(e); }
      } catch (e2) { if (!c) setErr((e2 as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">ORAT Readiness & Handover</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({err})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${ws.length} workstreams`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Name</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Progress</th><th className="px-5 py-3">Due M</th><th className="px-5 py-3">Status</th></tr></thead>
            <tbody>{ws.map(w => (
              <tr key={w.id} className="border-t border-meridian-100"><td className="px-5 py-3">{w.name}</td><td className="px-5 py-3">{w.owner}</td><td className="px-5 py-3">{w.progress_pct}%</td><td className="px-5 py-3">M{w.due_month}</td><td className="px-5 py-3"><StatusBadge value={w.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${tr.length} trials`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Month</th><th className="px-5 py-3">Participants</th><th className="px-5 py-3">Status</th></tr></thead>
            <tbody>{tr.map(t => (
              <tr key={t.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{t.ref}</td><td className="px-5 py-3">{t.title}</td><td className="px-5 py-3">M{t.month}</td><td className="px-5 py-3">{t.participants}</td><td className="px-5 py-3"><StatusBadge value={t.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${tg.length} training groups`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Function</th><th className="px-5 py-3">Trained / Target</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Status</th></tr></thead>
            <tbody>{tg.map(g => (
              <tr key={g.id} className="border-t border-meridian-100"><td className="px-5 py-3">{g.function_name}</td><td className="px-5 py-3">{g.trained_headcount} / {g.target_headcount}</td><td className="px-5 py-3">{g.owner}</td><td className="px-5 py-3"><StatusBadge value={g.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${ho.length} handover items`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Asset group</th><th className="px-5 py-3">Evidence</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Status</th></tr></thead>
            <tbody>{ho.map(h => (
              <tr key={h.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{h.ref}</td><td className="px-5 py-3">{h.asset_group}</td><td className="px-5 py-3">{h.evidence_pct}%</td><td className="px-5 py-3">{h.owner}</td><td className="px-5 py-3"><StatusBadge value={h.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
