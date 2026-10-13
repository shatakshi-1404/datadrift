export interface ClassificationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number | null;
}

export interface MLModel {
  id: number;
  project_id: number;
  training_dataset_id: number;
  name: string;
  version: number;
  algorithm: string;
  target_column: string;
  feature_columns: string[];
  train_metrics: ClassificationMetrics;
  test_metrics: ClassificationMetrics;
  mlflow_run_id: string;
  mlflow_experiment_id: string;
  created_at: string;
}
