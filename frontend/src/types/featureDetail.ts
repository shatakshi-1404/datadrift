import type { DriftResult } from "./monitoring";

export interface NumericStats {
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  std: number | null;
}

export interface CategoryFrequency {
  value: string;
  count: number;
  percentage: number;
}

export interface CategoricalStats {
  unique_categories: number;
  top_categories: CategoryFrequency[];
}

export interface FeatureStats {
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  numeric: NumericStats | null;
  categorical: CategoricalStats | null;
}

export interface DistributionData {
  labels: string[];
  reference_percentage: number[];
  current_percentage: number[];
}

export interface FeatureDetailResponse {
  feature_name: string;
  feature_type: "numeric" | "categorical";
  reference: FeatureStats;
  current: FeatureStats;
  distribution: DistributionData;
  metrics: DriftResult[];
  interpretation: string;
}
