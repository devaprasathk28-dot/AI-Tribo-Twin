import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportsPage from "./page";
import { api, type ImportHistoryItem, type ImportPreviewResult } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      importHistory: vi.fn(),
      previewImport: vi.fn(),
      confirmImport: vi.fn(),
    },
  };
});

const mockHistory: ImportHistoryItem[] = [
  {
    id: 1,
    sha256: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    filename: "verified_batch_01.csv",
    content_type: "text/csv",
    size_bytes: 4096,
    row_count: 24,
    format_name: "experiment-intake",
    created_at_utc: "2026-10-23T12:00:00Z",
    validation_outcome: "VALID",
    errors_count: 0,
    warnings_count: 0,
  },
];

const mockPreviewClean: ImportPreviewResult = {
  filename: "new_intake.csv",
  sha256: "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
  size_bytes: 2048,
  format_name: "experiment-intake",
  row_count: 10,
  valid: true,
  errors: [],
  warnings: [],
  preview_rows: [
    { experiment_id: "EXP-101", material_system_as_recorded: "Ti-6Al-4V" },
  ],
  can_confirm_import: true,
  accepted_rows: 10,
  duplicate_rows: 0,
  rejected_rows: 0,
  duplicate_experiment_ids: [],
  is_duplicate_artifact: false,
};

const mockPreviewWithDuplicates: ImportPreviewResult = {
  filename: "duplicates.csv",
  sha256: "9999888877776666555544443333222211110000ffffeeeeddddccccbbbbaaaa",
  size_bytes: 3072,
  format_name: "experiment-intake",
  row_count: 5,
  valid: true,
  errors: [],
  warnings: [
    {
      code: "DUPLICATE_EXPERIMENT_IDS",
      message: "2 experiment identifier(s) collide with existing database records.",
    },
  ],
  preview_rows: [
    { experiment_id: "COLLIDE-01", material_system_as_recorded: "CFRP Tow" },
  ],
  can_confirm_import: false,
  accepted_rows: 3,
  duplicate_rows: 2,
  rejected_rows: 0,
  duplicate_experiment_ids: ["COLLIDE-01", "COLLIDE-02"],
  is_duplicate_artifact: false,
};

describe("ImportsPage (Safe CSV Import & Audit History)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.importHistory).mockResolvedValue(mockHistory);
  });

  it("renders upload dropzone, scientific notices, and import history", async () => {
    render(<ImportsPage />);

    expect(screen.getByText("Select an experiment CSV")).toBeInTheDocument();
    expect(screen.getByText(/Two-step import/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("verified_batch_01.csv")).toBeInTheDocument();
      expect(screen.getByText("VALID")).toBeInTheDocument();
    });
  });

  it("handles clean CSV preview and permits transactional confirmation", async () => {
    vi.mocked(api.previewImport).mockResolvedValue(mockPreviewClean);
    vi.mocked(api.confirmImport).mockResolvedValue({
      sha256: mockPreviewClean.sha256,
      records_imported: 10,
      message: "10 records persisted.",
    });

    render(<ImportsPage />);

    // Simulate file input change
    const file = new File(["dummy content"], "new_intake.csv", { type: "text/csv" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("READY TO COMMIT")).toBeInTheDocument();
      expect(screen.getByText("Total Rows")).toBeInTheDocument();
      expect(screen.getByText("Accepted Rows")).toBeInTheDocument();
    });

    // Confirm import
    const confirmBtn = screen.getByRole("button", { name: /confirm import/i });
    expect(confirmBtn).not.toBeDisabled();
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.confirmImport).toHaveBeenCalledWith(file, mockPreviewClean.sha256);
      expect(screen.getByText(/10 records persisted/i)).toBeInTheDocument();
    });
  });

  it("displays duplicate warnings, row breakdown, and blocks confirmation on collisions", async () => {
    vi.mocked(api.previewImport).mockResolvedValue(mockPreviewWithDuplicates);

    render(<ImportsPage />);

    const file = new File(["duplicate content"], "duplicates.csv", { type: "text/csv" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("CONFIRMATION BLOCKED")).toBeInTheDocument();
      expect(screen.getAllByText("COLLIDE-01").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("COLLIDE-02")).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: /confirm import/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("displays duplicate artifact warning when same SHA-256 is uploaded", async () => {
    vi.mocked(api.previewImport).mockResolvedValue({
      ...mockPreviewClean,
      is_duplicate_artifact: true,
      can_confirm_import: false,
    });

    render(<ImportsPage />);

    const file = new File(["same content"], "same.csv", { type: "text/csv" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Duplicate CSV artifact detected/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: /confirm import/i });
    expect(confirmBtn).toBeDisabled();
  });
});
