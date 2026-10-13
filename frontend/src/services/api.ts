import type { Dataset } from "../types/dataset";
import type { HealthResponse } from "../types/health";
import type { FeatureDetailResponse } from "../types/featureDetail";
import type { MLModel } from "../types/model";
import type { Alert, DriftResult, MonitoringRun, MonitoringRunSummary, PerformanceResult } from "../types/monitoring";
import type { Project } from "../types/project";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request to ${path} failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  return (await res.json()) as HealthResponse;
}

export const getProject = (projectId: number) => getJson<Project>(`/api/projects/${projectId}`);

export const listDatasets = (projectId: number) =>
  getJson<Dataset[]>(`/api/projects/${projectId}/datasets`);

export const listModels = (projectId: number) =>
  getJson<MLModel[]>(`/api/projects/${projectId}/models`);

export const listMonitoringRuns = (projectId: number) =>
  getJson<MonitoringRun[]>(`/api/projects/${projectId}/monitoring`);

export const getMonitoringHistory = (projectId: number) =>
  getJson<MonitoringRunSummary[]>(`/api/projects/${projectId}/monitoring/history`);

export const getRunSummary = (runId: number) =>
  getJson<MonitoringRunSummary>(`/api/monitoring/${runId}/summary`);

export const getDriftResults = (runId: number) =>
  getJson<DriftResult[]>(`/api/monitoring/${runId}/drift`);

export const getPerformanceResults = (runId: number) =>
  getJson<PerformanceResult[]>(`/api/monitoring/${runId}/performance`);

export const listProjectAlerts = (projectId: number) =>
  getJson<Alert[]>(`/api/projects/${projectId}/alerts`);

export const getRunAlerts = (runId: number) =>
  getJson<Alert[]>(`/api/monitoring/${runId}/alerts`);

export const getFeatureDetail = (runId: number, featureName: string) =>
  getJson<FeatureDetailResponse>(
    `/api/monitoring/${runId}/features/${encodeURIComponent(featureName)}`
  );

export async function runMonitoring(
  projectId: number,
  body: { reference_dataset_id: number; current_dataset_id: number; model_id?: number }
): Promise<MonitoringRun> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/monitoring/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => null);
    throw new Error(errorBody?.detail ?? `Monitoring run failed (${res.status})`);
  }
  return res.json();
}
