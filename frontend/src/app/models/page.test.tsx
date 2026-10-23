import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ModelsPage from "@/app/models/page";
import type { ModelStatus } from "@/lib/api";

const MOCK_MODEL_STATUS: ModelStatus = {
  demo_status: "EVALUATED_SYNTHETIC_DEMO",
  training_source: "synthetic_fixture_only",
  experimental_model_trained: false,
  demo_report: {
    source_kind: "synthetic",
    synthetic_only: true,
    experimental_results: false,
    target_id: "SYNTHETIC-DEMO",
    selected_model: "ridge",
    training_rows: 80,
    holdout_rows: 20,
    training_groups: 4,
    holdout_groups: 1,
    cross_validation_folds: 4,
    model_comparison: {
      ridge: { cv_mae_mean: 0.05, cv_mae_std: 0.01, cv_rmse_mean: 0.06, cv_r2_mean: 0.88 },
    },
    holdout_metrics: {
      mae: 0.0526,
      rmse: 0.0643,
      r2: 0.8921,
    },
    interpretation: "Synthetic fixture demonstration only. These metrics are not estimates of performance on AI-TriboTwin composite experiments.",
  },
  external_model: {
    status: "EVALUATED_EXTERNAL_COF",
    plot_available: true,
    report: {
      status: "EVALUATED_EXTERNAL_COF",
      model_id: "TOW-TOOL-COF-CAMBRIDGE",
      source_kind: "external",
      is_ai_tribotwin_model: false,
      material_domain: "carbon-fibre tow on glass",
      source_name: "Friction of carbon fibre tows (University of Cambridge)",
      source_url: "https://doi.example/10.1000",
      source_workbook: "TowTool_ContactLengthAndFrictionForce.xlsx",
      source_workbook_sha256: "b9c9af71be796d25d8d6deac6e303943dc6ad45a69909eb3c7f7a06126bc4763",
      processed_table_sha256: "61ee1ec23b913272cf593939ae729208db1a7c367a926c08d900d1177bb6b91f",
      dataset_sha256: "80b05ecd401af749251afd78011a0104612ff64377b9c19c21a2c55b261b382c",
      observation_count: 140,
      training_rows: 98,
      holdout_rows: 42,
      training_groups: 7,
      holdout_groups: 3,
      training_group_ids: ["T1", "T2", "T3"],
      holdout_group_ids: ["T700-12k-50C-T1", "T700-12k-60E-T2", "T700-12k-60E-T4"],
      tow_types: ["T700-12k-50C", "T700-12k-60E"],
      cross_validation_folds: 5,
      seed: 417,
      measurement_protocol: "Tow-on-tool sliding friction under 14-step ramp",
      selected_model: "ridge_regression",
      selection_basis: "lowest group cross-validation MAE on training groups",
      target: "coefficient_of_friction",
      target_unit: "dimensionless",
      holdout_metrics: {
        mae: 0.1340,
        rmse: 0.2263,
        r2: 0.7826,
      },
      baseline_metrics: {
        mae: 0.2737,
        rmse: 0.4862,
        r2: -0.0039,
      },
      holdout_slices: {
        by_tow_type: {
          "T700-12k-50C": {
            rows: 14,
            mae: 0.1571,
            rmse: 0.2605,
            r2: -0.7446,
            mean_residual: 0.1571,
            baseline_mae: 0.1410,
            baseline_rmse: 0.2008,
            baseline_r2: -0.0367,
            baseline_mean_residual: 0.03,
          },
          "T700-12k-60E": {
            rows: 28,
            mae: 0.1225,
            rmse: 0.2070,
            r2: 0.8716,
            mean_residual: 0.0474,
            baseline_mae: 0.3401,
            baseline_rmse: 0.5783,
            baseline_r2: -0.0021,
            baseline_mean_residual: 0.03,
          },
        },
        by_test_run: {
          "T700-12k-50C-T1": {
            rows: 14,
            mae: 0.1571,
            rmse: 0.2605,
            r2: -0.7446,
            mean_residual: 0.1571,
            baseline_mae: 0.1410,
            baseline_rmse: 0.2008,
            baseline_r2: -0.0367,
            baseline_mean_residual: 0.03,
          },
        },
      },
      model_comparison: {
        ridge_regression: { cv_mae_mean: 0.11, cv_mae_std: 0.02, cv_rmse_mean: 0.18, cv_r2_mean: 0.82 },
      },
      residual_analysis: {
        mean_residual: 0.084,
        baseline_mean_residual: 0.030,
        residual_definition: "model prediction - observed COF",
        interpretation: "Fixed holdout only",
      },
      uncertainty_assessment: {
        status: "NOT_CALIBRATED",
        prediction_intervals_produced: false,
        mathematical_requirement: "Requires at least 9 independent runs per stratum under split-conformal prediction.",
        scientific_validity_distinction: "Meeting mathematical floor is necessary but does not guarantee physical validity without verified specimen independence.",
        reason: "Only 10 labelled sweeps total without specimen serial numbers.",
      },
      group_count_limitation: "10 sweeps total without specimen serial numbers.",
      caveats: ["Sequential load ramp autocorrelation", "Specimen independence unverified"],
      failure_investigation_50c: {
        held_out_run: "T700-12k-50C-T1",
        findings: [
          "Step 0 error is +0.786060 accounting for 65.02% of squared error.",
          "High baseline variability on 50C tow type.",
        ],
        implication: "Predictions for 50C carry substantially higher uncertainty.",
      },
      specimen_independence_disclosure: {
        labelled_runs: 10,
        runs_per_tow_type: 5,
        specimen_serial_numbers_recorded: false,
        statement: "Sweeps are labelled Test 1-5 without specimen serial numbers or spool IDs.",
      },
      feature_schema: {
        features: [
          { name: "normal_load_n", unit: "N", description: "", required: true, dtype: "numeric", min: 0.07, max: 48.36, median: 10 },
          { name: "nominal_pressure_mpa", unit: "MPa", description: "", required: true, dtype: "numeric", min: 0.0004, max: 0.34, median: 0.1 },
          { name: "contact_width_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 5.1, max: 8.0, median: 6.7 },
          { name: "contact_area_mm2", unit: "mm^2", description: "", required: true, dtype: "numeric", min: 121.8, max: 189.9, median: 160.3 },
          { name: "contact_length_scanned_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 14.9, max: 3252.6, median: 1452.0 },
          { name: "contact_half_width_a_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 0.000007, max: 0.000044, median: 0.000029 },
          { name: "percent_contact_length", unit: "%", description: "", required: true, dtype: "numeric", min: 0.2, max: 38.3, median: 17.8 },
          { name: "tow_type", unit: "categorical", description: "", required: true, dtype: "categorical", allowed_values: ["T700-12k-60E", "T700-12k-50C"] },
        ],
        request_feature_columns: ["normal_load_n", "nominal_pressure_mpa", "contact_width_mm", "contact_area_mm2", "contact_length_scanned_mm", "contact_half_width_a_mm", "percent_contact_length", "tow_type"],
        derived_features: ["nominal_pressure_mpa"],
        categorical_features: ["tow_type"],
        range_basis: "training observations only",
      },
      interpretation: "External Cambridge benchmark carbon-fibre tow-on-tool friction model.",
    },
  },
  experimental_targets: [
    { target_id: "COF", target_name: "Coefficient of Friction (Composite)", status: "BLOCKED", evidence: "No verified composite benchmark.", required_evidence: "Author clarification of replicate groups." },
    { target_id: "WEAR_RATE", target_name: "Wear Rate", status: "BLOCKED", evidence: "Incompatible volumetric vs specific wear units.", required_evidence: "Resolution of incompatible wear measurement units." },
  ],
  plot_available: true,
};

function mockFetch(body: unknown, ok = true) {
  const spy = vi.fn(async () => ({
    ok,
    status: ok ? 200 : 500,
    json: async () => body,
  }));
  vi.stubGlobal("fetch", spy);
  return spy;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ModelsPage (Model Experience & Prediction Transparency)", () => {
  it("renders all three distinct model tiers visibly separated", async () => {
    mockFetch(MOCK_MODEL_STATUS);
    render(<ModelsPage />);

    // Tier 1: External Cambridge Model
    expect(await screen.findByText(/Tier 1 · External Benchmark/i)).toBeInTheDocument();
    expect(screen.getByText(/Cambridge Tow-on-Tool Friction Model/i)).toBeInTheDocument();

    // Tier 2: Synthetic Demonstration Model
    expect(screen.getByText(/Tier 2 · Synthetic Demonstration/i)).toBeInTheDocument();
    expect(screen.getByText(/SYNTHETIC-DEMO/i)).toBeInTheDocument();
    expect(screen.getByText(/Software Pipeline Demonstration Only/i)).toBeInTheDocument();

    // Tier 3: Blocked Composite Targets
    expect(screen.getByText(/Tier 3 · Blocked \/ No Go/i)).toBeInTheDocument();
    expect(screen.getByText("CURRENTLY BLOCKED")).toBeInTheDocument();
  });

  it("displays verified model metrics and provenance from the report artifact", async () => {
    mockFetch(MOCK_MODEL_STATUS);
    render(<ModelsPage />);

    // Verified held-out evaluation metrics
    expect(await screen.findByText("0.1340")).toBeInTheDocument(); // Holdout MAE
    expect(screen.getByText("0.2263")).toBeInTheDocument(); // Holdout RMSE
    expect(screen.getByText("0.7826")).toBeInTheDocument(); // Holdout R²

    // Observation counts
    expect(screen.getByText(/140 total observations/)).toBeInTheDocument();
    expect(screen.getByText(/98 training rows/)).toBeInTheDocument();
    expect(screen.getByText(/42 held-out rows/)).toBeInTheDocument();

    // Stratified tow-type slices
    expect(screen.getAllByText("T700-12k-60E").length).toBeGreaterThan(0);
    expect(screen.getByText("0.8716")).toBeInTheDocument(); // 60E R²
    expect(screen.getAllByText("-0.7446").length).toBeGreaterThan(0); // 50C negative R²

    // 50C Deficit Warning
    expect(screen.getByText(/50C Generalization Deficit/i)).toBeInTheDocument();
  });

  it("renders scientific boundaries and specimen independence disclosures", async () => {
    mockFetch(MOCK_MODEL_STATUS);
    render(<ModelsPage />);

    expect(await screen.findByText(/Specimen Independence Disclosure/i)).toBeInTheDocument();
    expect(screen.getByText(/Sweeps are labelled Test 1-5 without specimen serial numbers/)).toBeInTheDocument();
    expect(screen.getByText(/Prediction Interval Feasibility/i)).toBeInTheDocument();
    expect(screen.getByText(/Requires at least 9 independent runs/)).toBeInTheDocument();
  });

  it("shows an honest error notice when the model service fails", async () => {
    mockFetch({ detail: "Database or artifact bundle offline" }, false);
    render(<ModelsPage />);

    expect(await screen.findByText(/Model service error/i)).toBeInTheDocument();
  });
});
