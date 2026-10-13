import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { Link } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { CURRENT_PROJECT_ID } from "../config";
import { getMonitoringHistory } from "../services/api";
import type { MonitoringRunSummary } from "../types/monitoring";

type State =
  | { kind: "loading" }
  | { kind: "ready"; runs: MonitoringRunSummary[] }
  | { kind: "error"; message: string };

export default function Monitoring() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    getMonitoringHistory(CURRENT_PROJECT_ID)
      .then((runs) => setState({ kind: "ready", runs }))
      .catch((err) =>
        setState({ kind: "error", message: err instanceof Error ? err.message : "Failed to load history." })
      );
  }, []);

  if (state.kind === "loading") return <LoadingState message="Loading monitoring history…" />;
  if (state.kind === "error") return <ErrorState message={state.message} />;

  return (
    <div className="space-y-4">
      <PageHeader title="Monitoring History" description="Every past monitoring run for this project." />
      {state.runs.length === 0 ? (
        <EmptyState
          icon={History}
          title="No monitoring runs yet"
          description="Run monitoring from the dashboard to see history here."
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-900">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-neutral-500">
                <th className="p-3 font-medium">Started</th>
                <th className="p-3 font-medium">Reference</th>
                <th className="p-3 font-medium">Current</th>
                <th className="p-3 font-medium">Model</th>
                <th className="p-3 font-medium">Drifted</th>
                <th className="p-3 font-medium">Alerts</th>
                <th className="p-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {state.runs.map((run) => (
                <tr key={run.id} className="hover:bg-neutral-800/50">
                  <td className="p-3">
                    <Link to={`/monitoring/${run.id}`} className="text-neutral-200 hover:text-white">
                      {new Date(run.started_at).toLocaleString()}
                    </Link>
                  </td>
                  <td className="p-3 text-neutral-400">{run.reference_dataset_name}</td>
                  <td className="p-3 text-neutral-400">{run.current_dataset_name}</td>
                  <td className="p-3 text-neutral-400">{run.model_name ?? "—"}</td>
                  <td className="p-3 text-neutral-400">{run.drifted_feature_count}</td>
                  <td className="p-3 text-neutral-400">{run.alert_count}</td>
                  <td className="p-3 text-neutral-400">{run.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
