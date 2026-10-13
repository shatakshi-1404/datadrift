import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AlertCard from "../components/AlertCard";
import RunResults from "../components/RunResults";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { getDriftResults, getPerformanceResults, getRunAlerts, getRunSummary } from "../services/api";
import type { Alert, DriftResult, MonitoringRunSummary, PerformanceResult } from "../types/monitoring";

interface RunDetailData {
  summary: MonitoringRunSummary;
  drift: DriftResult[];
  performance: PerformanceResult[];
  alerts: Alert[];
}

type State =
  | { kind: "loading" }
  | { kind: "ready"; data: RunDetailData }
  | { kind: "error"; message: string };

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!runId) return;
    const id = Number(runId);
    setState({ kind: "loading" });

    Promise.all([getRunSummary(id), getDriftResults(id), getPerformanceResults(id), getRunAlerts(id)])
      .then(([summary, drift, performance, alerts]) =>
        setState({ kind: "ready", data: { summary, drift, performance, alerts } })
      )
      .catch((err) =>
        setState({ kind: "error", message: err instanceof Error ? err.message : "Failed to load run." })
      );
  }, [runId]);

  if (state.kind === "loading") return <LoadingState message="Loading run…" />;
  if (state.kind === "error") return <ErrorState message={state.message} />;

  const { summary, drift, performance, alerts } = state.data;

  return (
    <div className="space-y-6">
      <Link to="/monitoring" className="text-sm text-neutral-500 hover:text-neutral-300">
        ← Back to monitoring history
      </Link>

      <div>
        <h1 className="text-lg font-semibold text-neutral-100">
          Run #{summary.id} · {new Date(summary.started_at).toLocaleString()}
        </h1>
        <p className="text-sm text-neutral-500">
          {summary.reference_dataset_name} vs {summary.current_dataset_name}
          {summary.model_name && ` · ${summary.model_name}`} · {summary.status}
        </p>
      </div>

      <RunResults runId={summary.id} drift={drift} performance={performance} />

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Alerts for this run</h2>
        {alerts.length === 0 ? (
          <p className="text-sm text-neutral-500">No alerts for this run.</p>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
