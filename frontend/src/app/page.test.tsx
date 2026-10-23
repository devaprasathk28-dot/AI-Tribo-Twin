import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import OverviewPage from "./page";
import { api, type Experiment, type ExperimentCounts, type ModelStatus, type Readiness } from "@/lib/api";

// Mock the API client
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      health: vi.fn(),
      readiness: vi.fn(),
      counts: vi.fn(),
      modelStatus: vi.fn(),
      experiments: vi.fn(),
    },
  };
});

const mockReadinessData: Readiness = {
  warning: "All 4 composite targets remain blocked.",
  targets: [
    {
      target_id: "TARGET-COF",
      target_name: "Coefficient of Friction (COF)",
      status: "BLOCKED",
      evidence: "Physical test condition contradictions",
      required_evidence: "Author-backed mapping and primary laboratory records",
    },
    {
      target_id: "TARGET-WEAR",
      target_name: "Wear rate",
      status: "BLOCKED",
      evidence: "Heterogeneous table headings",
      required_evidence: "Calibration definition and unified units",
    },
  ],
};

const mockCountsData: ExperimentCounts = {
  total: 108,
  MEASURED: 108,
  PLANNED: 0,
};

const mockModelStatusData: ModelStatus = {
  demo_status: "EVALUATED_SYNTHETIC_DEMO",
  training_source: "synthetic_fixture_only",
  experimental_model_trained: false,
  demo_report: null,
  plot_available: true,
  experimental_targets: mockReadinessData.targets,
  external_model: {
    status: "EVALUATED_EXTERNAL_COF",
    plot_available: true,
    report: {
      status: "EVALUATED_EXTERNAL_COF",
      model_id: "TOW-TOOL-COF-CAMBRIDGE",
      source_kind: "external",
      is_ai_tribotwin_model: false,
      material_domain: "Carbon fibre tow on glass tool",
      source_name: "University of Cambridge",
      source_url: "https://example.com",
      source_workbook: "Cambridge_Tow_Data.xlsx",
      source_workbook_sha256: "abc1234567890",
      processed_table_sha256: null,
      dataset_sha256: "def1234567890",
      observation_count: 140,
      training_rows: 98,
      holdout_rows: 42,
      training_groups: 7,
      holdout_groups: 3,
      holdout_group_ids: ["T700-12k-50C-T1"],
      cross_validation_folds: 5,
      selected_model: "RandomForestRegressor",
      target: "Tow_COF",
      target_unit: "dimensionless",
      model_comparison: {},
      holdout_metrics: { mae: 0.1340, rmse: 0.2263, r2: 0.7826 },
      baseline_metrics: { mae: 0.12, rmse: 0.15, r2: 0.0 },
      holdout_slices: { by_tow_type: {}, by_test_run: {} },
      residual_analysis: {
        residual_definition: "prediction - observed",
        mean_residual: 0.0012,
        baseline_mean_residual: 0.02,
        interpretation: "Unbiased",
      },
      group_count_limitation: "10 labelled test runs",
      uncertainty_assessment: {
        status: "NOT_CALIBRATED",
        prediction_intervals_produced: false,
        reason: "Insufficient runs for conformal guarantees",
      },
      caveats: ["Carbon-fibre tow only"],
      interpretation: "External model evaluated.",
    },
  },
};

const mockExperimentsData: Experiment[] = [
  {
    id: 1,
    experiment_id: "EXP-001",
    record_status: "MEASURED",
    material_system_as_recorded: "FeTiO3:SiO2",
    planned_by: "Researcher",
    composition_as_recorded: "5 wt%",
    composition_source_reference: "Ref",
    replicate_group_id: "G1",
    planned_conditions: { load_n: 10, sliding_velocity_m_per_s: 0.5 },
    measured_conditions: { load_n: 10, sliding_velocity_m_per_s: 0.5 },
    measurements: { cof: 0.352 },
    instrument_id: "POD-01",
    operator: "Lab Tech",
    experiment_date: "2026-01-15",
    source_artifact: "DOCX",
    source_location: "Table 1",
    notes: "Verified row",
    recorded_at_utc: "2026-01-15T10:00:00Z",
    created_at_utc: "2026-01-15T10:00:00Z",
    import_sha256: "hash123",
  },
];

