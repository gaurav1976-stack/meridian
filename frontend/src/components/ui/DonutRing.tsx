"use client";

/**
 * Simple SVG donut ring for showing a single percentage value.
 * Used on dashboard KPI cards and project overview.
 */

interface DonutRingProps {
  value: number; // 0–100
  size?: number; // px
  strokeWidth?: number;
  tone?: "positive" | "warning" | "critical" | "neutral";
  label?: string;
}

const TONE_COLOURS: Record<string, string> = {
  positive: "#10b981", // emerald-500
  warning: "#f59e0b", // amber-500
  critical: "#ef4444", // rose-500
  neutral: "#3b5e8c", // meridian-500
};

function toneFromValue(v: number): "positive" | "warning" | "critical" {
  if (v >= 75) return "positive";
  if (v >= 40) return "warning";
  return "critical";
}

export function DonutRing({
  value,
  size = 64,
  strokeWidth = 8,
  tone,
  label,
}: DonutRingProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const resolvedTone = tone ?? toneFromValue(clamped);
  const colour = TONE_COLOURS[resolvedTone];

  const r = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const dash = (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="#e4e9f1"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc — starts at top (−90°) */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={colour}
          strokeWidth={strokeWidth}
          strokeDasharray={`${dash} ${circumference - dash}`}
          strokeDashoffset={circumference / 4}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.5s ease" }}
        />
        {/* Centre text */}
        <text
          x={cx}
          y={cy + 4}
          textAnchor="middle"
          fontSize={size * 0.22}
          fontWeight="700"
          fill={colour}
        >
          {clamped}%
        </text>
      </svg>
      {label && (
        <span className="text-xs text-meridian-700 text-center leading-tight">
          {label}
        </span>
      )}
    </div>
  );
}
