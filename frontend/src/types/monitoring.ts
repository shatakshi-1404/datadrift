export interface MonitoringRun {
  id: number;
  project_id: number;
  reference_dataset_id: number;
  current_dataset_id: number;
  model_id: number | null;
  status: string;
  started_at: string;
  completed_at: string | null;
}

export type DriftStatus = "stable" | "warning" | "drift" | "critical" | "info";

export interface DriftResult {
  id: number;
  monitoring_run_id: number;
  feature_name: string;
  metric_name: string;
  metric_value: number;
  status: DriftStatus;
  created_at: string;
}

export interface PerformanceResult {
  id: number;
  monitoring_run_id: number;
  metric_name: string;
  reference_value: number;
  current_value: number;
  change: number;
  status: "improved" | "stable" | "degraded";
  created_at: string;
}

export interface Alert {
  id: number;
  monitoring_run_id: number;
  severity: "INFO" | "WARNING" | "CRITICAL";
  title: string;
  message: string;
  created_at: string;
}

export interface MonitoringRunSummary {
  id: number;
  status: string;
  started_at: string;
  completed_at: string | null;
  reference_dataset_name: string;
  current_dataset_name: string;
  model_name: string | null;
  drifted_feature_count: number;
  alert_count: number;
}
