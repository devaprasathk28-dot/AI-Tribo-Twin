import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AnalyticsPage from "./page";
import { api, type AnalyticsResponse } from "@/lib/api";

// Mock the API client
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      analytics: vi.fn(),
    },
  };
});

const mockAnalyticsData: AnalyticsResponse = {
  kpis: {
    total_records: 120,
    measured_records: 100,
    planned_records: 20,
    distinct_materials_count: 5,
    records_with_cof: 95,
    records_with_wear: 80,
  },
  timeline: [
    { period: "2026-08", total: 30, measured: 25, planned: 5 },
    { period: "2026-09", total: 50, measured: 45, planned: 5 },
    { period: "2026-10", total: 40, measured: 30, planned: 10 },
  ],
  materials: [
    { material_system: "Ti-6Al-4V", total_count: 60, measured_count: 50, planned_count: 10 },
    { material_system: "CFRP Tow", total_count: 40, measured_count: 35, planned_count: 5 },
    { material_system: "Si3N4 Ceramic", total_count: 20, measured_count: 15, planned_count: 5 },
  ],
  distinct_material_names: ["CFRP Tow", "Si3N4 Ceramic", "Ti-6Al-4V"],
  cof_distribution: {
    has_data: true,
    observation_count: 95,
    stats: {
      count: 95,
      min: 0.12,
      max: 0.45,
      mean: 0.285,
      median: 0.278,
      unit: "dimensionless",
    },
    bins: [
      { bin_start: 0.12, bin_end: 0.2, bin_label: "0.120–0.200", count: 15 },
      { bin_start: 0.2, bin_end: 0.3, bin_label: "0.200–0.300", count: 50 },
      { bin_start: 0.3, bin_end: 0.45, bin_label: "0.300–0.450", count: 30 },
    ],
    unit: "dimensionless",
    note: "Distribution computed from 95 verified laboratory measurements.",
  },
  wear_distribution: {
    has_data: true,
    total_wear_observations: 80,
    groups: [
      {
        measurement_name: "specific wear rate",
        unit: "mm3/N-m",
        observation_count: 50,
        stats: {
          count: 50,
          min: 1.1e-5,
          max: 4.8e-5,
          mean: 2.3e-5,
          median: 2.1e-5,
          unit: "mm3/N-m",
        },
        bins: [
          { bin_start: 1.1e-5, bin_end: 2.5e-5, bin_label: "1.1e-5–2.5e-5", count: 30 },
          { bin_start: 2.5e-5, bin_end: 4.8e-5, bin_label: "2.5e-5–4.8e-5", count: 20 },
        ],
      },
      {
        measurement_name: "wear volume loss",
        unit: "mm3",
        observation_count: 30,
        stats: {
          count: 30,
          min: 0.5,
          max: 3.2,
          mean: 1.4,
          median: 1.2,
          unit: "mm3",
        },
        bins: [
          { bin_start: 0.5, bin_end: 1.8, bin_label: "0.500–1.800", count: 20 },
          { bin_start: 1.8, bin_end: 3.2, bin_label: "1.800–3.200", count: 10 },
        ],
      },
    ],
    note: "Computed from 80 observations across 2 distinct, un-combined measurement-unit pairs.",
  },
  cof_relationships: {
    has_sufficient_data: true,
    observation_count: 95,
    points: [
      {
        experiment_id: "EXP-01",
        material_system: "Ti-6Al-4V",
        load_n: 10,
        sliding_velocity_m_per_s: 0.5,
        sliding_distance_m: 100,
        coefficient_of_friction: 0.25,
      },
      {
        experiment_id: "EXP-02",
        material_system: "Ti-6Al-4V",
        load_n: 20,
        sliding_velocity_m_per_s: 0.5,
        sliding_distance_m: 100,
        coefficient_of_friction: 0.28,
      },
      {
        experiment_id: "EXP-03",
        material_system: "Ti-6Al-4V",
        load_n: 30,
        sliding_velocity_m_per_s: 0.5,
        sliding_distance_m: 100,
        coefficient_of_friction: 0.31,
      },
    ],
    scientific_disclaimer:
      "Descriptive visualization only. Descriptive correlation between test conditions and friction does not imply causation.",
  },
  filter_echo: {
    material_system: null,
    date_from: null,
    date_to: null,
    record_status: null,
  },
};

