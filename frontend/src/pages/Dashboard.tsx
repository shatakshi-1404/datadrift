import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import MetricCard from "../components/MetricCard";
import RunResults from "../components/RunResults";
import AlertCard from "../components/AlertCard";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { CURRENT_PROJECT_ID } from "../config";
import { buildFeatureDriftRows, countQualityIssues, findMetric } from "../lib/monitoring";
import {
  getDriftResults,
  getPerformanceResults,
  getProject,
  listDatasets,
  listModels,
  listMonitoringRuns,
  listProjectAlerts,
  runMonitoring,
} from "../services/api";
import type { Alert, DriftResult, MonitoringRun, PerformanceResult } from "../types/monitoring";
import type { Project } from "../types/project";

interface DashboardData {
  project: Project;
  run: MonitoringRun | null;
  drift: DriftResult[];
  performance: PerformanceResult[];
  alerts: Alert[];
}

type State =
  | { kind: "loading" }
  | { kind: "ready"; data: DashboardData }
  | { kind: "error"; message: string };

export default function Dashboard() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [isRunning, setIsRunning] = useState(false);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const project = await getProject(CURRENT_PROJECT_ID);
      const runs = await listMonitoringRuns(CURRENT_PROJECT_ID);
      const latestRun = runs[0] ?? null;

      const [drift, performance, alerts] = await Promise.all([
        latestRun ? getDriftResults(latestRun.id) : Promise.resolve([]),
        latestRun ? getPerformanceResults(latestRun.id) : Promise.resolve([]),
        listProjectAlerts(CURRENT_PROJECT_ID),
      ]);

      setState({ kind: "ready", data: { project, run: latestRun, drift, performance, alerts } });
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : "Failed to load dashboard." });
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleRunMonitoring = async () => {
    setIsRunning(true);
    try {
      const [datasets, models] = await Promise.all([
        listDatasets(CURRENT_PROJECT_ID),
        listModels(CURRENT_PROJECT_ID),
      ]);
      const reference = datasets.find((d) => d.dataset_type === "reference");
      const current = datasets.find((d) => d.dataset_type === "current");
      const model = models[0];

      if (!reference || !current) {
        throw new Error("Upload both a reference and a current dataset before running monitoring.");
      }

      await runMonitoring(CURRENT_PROJECT_ID, {
        reference_dataset_id: reference.id,
        current_dataset_id: current.id,
        model_id: model?.id,
      });
      await load();
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : "Monitoring run failed." });
    } finally {
      setIsRunning(false);
    }
  };

  if (state.kind === "loading") return <LoadingState message="Loading dashboard…" />;
  if (state.kind === "error") return <ErrorState message={state.message} onRetry={load} />;

  const { project, run, drift, performance, alerts } = state.data;
  const featureRows = buildFeatureDriftRows(drift);
  const driftedCount = featureRows.filter((r) => r.status === "drift").length;
  const qualityIssueCount = countQualityIssues(drift);
  const f1 = findMetric(performance, "f1");

  return (
    <div className="space-y-6">
      <PageHeader
        title={project.name}
        description={project.description ?? undefined}
        action={
          <button
            onClick={handleRunMonitoring}
            disabled={isRunning}
            className="flex items-center gap-2 rounded-md bg-neutral-100 px-3 py-1.5 text-sm font-medium text-neutral-900 hover:bg-white disabled:opacity-50"
          >
            <RefreshCw size={14} className={isRunning ? "animate-spin" : ""} />
            {isRunning ? "Running…" : "Run Monitoring"}
          </button>
        }
      />

      {run === null ? (
        <EmptyState
          icon={RefreshCw}
          title="No monitoring runs yet"
          description="Upload a reference and current dataset, then click Run Monitoring."
          action={{ label: "Run Monitoring", onClick: handleRunMonitoring }}
        />
      ) : (
        <>
          <p className="text-xs text-neutral-500">
            Last run: {new Date(run.completed_at ?? run.started_at).toLocaleString()}
          </p>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <MetricCard label="Features monitored" value={String(featureRows.length)} />
            <MetricCard
              label="Drifted features"
              value={String(driftedCount)}
              tone={driftedCount > 0 ? "warning" : "default"}
            />
            <MetricCard
              label="Quality issues"
              value={String(qualityIssueCount)}
              tone={qualityIssueCount > 0 ? "warning" : "default"}
            />
            <MetricCard label="Model F1" value={f1 ? f1.current_value.toFixed(2) : "Not measured yet"} />
          </div>

          <RunResults runId={run.id} drift={drift} performance={performance} />
        </>
      )}

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Recent Alerts</h2>
        {alerts.length === 0 ? (
          <p className="text-sm text-neutral-500">No alerts yet.</p>
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
