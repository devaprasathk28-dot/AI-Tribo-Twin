import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExperimentsPage from "./page";
import { api, type Experiment } from "@/lib/api";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

// Mock the API client
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      experiments: vi.fn(),
      getExperiment: vi.fn(),
      createExperiment: vi.fn(),
      updateExperiment: vi.fn(),
      deleteExperiment: vi.fn(),
      createPlan: vi.fn(),
    },
  };
});

const mockExperiments: Experiment[] = [
  {
    id: 1,
    experiment_id: "EXP-MEASURED-01",
    record_status: "MEASURED",
    material_system_as_recorded: "Ti-6Al-4V / Al2O3",
    planned_by: "",
    composition_as_recorded: "Grade 5 Titanium with alumina counterface",
    composition_source_reference: "Lab Notebook Vol 4, p. 12",
    replicate_group_id: "REP-GRP-A",
    planned_conditions: {},
    measured_conditions: {
      load_n: 10,
      sliding_velocity_m_per_s: 0.5,
      sliding_distance_m: 100,
      test_duration_min: 10,
    },
    measurements: {
      coefficient_of_friction: {
        value: 0.32,
        unit_as_recorded: "dimensionless",
      },
      wear_measurement_name_as_recorded: "specific wear rate",
      wear_measurement: {
        value: 1.45e-5,
        unit_as_recorded: "mm3/N-m",
      },
    },
    instrument_id: "PIN-ON-DISK-01",
    operator: "Dr. A. Tribologist",
    experiment_date: "2026-09-15",
    source_artifact: "cambridge_trials.csv",
    source_location: "Row 15, Run 3",
    notes: "Steady state friction achieved after 200 cycles.",
    recorded_at_utc: "2026-09-15T10:00:00Z",
    created_at_utc: "2026-09-15T10:00:00Z",
    import_sha256: "abcdef1234567890",
  },
  {
    id: 2,
    experiment_id: "EXP-PLANNED-02",
    record_status: "PLANNED",
    material_system_as_recorded: "CFRP Tow / Steel Tool",
    planned_by: "Engineering Team",
    composition_as_recorded: "T700-12k carbon tow",
    composition_source_reference: "Manufacturer datasheet 2026",
    replicate_group_id: "T700-STUDY",
    planned_conditions: {
      load_n: 25,
      sliding_velocity_m_per_s: 1.0,
      sliding_distance_m: 500,
    },
    measured_conditions: {},
    measurements: {},
    instrument_id: "",
    operator: "",
    experiment_date: null,
    source_artifact: "",
    source_location: "",
    notes: "Planned run for next sprint validation.",
    recorded_at_utc: "2026-10-01T12:00:00Z",
    created_at_utc: "2026-10-01T12:00:00Z",
    import_sha256: "",
  },
];

