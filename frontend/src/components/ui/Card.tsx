import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "bg-white border border-meridian-100 rounded-lg shadow-sm",
        className
      )}
    >
      {children}
    </div>
  );
}

// CardHeader accepts two compositional forms:
//   1. Compact prop form — `<CardHeader title="X" subtitle="Y" />` — used by
//      the dashboard and the projects list where the header is a single line.
//   2. Slot form — `<CardHeader>{children}</CardHeader>` — used by the module
//      pages where the header may carry an `<h2>` heading plus richer prose.
// If `children` is supplied it takes precedence; the prop form falls back.
export function CardHeader({
  title,
  subtitle,
  children,
  className,
}: {
  title?: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("px-5 py-4 border-b border-meridian-100", className)}
    >
      {children ? (
        children
      ) : (
        <>
          {title ? (
            <div className="font-medium text-meridian-900">{title}</div>
          ) : null}
          {subtitle ? (
            <div className="text-xs text-meridian-700 mt-0.5">{subtitle}</div>
          ) : null}
        </>
      )}
    </div>
  );
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("p-5", className)}>{children}</div>;
}
