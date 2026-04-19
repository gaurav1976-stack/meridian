import { cn } from "@/lib/cn";

interface ProgressBarProps {
  value: number; // 0–100
  label?: string;
  showValue?: boolean;
  size?: "sm" | "md" | "lg";
  tone?: "auto" | "positive" | "warning" | "critical" | "neutral";
  className?: string;
}

function toneFromValue(value: number): "positive" | "warning" | "critical" {
  if (value >= 75) return "positive";
  if (value >= 40) return "warning";
  return "critical";
}

const FILL: Record<string, string> = {
  positive: "bg-emerald-500",
  warning: "bg-amber-400",
  critical: "bg-rose-500",
  neutral: "bg-meridian-500",
};

const HEIGHT: Record<string, string> = {
  sm: "h-1.5",
  md: "h-2",
  lg: "h-3",
};

export function ProgressBar({
  value,
  label,
  showValue = true,
  size = "md",
  tone = "auto",
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const resolvedTone = tone === "auto" ? toneFromValue(clamped) : tone;

  return (
    <div className={cn("space-y-1", className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between text-xs text-meridian-700">
          {label && <span>{label}</span>}
          {showValue && <span className="font-medium tabular-nums">{clamped}%</span>}
        </div>
      )}
      <div className={cn("w-full overflow-hidden rounded-full bg-meridian-100", HEIGHT[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-500", FILL[resolvedTone])}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