describe("ExperimentsPage (Complete Experiment Management)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.experiments).mockResolvedValue(mockExperiments);
  });

  it("renders registry table with experiment records and metrics", async () => {
    render(<ExperimentsPage />);

    expect(screen.getByRole("status")).toHaveTextContent(/loading/i);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
      expect(screen.getByText("EXP-PLANNED-02")).toBeInTheDocument();
    });

    expect(screen.getByText(/Total matching records:/)).toBeInTheDocument();
    expect(screen.getAllByText("Ti-6Al-4V / Al2O3").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("CFRP Tow / Steel Tool").length).toBeGreaterThanOrEqual(1);
  });

  it("filters records by status", async () => {
    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const statusFilter = screen.getByLabelText(/filter by status/i);
    fireEvent.change(statusFilter, { target: { value: "MEASURED" } });

    await waitFor(() => {
      expect(api.experiments).toHaveBeenCalledWith(
        expect.objectContaining({ status: "MEASURED" })
      );
    });
  });

  it("searches records via the query input", async () => {
    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search id, material/i);
    fireEvent.change(searchInput, { target: { value: "Titanium" } });

    await waitFor(() => {
      expect(api.experiments).toHaveBeenCalledWith(
        expect.objectContaining({ query: "Titanium" })
      );
    });
  });

  it("opens Detail Modal on clicking View and displays scientific fields and provenance", async () => {
    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const viewButton = screen.getByLabelText("View record EXP-MEASURED-01");
    fireEvent.click(viewButton);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText(/Database ID #1/)).toBeInTheDocument();
      expect(screen.getAllByText("Grade 5 Titanium with alumina counterface").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Lab Notebook Vol 4, p. 12")).toBeInTheDocument();
      expect(screen.getByText("PIN-ON-DISK-01")).toBeInTheDocument();
      expect(screen.getByText("Dr. A. Tribologist")).toBeInTheDocument();
      expect(screen.getByText("Steady state friction achieved after 200 cycles.")).toBeInTheDocument();
    });

    // Close modal
    const closeBtn = screen.getByLabelText("Close detail modal");
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("opens Edit Modal, modifies record, and calls api.updateExperiment", async () => {
    vi.mocked(api.updateExperiment).mockResolvedValue({
      ...mockExperiments[0],
      notes: "Updated test notes",
    });

    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const editBtn = screen.getByLabelText("Edit record EXP-MEASURED-01");
    fireEvent.click(editBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Edit EXP-MEASURED-01")).toBeInTheDocument();
    });

    const notesInput = screen.getByLabelText(/notes/i);
    fireEvent.change(notesInput, { target: { value: "Updated test notes" } });

    const submitBtn = screen.getByRole("button", { name: /save changes/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.updateExperiment).toHaveBeenCalledWith(
        "EXP-MEASURED-01",
        expect.objectContaining({
          notes: "Updated test notes",
        })
      );
    });
  });

  it("opens Delete Confirmation Modal and calls api.deleteExperiment on confirmation", async () => {
    vi.mocked(api.deleteExperiment).mockResolvedValue({
      message: "Experiment record deleted",
      experiment_id: "EXP-MEASURED-01",
    });

    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const deleteBtn = screen.getByLabelText("Delete record EXP-MEASURED-01");
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByRole("alertdialog")).toBeInTheDocument();
      expect(screen.getByText(/confirm deletion/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: /confirm delete/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.deleteExperiment).toHaveBeenCalledWith("EXP-MEASURED-01");
    });
  });

  it("opens Create Modal and submits a new measured experiment", async () => {
    vi.mocked(api.createExperiment).mockResolvedValue(mockExperiments[0]);

    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const newBtn = screen.getByRole("button", { name: /new experiment/i });
    fireEvent.click(newBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Create Experiment Record")).toBeInTheDocument();
    });

    // Fill form
    fireEvent.change(screen.getByLabelText(/experiment id \*/i), { target: { value: "EXP-NEW-99" } });
    fireEvent.change(screen.getByLabelText(/material system as recorded \*/i), { target: { value: "Si3N4 / Steel" } });
    fireEvent.change(screen.getByLabelText(/composition as recorded \*/i), { target: { value: "Hot-pressed silicon nitride" } });
    fireEvent.change(screen.getByLabelText(/composition source reference \*/i), { target: { value: "Spec Ref 1" } });
    fireEvent.change(screen.getByLabelText(/load \(n\) \*/i), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText(/velocity \(m\/s\) \*/i), { target: { value: "1.5" } });
    fireEvent.change(screen.getByLabelText(/distance \(m\) \*/i), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText(/cof value \*/i), { target: { value: "0.22" } });
    fireEvent.change(screen.getByLabelText(/source artifact \*/i), { target: { value: "ceramic_test.csv" } });
    fireEvent.change(screen.getByLabelText(/page \/ table \/ run id \*/i), { target: { value: "Table 1" } });

    const form = screen.getByRole("dialog").querySelector("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(api.createExperiment).toHaveBeenCalledWith(
        expect.objectContaining({
          experiment_id: "EXP-NEW-99",
          record_status: "MEASURED",
          material_system_as_recorded: "Si3N4 / Steel",
        })
      );
    });
  });

  it("includes active filter query parameters in CSV export link", async () => {
    render(<ExperimentsPage />);

    await waitFor(() => {
      expect(screen.getByText("EXP-MEASURED-01")).toBeInTheDocument();
    });

    const exportLink = screen.getByTitle(/export currently filtered records to csv/i);
    expect(exportLink.getAttribute("href")).toContain("/api/v1/exports/experiments.csv");

    // Apply status filter
    const statusFilter = screen.getByLabelText(/filter by status/i);
    fireEvent.change(statusFilter, { target: { value: "PLANNED" } });

    await waitFor(() => {
      expect(exportLink.getAttribute("href")).toContain("record_status=PLANNED");
    });
  });
});
