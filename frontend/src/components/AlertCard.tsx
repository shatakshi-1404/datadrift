import type { Alert } from "../types/monitoring";

const severityStyles: Record<Alert["severity"], string> = {
  INFO: "border-neutral-700 text-neutral-300",
  WARNING: "border-amber-700 text-amber-400",
  CRITICAL: "border-red-700 text-red-400",
};

export default function AlertCard({ alert }: { alert: Alert }) {
  return (
    <div className={`rounded-lg border p-3 ${severityStyles[alert.severity]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide">{alert.severity}</span>
        <span className="text-xs text-neutral-500">
          {new Date(alert.created_at).toLocaleString()}
        </span>
      </div>
      <p className="mt-1 text-sm font-medium text-neutral-100">{alert.title}</p>
      <p className="mt-1 text-sm text-neutral-400">{alert.message}</p>
    </div>
  );
}
