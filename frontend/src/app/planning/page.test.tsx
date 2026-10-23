import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PlanningPage from "./page";
import { api, type Experiment } from "@/lib/api";

const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      experiments: vi.fn(),
      createPlan: vi.fn(),
    },
  };
});

const mockPlans: Experiment[] = [
  {
    id: 1,
    experiment_id: "PLAN-CAND-01",
    record_status: "PLANNED",
    material_system_as_recorded: "T700-12k-60E",
    planned_by: "Test Engineer",
    composition_as_recorded: "Carbon fibre tow",
    composition_source_reference: "Cambridge tow dataset",
    replicate_group_id: "GRP-01",
    planned_conditions: {
      load_n: 15.0,
      sliding_velocity_m_per_s: 0.05,
      sliding_distance_m: 0.8,
      test_duration_min: 16,
    },
    measured_conditions: {},
    measurements: {},
    instrument_id: "INSTR-01",
    operator: "Operator A",
    experiment_date: "2026-10-23",
    source_artifact: "DOE Matrix",
    source_location: "Lab Shelf A",
    notes: "Candidate test design",
    recorded_at_utc: "2026-10-23T12:00:00Z",
    created_at_utc: "2026-10-23T12:00:00Z",
    import_sha256: "",
  },
];

describe("PlanningPage (Unified Planning & Registry Integration)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.delete("candidate_id");
    mockSearchParams.delete("material");
    mockSearchParams.delete("load_n");
    vi.mocked(api.experiments).mockResolvedValue(mockPlans);
  });

  it("renders planning form, cues, and saved plans with registry links", async () => {
    render(<PlanningPage />);

    expect(screen.getByText("Proposed conditions")).toBeInTheDocument();
    expect(screen.getByText(/A plan is not an AI recommendation/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("PLAN-CAND-01 · T700-12k-60E")).toBeInTheDocument();
      expect(screen.getByText("Inspect")).toBeInTheDocument();
      expect(screen.getByText("View all in registry")).toBeInTheDocument();
    });
  });

  it("submits planned experiment and persists as PLANNED", async () => {
    vi.mocked(api.createPlan).mockResolvedValue(mockPlans[0]);

    render(<PlanningPage />);

    fireEvent.change(screen.getByLabelText(/Experiment plan ID/i), {
      target: { value: "PLAN-NEW-99" },
    });
    fireEvent.change(screen.getByLabelText(/Material system exactly as proposed/i), {
      target: { value: "Ti-6Al-4V" },
    });
    fireEvent.change(screen.getByLabelText(/Composition \/ preparation description/i), {
      target: { value: "Standard annealed formulation" },
    });
    fireEvent.change(screen.getByLabelText(/Load \(N\)/i), {
      target: { value: "25" },
    });

    const submitBtn = screen.getByRole("button", { name: /save planned experiment/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.createPlan).toHaveBeenCalledWith(
        expect.objectContaining({
          experiment_id: "PLAN-NEW-99",
          record_status: "PLANNED",
          material_system_as_recorded: "Ti-6Al-4V",
        })
      );
      expect(screen.getByText(/persisted as PLANNED/i)).toBeInTheDocument();
    });
  });

  it("handles pre-population from URL search parameters", async () => {
    mockSearchParams.set("candidate_id", "CAND-REC-42");
    mockSearchParams.set("material", "T700-12k-50C");
    mockSearchParams.set("load_n", "35.5");

    render(<PlanningPage />);

    expect(screen.getByText(/Candidate pre-populated from model recommendation/i)).toBeInTheDocument();

    const idInput = screen.getByLabelText(/Experiment plan ID/i) as HTMLInputElement;
    const materialInput = screen.getByLabelText(/Material system exactly as proposed/i) as HTMLInputElement;
    const loadInput = screen.getByLabelText(/Load \(N\)/i) as HTMLInputElement;

    expect(idInput.value).toBe("PLAN-CAND-REC-42");
    expect(materialInput.value).toBe("T700-12k-50C");
    expect(loadInput.value).toBe("35.5");
  });
});
