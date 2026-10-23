import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CofPredictionForm } from "@/components/cof-prediction-form";
import type { CofPredictionResponse, ExternalFeatureSchema } from "@/lib/api";

const SCHEMA: ExternalFeatureSchema = {
  features: [
    { name: "normal_load_n", unit: "N", description: "", required: true, dtype: "numeric", min: 0.07, max: 49.1, median: 10 },
    { name: "log10_normal_load_n", unit: "log10(N)", description: "", required: false, dtype: "derived", source: "normal_load_n", transformation: "log10(normal_load_n), base 10" },
    { name: "nominal_pressure_mpa", unit: "MPa", description: "", required: true, dtype: "numeric", min: 0.0004, max: 0.34, median: 0.1 },
    { name: "contact_width_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 5.1, max: 8.0, median: 6.7 },
    { name: "contact_area_mm2", unit: "mm^2", description: "", required: true, dtype: "numeric", min: 121.8, max: 189.9, median: 160.3 },
    { name: "contact_length_scanned_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 14.9, max: 3252.6, median: 1452.0 },
    { name: "contact_half_width_a_mm", unit: "mm", description: "", required: true, dtype: "numeric", min: 0.000007, max: 0.000044, median: 0.000029 },
    { name: "percent_contact_length", unit: "%", description: "", required: true, dtype: "numeric", min: 0.2, max: 38.3, median: 17.8 },
    { name: "tow_type", unit: "categorical", description: "", required: true, dtype: "categorical", allowed_values: ["T700-12k-50C", "T700-12k-60E"] },
  ],
  request_feature_columns: [
    "normal_load_n",
    "nominal_pressure_mpa",
    "contact_width_mm",
    "contact_area_mm2",
    "contact_length_scanned_mm",
    "contact_half_width_a_mm",
    "percent_contact_length",
    "tow_type",
  ],
  derived_features: ["log10_normal_load_n"],
  categorical_features: ["tow_type"],
  range_basis: "min/max observed in training",
};

function predictionBody(overrides: Partial<CofPredictionResponse> = {}): CofPredictionResponse {
  return {
    model_id: "TOW-TOOL-COF-CAMBRIDGE",
    source_kind: "external",
    target: "coefficient_of_friction",
    target_unit: "dimensionless",
    predicted_coefficient_of_friction: 0.42,
    domain_status: "IN_DOMAIN",
    out_of_domain_features: [],
    domain_limitation: "External Cambridge tow-on-tool model, not a composite predictor.",
    interpretation: "external",
    metrics: {
      mae: 0.134,
      rmse: 0.226,
      r2: 0.783,
      holdout_rows: 42,
      selection_basis: "lowest group CV MAE",
      baseline_mae: 0.274,
      baseline_rmse: 0.486,
      baseline_r2: -0.004,
    },
    provenance: {
      model_id: "TOW-TOOL-COF-CAMBRIDGE",
      source_kind: "external",
      source_name: "Friction of carbon fibre tows (University of Cambridge)",
      source_url: "https://example.org",
      source_workbook: "TowTool_ContactLengthAndFrictionForce.xlsx",
      source_workbook_sha256: "b9c9af71be796d25",
      processed_table: "towtool_cof_measurements.csv",
      processed_table_sha256: "61ee1ec23b913272",
      dataset_sha256: "80b05ecd401af749",
      measurement_protocol: "ramp",
      material_domain: "carbon-fibre tow on glass",
      observation_count: 140,
      training_rows: 98,
      holdout_rows: 42,
      training_groups: 7,
      holdout_groups: 3,
      selected_model: "ridge_regression",
      seed: 417,
      range_basis: "min/max observed in training",
    },
    composite_targets_trained: false,
    note: "Point prediction only: no prediction interval is produced.",
    ...overrides,
  };
}

function mockFetch(body: unknown, ok = true, statusCode = 200) {
  const spy = vi.fn(async () => ({
    ok,
    status: statusCode,
    json: async () => body,
  }));
  vi.stubGlobal("fetch", spy);
  return spy;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CofPredictionForm", () => {
  it("submits the entered observation and renders the predicted COF", async () => {
    const fetchSpy = mockFetch(predictionBody());
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /predict coefficient of friction/i }));

    await waitFor(() => expect(screen.getByTestId("cof-prediction-value")).toHaveTextContent("0.4200"));
    expect(screen.getByText("IN DOMAIN")).toBeInTheDocument();
    expect(screen.getByText(/Composite targets trained by this response: no/)).toBeInTheDocument();

    const call = fetchSpy.mock.calls[0] as unknown as [string, RequestInit];
    const payload = JSON.parse(call[1].body as string);
    expect(payload.tow_type).toBe("T700-12k-50C");
    expect(payload.normal_load_n).toBe(10);
    expect(payload.nominal_pressure_mpa).toBe(payload.normal_load_n / payload.contact_area_mm2);
    expect(payload.log10_normal_load_n).toBeUndefined();
  });

  it("shows the external domain limitation and metrics after predicting", async () => {
    mockFetch(predictionBody());
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /predict coefficient of friction/i }));

    await screen.findByTestId("cof-prediction-value");
    expect(screen.getByText("Domain limitation")).toBeInTheDocument();
    expect(screen.getByText(/not a composite predictor/i)).toBeInTheDocument();
    expect(screen.getByText("Holdout MAE")).toBeInTheDocument();
  });

  it("surfaces out-of-domain flags returned by the API", async () => {
    mockFetch(
      predictionBody({
        domain_status: "OUT_OF_DOMAIN",
        out_of_domain_features: [
          {
            feature: "normal_load_n",
            unit: "N",
            value: 500,
            training_min: 0.07,
            training_max: 49.1,
            direction: "above_max",
            message: "normal_load_n=500 is outside the training range [0.0775, 49.15] N.",
          },
        ],
      }),
    );
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /predict coefficient of friction/i }));

    await screen.findByText("OUT OF DOMAIN");
    expect(screen.getByText(/normal_load_n=500 is outside the training range/)).toBeInTheDocument();
  });

  it("blocks a non-positive value before calling the API", async () => {
    const fetchSpy = mockFetch(predictionBody());
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    const loadInput = screen.getByLabelText("Normal load");
    await user.clear(loadInput);
    await user.type(loadInput, "0");
    await user.click(screen.getByRole("button", { name: /predict coefficient of friction/i }));

    expect(await screen.findByText(/must be greater than zero/i)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("surfaces an API error notice when the request fails", async () => {
    mockFetch({ detail: "External model artifacts failed provenance verification." }, false, 503);
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /predict coefficient of friction/i }));

    expect(await screen.findByText(/failed provenance verification/i)).toBeInTheDocument();
  });

  it("labels an accepted candidate as a physical test condition, not an optimum", async () => {
    mockFetch({
      model_id: "TOW-TOOL-COF-CAMBRIDGE",
      source_kind: "external",
      interpretation: "Candidate validation only.",
      results: [
        {
          candidate_id: "current-condition",
          accepted_for_physical_testing: true,
          out_of_domain_features: [],
          issues: [],
        },
      ],
    });
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /validate physical-test candidate/i }));

    expect(await screen.findByText("Candidate is within the recorded limits")).toBeInTheDocument();
    expect(screen.getByText(/not an optimum or validated recommendation/i)).toBeInTheDocument();
  });

  it("renders ranked candidate recommendations with caution notices and disclaimers", async () => {
    mockFetch({
      model_id: "TOW-TOOL-COF-CAMBRIDGE",
      source_kind: "external",
      target_criterion: "lowest_predicted_cof",
      interpretation: "These conditions are candidate points for laboratory testing.",
      causal_disclaimer: "No causal relationship is inferred.",
      reliability_notice: "Caution: The model has negative R² (-0.74) on held-out T700-12k-50C.",
      composite_targets_trained: false,
      recommendations: [
        {
          rank: 1,
          candidate_id: "candidate-1",
          conditions: {
            normal_load_n: 10.0,
            nominal_pressure_mpa: 0.0624,
            contact_width_mm: 6.75,
            contact_area_mm2: 160.3,
            contact_length_scanned_mm: 1452.0,
            contact_half_width_a_mm: 0.000029,
            percent_contact_length: 16.8,
            tow_type: "T700-12k-60E",
          },
          predicted_coefficient_of_friction: 0.385,
          is_model_estimate_not_measurement: true,
          recommendation_label: "Candidate condition for physical laboratory testing (not an established optimum)",
        },
      ],
    });
    const user = userEvent.setup();
    render(<CofPredictionForm schema={SCHEMA} />);

    await user.click(screen.getByRole("button", { name: /recommend physical-test conditions/i }));

    expect(await screen.findByTestId("cof-recommendations-panel")).toBeInTheDocument();
    expect(screen.getByText("Constrained physical-test candidates")).toBeInTheDocument();
    expect(screen.getByText(/negative R² \(-0.74\)/)).toBeInTheDocument();
    expect(screen.getByText(/No causal relationship is inferred/)).toBeInTheDocument();
    expect(screen.getByText("0.3850")).toBeInTheDocument();
    expect(screen.getByText(/Composite targets trained: no/)).toBeInTheDocument();
  });
});

