export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export type TargetReadiness = {
  target_id: string;
  target_name: string;
  status: string;
  evidence: string;
  required_evidence: string;
};

export type Readiness = {
  targets: TargetReadiness[];
  warning: string;
};

export type ExternalModelReport = {
  status: "EVALUATED_EXTERNAL_COF";
  model_id: "TOW-TOOL-COF-CAMBRIDGE";
  source_kind: "external";
  is_ai_tribotwin_model: false;
  material_domain: string;
  source_name: string;
  source_url: string;
  source_workbook: string;
  source_workbook_sha256: string;
  processed_table_sha256: string | null;
  dataset_sha256: string;
  observation_count: number;
  training_rows: number;
  holdout_rows: number;
  training_groups: number;
  holdout_groups: number;
  training_group_ids?: string[];
  holdout_group_ids: string[];
  tow_types?: string[];
  cross_validation_folds: number;
  seed?: number;
  measurement_protocol?: string;
  selected_model: string;
  selection_basis?: string;
  target: string;
  target_unit: string;
  feature_schema?: ExternalFeatureSchema;
  model_comparison: Record<
    string,
    { cv_mae_mean: number; cv_mae_std: number; cv_rmse_mean: number; cv_r2_mean: number }
  >;
  holdout_metrics: { mae: number; rmse: number; r2: number };
  baseline_metrics: { mae: number; rmse: number; r2: number };
  stratified_baseline_metrics?: { mae: number; rmse: number; r2: number };
  holdout_slices: {
    by_tow_type: Record<string, ExternalHoldoutSlice>;
    by_test_run: Record<string, ExternalHoldoutSlice>;
  };
  leave_one_run_out_sensitivity?: {
    description: string;
    by_run: Record<
      string,
      { tow_type: string; rows: number; mae: number; rmse: number; r2: number; mean_residual: number }
    >;
    summary_by_tow_type: Record<
      string,
      { runs: number; mae_mean: number; rmse_mean: number; r2_mean: number; mean_residual_mean: number }
    >;
  };
  failure_investigation_50c?: {
    held_out_run: string;
    findings: string[];
    implication: string;
  };
  specimen_independence_disclosure?: {
    labelled_runs: number;
    runs_per_tow_type: number;
    specimen_serial_numbers_recorded: boolean;
    statement: string;
  };
  residual_analysis: {
    residual_definition: string;
    mean_residual: number;
    baseline_mean_residual: number;
    stratified_baseline_mean_residual?: number;
    interpretation: string;
  };
  group_count_limitation: string;
  uncertainty_assessment: {
    status: string;
    prediction_intervals_produced: boolean;
    reason: string;
    minimum_additional_data?: string;
    mathematical_requirement?: string;
    scientific_validity_distinction?: string;
  };
  caveats: string[];
  interpretation: string;
};

export type ExternalHoldoutSlice = {
  rows: number;
  mae: number;
  rmse: number;
  r2: number;
  mean_residual: number;
  baseline_mae: number;
  baseline_rmse: number;
  baseline_r2: number;
  baseline_mean_residual: number;
};

export type ExternalModelStatus = {
  status: "NOT_RUN" | "EVALUATED_EXTERNAL_COF";
  plot_available: boolean;
  report: ExternalModelReport | null;
};

export type ExternalFeatureInput = {
  name: string;
  unit: string;
  description: string;
  required: boolean;
  dtype: "numeric" | "categorical" | "derived";
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  allowed_values?: string[];
  source?: string;
  transformation?: string;
};

export type ExternalFeatureSchema = {
  features: ExternalFeatureInput[];
  request_feature_columns: string[];
  derived_features: string[];
  categorical_features: string[];
  range_basis: string;
};

export type ModelStatus = {
  demo_status: "NOT_RUN" | "EVALUATED_SYNTHETIC_DEMO";
  training_source: "synthetic_fixture_only";
  experimental_model_trained: false;
  experimental_targets: TargetReadiness[];
  external_model: ExternalModelStatus;
  plot_available: boolean;
  demo_report: {
    source_kind: "synthetic";
    synthetic_only: true;
    experimental_results: false;
    target_id: "SYNTHETIC-DEMO";
    selected_model: string;
    training_rows: number;
    holdout_rows: number;
    training_groups: number;
    holdout_groups: number;
    cross_validation_folds: number;
    model_comparison: Record<
      string,
      { cv_mae_mean: number; cv_mae_std: number; cv_rmse_mean: number; cv_r2_mean: number }
    >;
    holdout_metrics: { mae: number; rmse: number; r2: number };
    interpretation: string;
  } | null;
};

