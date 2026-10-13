export type DatasetType = "reference" | "current";

export interface Dataset {
  id: number;
  project_id: number;
  name: string;
  dataset_type: DatasetType;
  rows: number;
  columns: number;
  created_at: string;
}
