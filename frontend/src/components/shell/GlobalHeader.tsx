import type { MeResponse } from "@/lib/types";

export function GlobalHeader({ me }: { me: MeResponse | null }) {
  return (
    <header className="h-14 bg-white border-b border-meridian-100 flex items-center justify-between px-6">
      <div className="text-sm text-meridian-700">
        <span className="font-medium">Programme Management Information System</span>
      </div>
      <div className="text-right text-sm">
        {me ? (
          <>
            <div className="font-medium text-meridian-900">{me.name}</div>
            <div className="text-xs text-meridian-700">{me.role}</div>
          </>
        ) : (
          <div className="text-xs text-meridian-700">Signed out</div>
        )}
      </div>
    </header>
  );
}