export type CofPredictionRequest = {
  normal_load_n: number;
  nominal_pressure_mpa: number;
  contact_width_mm: number;
  contact_area_mm2: number;
  contact_length_scanned_mm: number;
  contact_half_width_a_mm: number;
  percent_contact_length: number;
  tow_type: string;
};

export type OutOfDomainFeature = {
  feature: string;
  unit: string;
  value: number;
  training_min: number;
  training_max: number;
  direction: "below_min" | "above_max";
  message: string;
};

export type PredictionMetrics = {
  mae: number;
  rmse: number;
  r2: number;
  holdout_rows: number;
  selection_basis: string;
  baseline_mae: number;
  baseline_rmse: number;
  baseline_r2: number;
};

export type PredictionProvenance = {
  model_id: string;
  source_kind: "external";
  source_name: string;
  source_url: string;
  source_workbook: string;
  source_workbook_sha256: string;
  processed_table: string;
  processed_table_sha256: string;
  dataset_sha256: string;
  measurement_protocol: string;
  material_domain: string;
  observation_count: number;
  training_rows: number;
  holdout_rows: number;
  training_groups: number;
  holdout_groups: number;
  selected_model: string;
  seed: number;
  range_basis: string;
};

export type CofPredictionResponse = {
  model_id: string;
  source_kind: "external";
  target: string;
  target_unit: string;
  predicted_coefficient_of_friction: number;
  domain_status: "IN_DOMAIN" | "OUT_OF_DOMAIN";
  out_of_domain_features: OutOfDomainFeature[];
  domain_limitation: string;
  interpretation: string;
  metrics: PredictionMetrics;
  provenance: PredictionProvenance;
  composite_targets_trained: boolean;
  note: string;
};

export type CofCandidateValidationResult = {
  candidate_id: string;
  accepted_for_physical_testing: boolean;
  out_of_domain_features: OutOfDomainFeature[];
  issues: string[];
};

export type CofCandidateValidationResponse = {
  model_id: string;
  source_kind: "external";
  interpretation: string;
  results: CofCandidateValidationResult[];
};

export type CofRecommendationRequest = {
  tow_type: string;
  min_load_n?: number;
  max_load_n?: number;
  num_candidates?: number;
  target_criterion?: "lowest_predicted_cof" | "highest_predicted_cof" | "load_sweep_grid";
};

export type CofRecommendedCandidate = {
  rank: number;
  candidate_id: string;
  conditions: CofPredictionRequest;
  predicted_coefficient_of_friction: number;
  is_model_estimate_not_measurement: boolean;
  recommendation_label: string;
};

export type CofRecommendationResponse = {
  model_id: string;
  source_kind: "external";
  target_criterion: string;
  interpretation: string;
  causal_disclaimer: string;
  reliability_notice: string;
  composite_targets_trained: boolean;
  recommendations: CofRecommendedCandidate[];
};

export type Experiment = {
  id: number;
  experiment_id: string;
  record_status: "PLANNED" | "MEASURED";
  material_system_as_recorded: string;
  planned_by: string;
  composition_as_recorded: string;
  composition_source_reference: string;
  replicate_group_id: string;
  planned_conditions: Record<string, number>;
  measured_conditions: Record<string, number>;
  measurements: Record<string, unknown>;
  instrument_id: string;
  operator: string;
  experiment_date: string | null;
  source_artifact: string;
  source_location: string;
  notes: string;
  recorded_at_utc: string;
  created_at_utc: string;
  import_sha256: string;
};

export type ExperimentFilterParams = {
  status?: "PLANNED" | "MEASURED";
  query?: string;
  material?: string;
  sortBy?: "id" | "experiment_id" | "record_status" | "material_system_as_recorded" | "experiment_date" | "created_at_utc";
  sortDesc?: boolean;
  limit?: number;
  offset?: number;
};

export type ExperimentCounts = {
  PLANNED: number;
  MEASURED: number;
  total: number;
};