describe("OverviewPage (Dashboard)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.health).mockResolvedValue({ status: "ok", database: "ok" });
    vi.mocked(api.readiness).mockResolvedValue(mockReadinessData);
    vi.mocked(api.counts).mockResolvedValue(mockCountsData);
    vi.mocked(api.modelStatus).mockResolvedValue(mockModelStatusData);
    vi.mocked(api.experiments).mockResolvedValue(mockExperimentsData);
  });

  it("renders the dashboard header, title, and quick action links", async () => {
    render(<OverviewPage />);

    expect(
      screen.getByRole("heading", { name: /Research & Experimentation Dashboard/i })
    ).toBeInTheDocument();

    expect(screen.getByRole("link", { name: /New Record/i })).toHaveAttribute(
      "href",
      "/experiments?new=1"
    );
    expect(screen.getByRole("link", { name: /Tow COF Prediction/i })).toHaveAttribute(
      "href",
      "/models"
    );
  });

  it("renders truthful summary cards with real counts and metrics", async () => {
    render(<OverviewPage />);

    await waitFor(() => {
      // Metric 1: 1 Active
      expect(screen.getByText("1 Active")).toBeInTheDocument();
      // Metric 2: R² 0.783
      expect(screen.getByText(/R² 0.783/i)).toBeInTheDocument();
      // Metric 3: 108 records
      expect(screen.getByText("108")).toBeInTheDocument();
      // Metric 4: System health Operational
      expect(screen.getByText("Operational")).toBeInTheDocument();
    });
  });

  it("accurately separates the three model tiers with honest boundaries", async () => {
    render(<OverviewPage />);

    await waitFor(() => {
      // Tier 1: External Cambridge Model
      expect(
        screen.getByRole("heading", { name: /Cambridge Tow-on-Tool Friction/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/REAL EXPERIMENTAL DATA \(EXTERNAL\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Carbon-fibre only/i)).toBeInTheDocument();

      // Tier 2: Synthetic Pipeline Demonstration
      expect(
        screen.getByRole("heading", { name: /Synthetic Architecture Pipeline/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/SYNTHETIC PIPELINE BENCHMARK/i)).toBeInTheDocument();
      expect(screen.getByText(/None \(Deterministic\)/i)).toBeInTheDocument();

      // Tier 3: Original Composite Targets (BLOCKED)
      expect(
        screen.getByRole("heading", { name: /Glass-Fibre\/Epoxy Targets/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/ORIGINAL COMPOSITE \(GFRE\)/i)).toBeInTheDocument();
      expect(screen.getAllByText(/BLOCKED \(NO_GO\)/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("renders functional workspace module shortcuts", async () => {
    render(<OverviewPage />);

    // Modules
    const modelsShortcut = screen.getByRole("link", { name: /Models & Prediction/i });
    expect(modelsShortcut).toHaveAttribute("href", "/models");

    const experimentsShortcut = screen.getByRole("link", { name: /Experiment Records/i });
    expect(experimentsShortcut).toHaveAttribute("href", "/experiments");

    const planningShortcut = screen.getByRole("link", { name: /Experiment Planning/i });
    expect(planningShortcut).toHaveAttribute("href", "/planning");

    const importsShortcut = screen.getByRole("link", { name: /Data Intake & CSV/i });
    expect(importsShortcut).toHaveAttribute("href", "/imports");
  });

  it("renders recent experimental activity when records exist", async () => {
    render(<OverviewPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-001")).toBeInTheDocument();
      expect(screen.getByText("FeTiO3:SiO2")).toBeInTheDocument();
    });
  });

  it("renders an honest empty state when no experiments exist", async () => {
    vi.mocked(api.experiments).mockResolvedValue([]);

    render(<OverviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/No Experiment Records Stored/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /Import CSV Template/i })).toBeInTheDocument();
    });
  });

  it("handles backend API errors gracefully without crashing", async () => {
    vi.mocked(api.health).mockRejectedValue(new Error("Network Error"));
    vi.mocked(api.readiness).mockRejectedValue(new Error("503 Service Unavailable"));
    vi.mocked(api.counts).mockRejectedValue(new Error("503 Service Unavailable"));
    vi.mocked(api.modelStatus).mockRejectedValue(new Error("503 Service Unavailable"));
    vi.mocked(api.experiments).mockRejectedValue(new Error("503 Service Unavailable"));

    render(<OverviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Connection Unavailable/i)).toBeInTheDocument();
      expect(screen.getByText(/Degraded/i)).toBeInTheDocument();
    });
  });
});
