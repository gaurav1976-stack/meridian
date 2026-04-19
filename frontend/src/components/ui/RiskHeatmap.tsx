"use client";

/**
 * 5×5 Risk Heatmap — pure SVG/CSS, no charting library required.
 * Likelihood on X axis (1–5), Impact on Y axis (5–1 top-to-bottom).
 * Cells are coloured by score (L × I): green ≤ 6, amber 7–14, red ≥ 15.
 */

interface RiskPoint {
  likelihood: number;
  impact: number;
  code: string;
  title: string;
}

interface RiskHeatmapProps {
  risks: RiskPoint[];
}

function cellColour(l: number, i: number): string {
  const score = l * i;
  if (score >= 15) return "#fecaca"; // rose-200
  if (score >= 9) return "#fde68a"; // amber-200
  if (score >= 6) return "#fef9c3"; // yellow-100
  return "#d1fae5"; // emerald-100
}

function cellTextColour(l: number, i: number): string {
  const score = l * i;
  if (score >= 15) return "#991b1b"; // rose-800
  if (score >= 9) return "#92400e"; // amber-800
  if (score >= 6) return "#713f12"; // yellow-800
  return "#065f46"; // emerald-800
}

const CELL = 56; // px per cell
const LABEL = 28; // axis label width/height
const PAD = 4;

export function RiskHeatmap({ risks }: RiskHeatmapProps) {
  const width = LABEL + 5 * CELL + PAD;
  const height = LABEL + 5 * CELL + PAD;

  // Group risks by (likelihood, impact)
  const grouped = new Map<string, RiskPoint[]>();
  for (const r of risks) {
    const key = `${r.likelihood},${r.impact}`;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(r);
  }

  return (
    <div className="overflow-x-auto">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="font-sans"
        aria-label="5×5 Risk Heatmap"
      >
        {/* Y-axis label: Impact */}
        <text
          x={10}
          y={height / 2}
          textAnchor="middle"
          fontSize={9}
          fill="#21365a"
          transform={`rotate(-90, 10, ${height / 2})`}
          fontWeight="600"
        >
          IMPACT ↑
        </text>

        {/* X-axis label: Likelihood */}
        <text
          x={LABEL + (5 * CELL) / 2}
          y={height - 2}
          textAnchor="middle"
          fontSize={9}
          fill="#21365a"
          fontWeight="600"
        >
          LIKELIHOOD →
        </text>

        {/* Axis tick labels */}
        {[1, 2, 3, 4, 5].map((v) => (
          <g key={`x-${v}`}>
            {/* X ticks */}
            <text
              x={LABEL + (v - 1) * CELL + CELL / 2}
              y={LABEL - 6}
              textAnchor="middle"
              fontSize={9}
              fill="#21365a"
            >
              {v}
            </text>
            {/* Y ticks (impact 5 at top, 1 at bottom) */}
            <text
              x={LABEL - 6}
              y={PAD + (5 - v) * CELL + CELL / 2 + 4}
              textAnchor="end"
              fontSize={9}
              fill="#21365a"
            >
              {v}
            </text>
          </g>
        ))}

        {/* Cells */}
        {[1, 2, 3, 4, 5].map((impact) =>
          [1, 2, 3, 4, 5].map((likelihood) => {
            const x = LABEL + (likelihood - 1) * CELL;
            const y = PAD + (5 - impact) * CELL;
            const key = `${likelihood},${impact}`;
            const cellRisks = grouped.get(key) ?? [];
            const bg = cellColour(likelihood, impact);
            const fg = cellTextColour(likelihood, impact);
            const score = likelihood * impact;

            return (
              <g key={key}>
                <rect
                  x={x}
                  y={y}
                  width={CELL}
                  height={CELL}
                  fill={bg}
                  stroke="#e4e9f1"
                  strokeWidth={1}
                />
                {/* Score in corner */}
                <text
                  x={x + 4}
                  y={y + 11}
                  fontSize={8}
                  fill={fg}
                  opacity={0.6}
                >
                  {score}
                </text>
                {/* Risk codes */}
                {cellRisks.slice(0, 3).map((r, idx) => (
                  <text
                    key={r.code}
                    x={x + CELL / 2}
                    y={y + 24 + idx * 12}
                    textAnchor="middle"
                    fontSize={8}
                    fontWeight="700"
                    fill={fg}
                  >
                    {r.code}
                  </text>
                ))}
                {cellRisks.length > 3 && (
                  <text
                    x={x + CELL / 2}
                    y={y + CELL - 6}
                    textAnchor="middle"
                    fontSize={7}
                    fill={fg}
                  >
                    +{cellRisks.length - 3}
                  </text>
                )}
              </g>
            );
          })
        )}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex items-center gap-4 text-xs text-meridian-700">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-emerald-100 border border-emerald-200" />
          Low (≤6)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-yellow-100 border border-yellow-200" />
          Medium (7–8)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-amber-200 border border-amber-300" />
          High (9–14)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-rose-200 border border-rose-300" />
          Critical (≥15)
        </span>
      </div>
    </div>
  );
}