describe("AnalyticsPage (Engineering Analytics & Visualizations)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.analytics).mockResolvedValue(mockAnalyticsData);
  });

  it("renders truth-based KPI cards and scientific safeguard notices", async () => {
    render(<AnalyticsPage />);

    expect(screen.getByRole("status")).toHaveTextContent(/loading/i);

    await waitFor(() => {
      expect(screen.getByText("Total Records")).toBeInTheDocument();
      expect(screen.getAllByText("120").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("100").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("20").length).toBeGreaterThanOrEqual(1);
    });

    // Check scientific disclaimer notice
    expect(screen.getByText(/Scientific Safeguard Notice:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/BLOCKED/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders charts and distribution statistics with explicit units", async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Experiment Records Over Time")).toBeInTheDocument();
      expect(screen.getByText("State Segregation")).toBeInTheDocument();
      expect(screen.getByText("Experiment Count by Material System")).toBeInTheDocument();
      expect(screen.getByText(/Measured Friction Coefficient \(COF\) Distribution/i)).toBeInTheDocument();
      expect(screen.getByText(/Measured Wear Distribution/i)).toBeInTheDocument();
      expect(screen.getByText(/Relationship: Measured Friction vs\. Test Conditions/i)).toBeInTheDocument();
    });

    // Verify statistical summary cards are displayed
    expect(screen.getByText("0.285")).toBeInTheDocument(); // COF mean
    expect(screen.getByText("Unit: dimensionless")).toBeInTheDocument();
  });

  it("switches wear measurement groups without mixing incompatible units", async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/specific wear rate \(mm3\/N-m\)/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole("button", { name: /wear volume loss/i })).toBeInTheDocument();
    });

    // Click on the second wear group button
    const volLossBtn = screen.getByRole("button", { name: /wear volume loss/i });
    fireEvent.click(volLossBtn);

    await waitFor(() => {
      expect(screen.getByText("N = 30")).toBeInTheDocument();
    });
  });

  it("switches X-axis test condition variables on the relationship scatter plot", async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Normal Load (N)")).toBeInTheDocument();
      expect(screen.getByText("Sliding Speed (m/s)")).toBeInTheDocument();
      expect(screen.getByText("Sliding Distance (m)")).toBeInTheDocument();
    });

    // Switch to Sliding Speed
    const speedBtn = screen.getByText("Sliding Speed (m/s)");
    fireEvent.click(speedBtn);

    // Verify button is active
    expect(speedBtn.className).toContain("bg-accent");
  });

  it("handles filter changes and reloads analytics data", async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("120")).toBeInTheDocument();
    });

    // Select Material filter
    const materialSelect = screen.getByLabelText(/material system/i);
    fireEvent.change(materialSelect, { target: { value: "Ti-6Al-4V" } });

    await waitFor(() => {
      expect(api.analytics).toHaveBeenCalledWith(
        expect.objectContaining({ material: "Ti-6Al-4V" })
      );
    });

    // Select Status filter
    const statusSelect = screen.getByLabelText(/record status/i);
    fireEvent.change(statusSelect, { target: { value: "MEASURED" } });

    await waitFor(() => {
      expect(api.analytics).toHaveBeenCalledWith(
        expect.objectContaining({ status: "MEASURED" })
      );
    });
  });

  it("displays an honest empty state when no records match filters", async () => {
    vi.mocked(api.analytics).mockResolvedValue({
      ...mockAnalyticsData,
      kpis: {
        total_records: 0,
        measured_records: 0,
        planned_records: 0,
        distinct_materials_count: 0,
        records_with_cof: 0,
        records_with_wear: 0,
      },
      timeline: [],
      materials: [],
      cof_distribution: {
        has_data: false,
        observation_count: 0,
        stats: null,
        bins: [],
        unit: "dimensionless",
        note: "No friction measurements recorded.",
      },
      wear_distribution: {
        has_data: false,
        total_wear_observations: 0,
        groups: [],
        note: "No wear measurements recorded.",
      },
      cof_relationships: {
        has_sufficient_data: false,
        observation_count: 0,
        points: [],
        scientific_disclaimer: "Descriptive only.",
      },
    });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText(/No experimental records match the current filters/i)).toBeInTheDocument();
    });
  });
});
