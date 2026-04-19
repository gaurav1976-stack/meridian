"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || "https://meridian-backend-0iy9.onrender.com";
const H = { Authorization: "Basic " + btoa("meridian-demo:uMISq6JJ-uvlYDMik-5NjPsFVsxR4GUqWomSAXRH4Tw") };

type Idx = { id: string; entity_type?: string; source?: string; title?: string; ref?: string; indexed_at?: string };

export default function SearchPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [idx, setIdx] = useState<Idx[]>([]);
  const [q, setQ] = useState("");
  // Use "unknown" so we accept whatever shape the backend returns.
  const [results, setResults] = useState<{ items?: unknown[]; total?: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/projects/${projectId}/search/index`, { headers: H });
        const data: Idx[] = await r.json();
        if (!c) setIdx(data);
      } catch (e) { if (!c) setErr((e as Error).message); }
    })();
    return () => { c = true; };
  }, [projectId]);

  async function runQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true); setErr(null);
    try {
      const r = await fetch(`${BACKEND}/projects/${projectId}/search/query?q=${encodeURIComponent(q)}`, { headers: H });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setResults(data);
    } catch (e) { setErr((e as Error).message); }
    finally { setLoading(false); }
  }

  const items = Array.isArray(results) ? results : (results?.items ?? []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-meridian-900">Enterprise Search</h1>
      {err ? <Card><CardBody className="text-amber-700 text-sm">{err}</CardBody></Card> : null}

      <Card>
        <CardHeader title="Query" subtitle="Hybrid keyword + semantic search across risks, activities, documents, gates." />
        <CardBody>
          <form onSubmit={runQuery} className="flex gap-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="e.g. piling, CAA, curtain wall, pile cap…"
              className="flex-1 rounded border border-meridian-200 px-3 py-2 text-sm"
            />
            <button type="submit" className="px-4 py-2 bg-meridian-900 text-white text-sm rounded hover:bg-meridian-800" disabled={loading}>
              {loading ? "Searching…" : "Search"}
            </button>
          </form>

          {results !== null ? (
            <div className="mt-4">
              <div className="text-xs text-meridian-700 mb-2">{items.length} result(s)</div>
              <ul className="space-y-2">
                {items.map((it: any, i: number) => (
                  <li key={i} className="border border-meridian-100 rounded p-3 text-sm">
                    <div className="font-medium">{it.title ?? it.name ?? it.ref ?? JSON.stringify(it).slice(0, 80)}</div>
                    {it.entity_type ? <div className="text-xs text-meridian-700 mt-1">{it.entity_type} · {it.source ?? "meridian"}</div> : null}
                    {it.snippet ? <div className="text-xs text-meridian-700 mt-1">{it.snippet}</div> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`${idx.length} indexed records`} subtitle="Per-entity index rows the search engine can resolve to." />
        <CardBody className="p-0">
          {idx.length === 0 ? <p className="p-5 text-sm text-meridian-700">No indexed rows yet. Apply the expanded seed and the indexer will back-fill.</p> : (
          <table className="w-full text-sm">
            <thead className="bg-meridian-50 text-left text-meridian-700"><tr><th className="px-5 py-3">Type</th><th className="px-5 py-3">Ref</th><th className="px-5 py-3">Title</th><th className="px-5 py-3">Source</th></tr></thead>
            <tbody>{idx.slice(0, 30).map(r => (
              <tr key={r.id} className="border-t border-meridian-100"><td className="px-5 py-3">{r.entity_type ?? "—"}</td><td className="px-5 py-3 font-mono text-xs">{r.ref ?? "—"}</td><td className="px-5 py-3">{r.title ?? "—"}</td><td className="px-5 py-3">{r.source ?? "—"}</td></tr>
            ))}</tbody>
          </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
