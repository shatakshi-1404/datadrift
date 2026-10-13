import { Link } from "react-router-dom";
import type { FeatureDriftRow } from "../lib/monitoring";

const statusStyles: Record<string, string> = {
  stable: "bg-emerald-500/10 text-emerald-400",
  warning: "bg-amber-500/10 text-amber-400",
  drift: "bg-red-500/10 text-red-400",
  critical: "bg-red-500/10 text-red-400",
  info: "bg-neutral-500/10 text-neutral-400",
};

export default function DriftTable({ rows, runId }: { rows: FeatureDriftRow[]; runId: number }) {
  if (rows.length === 0) {
    return <p className="text-sm text-neutral-500">No feature drift results yet.</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs uppercase tracking-wide text-neutral-500">
          <th className="pb-2 font-medium">Feature</th>
          <th className="pb-2 font-medium">{rows[0]?.metricLabel ?? "Metric"}</th>
          <th className="pb-2 font-medium">Status</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-neutral-800">
        {rows.map((row) => (
          <tr key={row.feature}>
            <td className="py-2">
              <Link
                to={`/monitoring/${runId}/features/${encodeURIComponent(row.feature)}`}
                className="text-neutral-200 underline decoration-neutral-700 underline-offset-2 hover:text-white"
              >
                {row.feature}
              </Link>
            </td>
            <td className="py-2 text-neutral-400">{row.value.toFixed(3)}</td>
            <td className="py-2">
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium uppercase ${
                  statusStyles[row.status] ?? statusStyles.info
                }`}
              >
                {row.status}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
