"use client";

/**
 * Lightweight Gantt-style bar chart for schedule activities.
 * Pure SVG — no charting library required.
 */

interface GanttActivity {
  id: string;
  name: string;
  start: string | null; // ISO date
  finish: string | null; // ISO date
  percentComplete: number;
  isCritical: boolean | null;
  status: string;
}

interface GanttBarProps {
  activities: GanttActivity[];
  maxRows?: number;
}

const ROW_H = 28;
const LABEL_W = 180;
const BAR_H = 14;
const PAD_TOP = 24; // space for date axis
const PAD_BOTTOM = 8;

function parseDate(s: string | null): Date | null {
  if (!s) return null;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / 86_400_000);
}

export function GanttBar({ activities, maxRows = 20 }: GanttBarProps) {
  const rows = activities.slice(0, maxRows);

  // Determine date range
  const allDates: Date[] = [];
  for (const a of rows) {
    const s = parseDate(a.start);
    const f = parseDate(a.finish);
    if (s) allDates.push(s);
    if (f) allDates.push(f);
  }

  if (allDates.length === 0) {
    return (
      <p className="text-sm text-meridian-600 py-4">
        No date information available for Gantt view.
      </p>
    );
  }

  const minDate = new Date(Math.min(...allDates.map((d) => d.getTime())));
  const maxDate = new Date(Math.max(...allDates.map((d) => d.getTime())));
  // Add a small buffer
  minDate.setDate(minDate.getDate() - 7);
  maxDate.setDate(maxDate.getDate() + 7);

  const totalDays = daysBetween(minDate, maxDate) || 1;
  const CHART_W = 520;
  const svgW = LABEL_W + CHART_W;
  const svgH = PAD_TOP + rows.length * ROW_H + PAD_BOTTOM;

  function xForDate(d: Date): number {
    return LABEL_W + (daysBetween(minDate, d) / totalDays) * CHART_W;
  }

  // Month tick marks
  const ticks: { x: number; label: string }[] = [];
  const cursor = new Date(minDate);
  cursor.setDate(1);
  while (cursor <= maxDate) {
    const x = xForDate(cursor);
    if (x >= LABEL_W && x <= LABEL_W + CHART_W) {
      ticks.push({
        x,
        label: cursor.toLocaleDateString("en-GB", { month: "short", year: "2-digit" }),
      });
    }
    cursor.setMonth(cursor.getMonth() + 1);
  }

  // Today line
  const today = new Date();
  const todayX = xForDate(today);
  const showToday = todayX >= LABEL_W && todayX <= LABEL_W + CHART_W;

  return (
    <div className="overflow-x-auto">
      <svg
        width={svgW}
        height={svgH}
        viewBox={`0 0 ${svgW} ${svgH}`}
        className="font-sans"
        aria-label="Schedule Gantt chart"
      >
        {/* Month ticks */}
        {ticks.map((t) => (
          <g key={t.x}>
            <line x1={t.x} y1={PAD_TOP - 4} x2={t.x} y2={svgH - PAD_BOTTOM} stroke="#e4e9f1" strokeWidth={1} />
            <text x={t.x + 3} y={PAD_TOP - 8} fontSize={8} fill="#21365a">
              {t.label}
            </text>
          </g>
        ))}

        {/* Today line */}
        {showToday && (
          <g>
            <line x1={todayX} y1={PAD_TOP - 4} x2={todayX} y2={svgH - PAD_BOTTOM} stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4,3" />
            <text x={todayX + 2} y={PAD_TOP - 8} fontSize={8} fill="#f59e0b" fontWeight="600">
              Today
            </text>
          </g>
        )}

        {/* Rows */}
        {rows.map((a, idx) => {
          const y = PAD_TOP + idx * ROW_H;
          const barY = y + (ROW_H - BAR_H) / 2;
          const s = parseDate(a.start);
          const f = parseDate(a.finish);

          const barX = s ? xForDate(s) : LABEL_W;
          const barEnd = f ? xForDate(f) : barX + 40;
          const barW = Math.max(barEnd - barX, 4);

          const progressW = (a.percentComplete / 100) * barW;

          const barFill = a.isCritical ? "#fca5a5" : "#bfdbfe"; // rose-300 or blue-200
          const progressFill = a.isCritical ? "#ef4444" : "#3b82f6"; // rose-500 or blue-500

          return (
            <g key={a.id}>
              {/* Alternating row background */}
              {idx % 2 === 0 && (
                <rect x={0} y={y} width={svgW} height={ROW_H} fill="#f5f7fa" />
              )}

              {/* Activity name */}
              <text
                x={LABEL_W - 6}
                y={y + ROW_H / 2 + 4}
                textAnchor="end"
                fontSize={9}
                fill="#21365a"
                fontWeight={a.isCritical ? "700" : "400"}
              >
                {a.name.length > 22 ? a.name.slice(0, 22) + "…" : a.name}
              </text>

              {/* Bar background */}
              {s && f && (
                <>
                  <rect
                    x={barX}
                    y={barY}
                    width={barW}
                    height={BAR_H}
                    rx={2}
                    fill={barFill}
                  />
                  {/* Progress fill */}
                  <rect
                    x={barX}
                    y={barY}
                    width={progressW}
                    height={BAR_H}
                    rx={2}
                    fill={progressFill}
                  />
                  {/* % label */}
                  {a.percentComplete > 0 && (
                    <text
                      x={barX + progressW / 2}
                      y={barY + BAR_H / 2 + 3}
                      textAnchor="middle"
                      fontSize={7}
                      fill="white"
                      fontWeight="700"
                    >
                      {a.percentComplete}%
                    </text>
                  )}
                </>
              )}
            </g>
          );
        })}
      </svg>

      <div className="mt-2 flex items-center gap-4 text-xs text-meridian-700">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-blue-200 border border-blue-300" />
          Normal
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-rose-200 border border-rose-300" />
          Critical path
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-amber-400" />
          Today
        </span>
      </div>
    </div>
  );
}