export type ApiError = {
  detail?: string | { code?: string; [key: string]: unknown };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiError;
    const message =
      typeof body.detail === "string"
        ? body.detail
        : body.detail
          ? JSON.stringify(body.detail)
          : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export type AnalyticsKpis = {
  total_records: number;
  measured_records: number;
  planned_records: number;
  distinct_materials_count: number;
  records_with_cof: number;
  records_with_wear: number;
};

export type TimeSeriesPoint = {
  period: string;
  total: number;
  measured: number;
  planned: number;
};

export type MaterialDistributionItem = {
  material_system: string;
  total_count: number;
  measured_count: number;
  planned_count: number;
};

export type DistributionBin = {
  bin_start: number;
  bin_end: number;
  bin_label: string;
  count: number;
};

export type NumericStats = {
  count: number;
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  unit: string;
};

export type CofDistribution = {
  has_data: boolean;
  observation_count: number;
  stats: NumericStats | null;
  bins: DistributionBin[];
  unit: string;
  note: string;
};

export type WearDistributionGroup = {
  measurement_name: string;
  unit: string;
  observation_count: number;
  stats: NumericStats | null;
  bins: DistributionBin[];
};

export type WearDistribution = {
  has_data: boolean;
  total_wear_observations: number;
  groups: WearDistributionGroup[];
  note: string;
};

export type CofConditionPoint = {
  experiment_id: string;
  material_system: string;
  load_n: number | null;
  sliding_velocity_m_per_s: number | null;
  sliding_distance_m: number | null;
  coefficient_of_friction: number;
};

export type CofRelationships = {
  has_sufficient_data: boolean;
  observation_count: number;
  points: CofConditionPoint[];
  scientific_disclaimer: string;
};

export type AnalyticsFilterParams = {
  material?: string;
  dateFrom?: string;
  dateTo?: string;
  status?: "PLANNED" | "MEASURED";
};

export type AnalyticsResponse = {
  kpis: AnalyticsKpis;
  timeline: TimeSeriesPoint[];
  materials: MaterialDistributionItem[];
  distinct_material_names: string[];
  cof_distribution: CofDistribution;
  wear_distribution: WearDistribution;
  cof_relationships: CofRelationships;
  filter_echo: Record<string, string | null>;
};

export type ImportPreviewResult = {
  filename: string;
  sha256: string;
  size_bytes: number;
  format_name: string;
  row_count: number;
  valid: boolean;
  errors: { code: string; message: string; row_number?: number }[];
  warnings: { code: string; message: string; row_number?: number }[];
  preview_rows: Record<string, string | null>[];
  can_confirm_import: boolean;
  accepted_rows: number;
  duplicate_rows: number;
  rejected_rows: number;
  duplicate_experiment_ids: string[];
  is_duplicate_artifact: boolean;
};

export type ImportHistoryItem = {
  id: number;
  sha256: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  row_count: number;
  format_name: string;
  created_at_utc: string;
  validation_outcome: string;
  errors_count: number;
  warnings_count: number;
};

export const api = {
  health: () => request<{ status: string; database: string }>("/api/v1/health"),
  readiness: () => request<Readiness>("/api/v1/readiness"),
  modelStatus: () => request<ModelStatus>("/api/v1/models/status"),
  counts: () => request<ExperimentCounts>("/api/v1/experiments/count"),
  analytics: (params?: AnalyticsFilterParams) => {
    const search = new URLSearchParams();
    if (params?.material) search.set("material_system", params.material);
    if (params?.dateFrom) search.set("date_from", params.dateFrom);
    if (params?.dateTo) search.set("date_to", params.dateTo);
    if (params?.status) search.set("record_status", params.status);
    const qs = search.toString();
    return request<AnalyticsResponse>(`/api/v1/analytics${qs ? `?${qs}` : ""}`);
  },
  experiments: (paramsOrStatus?: "PLANNED" | "MEASURED" | ExperimentFilterParams) => {
    const params: ExperimentFilterParams =
      typeof paramsOrStatus === "string" ? { status: paramsOrStatus } : (paramsOrStatus ?? {});
    const search = new URLSearchParams();
    if (params.status) search.set("record_status", params.status);
    if (params.query) search.set("query", params.query);
    if (params.material) search.set("material_system", params.material);
    if (params.sortBy) search.set("sort_by", params.sortBy);
    if (params.sortDesc !== undefined) search.set("sort_desc", String(params.sortDesc));
    if (params.limit !== undefined) search.set("limit", String(params.limit));
    if (params.offset !== undefined) search.set("offset", String(params.offset));
    const qs = search.toString();
    return request<Experiment[]>(`/api/v1/experiments${qs ? `?${qs}` : ""}`);
  },
  getExperiment: (experimentId: string) =>
    request<Experiment>(`/api/v1/experiments/${encodeURIComponent(experimentId)}`),
  createExperiment: (payload: Record<string, unknown>) =>
    request<Experiment>("/api/v1/experiments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExperiment: (experimentId: string, payload: Record<string, unknown>) =>
    request<Experiment>(`/api/v1/experiments/${encodeURIComponent(experimentId)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteExperiment: (experimentId: string) =>
    request<{ message: string; experiment_id: string }>(
      `/api/v1/experiments/${encodeURIComponent(experimentId)}`,
      { method: "DELETE" },
    ),
  createPlan: (payload: Record<string, unknown>) =>
    request<Experiment>("/api/v1/plans", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  predictCof: (payload: CofPredictionRequest) =>
    request<CofPredictionResponse>("/api/v1/models/external/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  validateCofCandidates: (candidates: {
    candidate_id: string;
    conditions: CofPredictionRequest;
  }[]) =>
    request<CofCandidateValidationResponse>("/api/v1/models/external/candidates/validate", {
      method: "POST",
      body: JSON.stringify({ candidates }),
    }),
  recommendCofExperiments: (payload: CofRecommendationRequest) =>
    request<CofRecommendationResponse>("/api/v1/models/external/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  importHistory: (limit = 25) =>
    request<ImportHistoryItem[]>(`/api/v1/imports/history?limit=${limit}`),
  previewImport: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportPreviewResult>("/api/v1/imports/preview", { method: "POST", body: form });
  },
  confirmImport: (file: File, sha256: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("expected_sha256", sha256);
    form.append("confirmation", "true");
    return request<{ sha256: string; records_imported: number; message: string }>(
      "/api/v1/imports/confirm",
      { method: "POST", body: form },
    );
  },
  getExperimentPdfUrl: (experimentId: string) =>
    `${API_BASE}/api/v1/reports/experiment/${encodeURIComponent(experimentId)}/pdf`,
  getRegistryPdfUrl: (params?: { material_system?: string; status?: string; query?: string }) => {
    const q = new URLSearchParams();
    if (params?.material_system && params.material_system !== "ALL") q.set("material_system", params.material_system);
    if (params?.status && params.status !== "ALL") q.set("status", params.status);
    if (params?.query) q.set("query", params.query);
    const qs = q.toString();
    return `${API_BASE}/api/v1/reports/experiments/pdf${qs ? `?${qs}` : ""}`;
  },
  getRegistryCsvUrl: (params?: { material_system?: string; status?: string; query?: string }) => {
    const q = new URLSearchParams();
    if (params?.material_system && params.material_system !== "ALL") q.set("material_system", params.material_system);
    if (params?.status && params.status !== "ALL") q.set("status", params.status);
    if (params?.query) q.set("query", params.query);
    const qs = q.toString();
    return `${API_BASE}/api/v1/reports/experiments/csv${qs ? `?${qs}` : ""}`;
  },
  getAnalyticsPdfUrl: (params?: { material_system?: string; date_start?: string; date_end?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.material_system && params.material_system !== "ALL") q.set("material_system", params.material_system);
    if (params?.date_start) q.set("date_start", params.date_start);
    if (params?.date_end) q.set("date_end", params.date_end);
    if (params?.status && params.status !== "ALL") q.set("status", params.status);
    const qs = q.toString();
    return `${API_BASE}/api/v1/reports/analytics/pdf${qs ? `?${qs}` : ""}`;
  },
  getAnalyticsCsvUrl: (params?: { material_system?: string; date_start?: string; date_end?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.material_system && params.material_system !== "ALL") q.set("material_system", params.material_system);
    if (params?.date_start) q.set("date_start", params.date_start);
    if (params?.date_end) q.set("date_end", params.date_end);
    if (params?.status && params.status !== "ALL") q.set("status", params.status);
    const qs = q.toString();
    return `${API_BASE}/api/v1/reports/analytics/csv${qs ? `?${qs}` : ""}`;
  },
  getModelsPdfUrl: () => `${API_BASE}/api/v1/reports/models/pdf`,
};
