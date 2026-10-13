import type { DriftResult, PerformanceResult } from "../types/monitoring";

const PREDICTION_FEATURES = new Set(["predicted_class", "predicted_probability"]);
const QUALITY_METRICS = new Set(["missing_percentage_increase", "duplicate_percentage", "constant_column"]);

export interface FeatureDriftRow {
  feature: string;
  metricLabel: string;
  value: number;
  status: string;
}

/**
 * One row per real dataset feature, using PSI as the representative
 * status - the same magnitude-based signal the alert engine uses, so the
 * dashboard and the alerts it also displays never disagree.
 */
export function buildFeatureDriftRows(results: DriftResult[]): FeatureDriftRow[] {
  const byFeature = new Map<string, DriftResult[]>();
  for (const row of results) {
    if (row.feature_name === "__dataset__" || PREDICTION_FEATURES.has(row.feature_name)) continue;
    if (QUALITY_METRICS.has(row.metric_name)) continue;
    if (!byFeature.has(row.feature_name)) byFeature.set(row.feature_name, []);
    byFeature.get(row.feature_name)!.push(row);
  }

  const rows: FeatureDriftRow[] = [];
  for (const [feature, featureResults] of byFeature) {
    const psi = featureResults.find((r) => r.metric_name === "psi");
    const chi2 = featureResults.find((r) => r.metric_name === "chi2_statistic");
    const representative = psi ?? chi2;
    if (!representative) continue;
    rows.push({
      feature,
      metricLabel: representative.metric_name === "psi" ? "PSI" : "Chi\u00b2",
      value: representative.metric_value,
      status: representative.status,
    });
  }
  return rows.sort((a, b) => a.feature.localeCompare(b.feature));
}

export function countQualityIssues(results: DriftResult[]): number {
  return results.filter((r) => QUALITY_METRICS.has(r.metric_name) && r.status !== "stable").length;
}

export function findMetric(results: PerformanceResult[], metricName: string): PerformanceResult | undefined {
  return results.find((r) => r.metric_name === metricName);
}
