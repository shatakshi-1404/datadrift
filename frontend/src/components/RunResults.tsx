import DriftTable from "./DriftTable";
import { buildFeatureDriftRows } from "../lib/monitoring";
import type { DriftResult, PerformanceResult } from "../types/monitoring";

interface RunResultsProps {
  runId: number;
  drift: DriftResult[];
  performance: PerformanceResult[];
}

export default function RunResults({ runId, drift, performance }: RunResultsProps) {
  const featureRows = buildFeatureDriftRows(drift);

  return (
    <>
      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Feature Drift</h2>
        <div className="overflow-x-auto">
          <DriftTable rows={featureRows} runId={runId} />
        </div>
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Model Performance</h2>
        {performance.length === 0 ? (
          <p className="text-sm text-neutral-500">Not measured yet (no ground-truth labels in current data).</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-neutral-500">
                  <th className="pb-2 font-medium">Metric</th>
                  <th className="pb-2 font-medium">Reference</th>
                  <th className="pb-2 font-medium">Current</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {performance.map((row) => (
                  <tr key={row.metric_name}>
                    <td className="py-2 text-neutral-200">{row.metric_name}</td>
                    <td className="py-2 text-neutral-400">{row.reference_value.toFixed(3)}</td>
                    <td className="py-2 text-neutral-400">{row.current_value.toFixed(3)}</td>
                    <td className="py-2 text-neutral-400">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
