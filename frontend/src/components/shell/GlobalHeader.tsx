import { Bell, User } from "lucide-react";
import type { MeResponse } from "@/lib/types";

export function GlobalHeader({ me }: { me: MeResponse | null }) {
  return (
    <header className="h-12 bg-white border-b border-meridian-100 flex items-center justify-between px-6 shrink-0">
      <div className="text-xs text-meridian-500 font-medium tracking-wide uppercase">
        Programme Management Information System
      </div>
      <div className="flex items-center gap-3">
        <button
          className="w-7 h-7 rounded-full flex items-center justify-center text-meridian-500 hover:bg-meridian-50 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-meridian-100 flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-meridian-700" />
          </div>
          {me ? (
            <div className="text-right hidden sm:block">
              <div className="text-xs font-medium text-meridian-900 leading-tight">{me.name}</div>
              <div className="text-[10px] text-meridian-500 leading-tight">{me.role}</div>
            </div>
          ) : (
            <div className="text-xs text-meridian-500">Guest</div>
          )}
        </div>
      </div>
    </header>
  );
}
