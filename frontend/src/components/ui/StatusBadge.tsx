import { cn } from "@/lib/cn";

const PALETTE: Record<string, string> = {
  Active: "bg-emerald-100 text-emerald-800",
  Planned: "bg-sky-100 text-sky-800",
  "On Hold": "bg-amber-100 text-amber-800",
  Closed: "bg-zinc-200 text-zinc-700",
  Draft: "bg-zinc-100 text-zinc-700",
  Issued: "bg-sky-100 text-sky-800",
  Archived: "bg-zinc-200 text-zinc-700",
  Identified: "bg-sky-100 text-sky-800",
  Assessed: "bg-amber-100 text-amber-800",
  Mitigating: "bg-amber-100 text-amber-900",
  Monitoring: "bg-indigo-100 text-indigo-800",
  "Not Started": "bg-zinc-100 text-zinc-700",
  "In Progress": "bg-sky-100 text-sky-800",
  Completed: "bg-emerald-100 text-emerald-800",
};

// StatusBadge accepts either `value` (legacy) or `label` (newer module pages).
// Both forms render the same way; this is a backward-compatibility shim.
export function StatusBadge({ value, label }: { value?: string; label?: string }) {
  const text = label ?? value ?? "";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
        PALETTE[text] ?? "bg-zinc-100 text-zinc-700"
      )}
    >
      {text}
    </span>
  );
}
