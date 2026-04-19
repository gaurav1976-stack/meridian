"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Mtg = { id: string; ref: string; title: string; meeting_type: string; month: number; chair: string; attendee_count: number; linked_module: string };
type Act = { id: string; ref: string; title: string; owner: string; priority: string; due_month: number; status: string; closure_evidence_pct: number };
type Comp = { id: string; ref: string; title: string; domain: string; owner: string; due_month: number; status: string; evidence_pct: number };

export default function MeetingsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [mtgs, setMtgs] = useState<Mtg[]>([]);
  const [acts, setActs] = useState<Act[]>([]);
  const [comp, setComp] = useState<Comp[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const [m, a, cp] = await Promise.all([
          fetch(`${BACKEND}/projects/${projectId}/meetings`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/meetings/actions`, { headers: H }).then(r => r.json()),
          fetch(`${BACKEND}/projects/${projectId}/meetings/compliance-items`, { headers: H }).then(r => r.json()),
        ]);
        if (!c) { setMtgs(m); setActs(a); setComp(cp); }
      } catch (e) { if (!c) setErr((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Meetings & Accountability</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">Backend unreachable. ({err})</CardBody></Card> : null}

      <Card>
        <CardHeader title={`${mtgs.length} meetings`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Month</th><th className="px-5 py-3">Chair</th><th className="px-5 py-3">Attendees</th></tr>
            </thead>
            <tbody>{mtgs.map(m => (
              <tr key={m.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{m.ref}</td><td className="px-5 py-3">{m.title}</td><td className="px-5 py-3">{m.meeting_type}</td><td className="px-5 py-3">M{m.month}</td><td className="px-5 py-3">{m.chair}</td><td className="px-5 py-3">{m.attendee_count}</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${acts.length} action items`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Priority</th><th className="px-5 py-3">Due</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">%</th></tr>
            </thead>
            <tbody>{acts.map(a => (
              <tr key={a.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{a.ref}</td><td className="px-5 py-3">{a.title}</td><td className="px-5 py-3">{a.owner}</td><td className="px-5 py-3">{a.priority}</td><td className="px-5 py-3">M{a.due_month}</td><td className="px-5 py-3"><StatusBadge value={a.status} /></td><td className="px-5 py-3">{a.closure_evidence_pct}%</td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${comp.length} compliance items`} />
        <CardBody className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700">
              <tr><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Domain</th><th className="px-5 py-3">Owner</th><th className="px-5 py-3">Due</th><th className="px-5 py-3">Status</th></tr>
            </thead>
            <tbody>{comp.map(c => (
              <tr key={c.id} className="border-t border-meridian-100"><td className="px-5 py-3 font-mono text-xs">{c.ref}</td><td className="px-5 py-3">{c.title}</td><td className="px-5 py-3">{c.domain}</td><td className="px-5 py-3">{c.owner}</td><td className="px-5 py-3">M{c.due_month}</td><td className="px-5 py-3"><StatusBadge value={c.status} /></td></tr>
            ))}</tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
