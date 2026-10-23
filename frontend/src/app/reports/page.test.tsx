import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import ReportsPage from "@/app/reports/page";

describe("ReportsPage (Engineering Reports & Export)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders page heading, description, and standards notice", () => {
    render(<ReportsPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: /engineering reports & export/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/documentation & audit/i)).toBeInTheDocument();
    expect(
      screen.getByText(/stable report identifiers/i),
    ).toBeInTheDocument();
  });

  it("renders all four primary report generation cards", () => {
    render(<ReportsPage />);

    expect(
      screen.getByRole("heading", { level: 2, name: /experiment registry summary report/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /engineering analytics summary report/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /model evaluation & provenance audit/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /individual experiment engineering report/i }),
    ).toBeInTheDocument();
  });

  it("provides PDF and CSV download actions for registry and analytics", () => {
    render(<ReportsPage />);

    expect(
      screen.getByRole("button", { name: /download registry report \(pdf\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /export registry records \(csv\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /download analytics summary \(pdf\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /export analytics kpis \(csv\)/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /download model audit report \(pdf\)/i }),
    ).toBeInTheDocument();
  });

  it("shows an error when generating single experiment PDF with empty ID", () => {
    render(<ReportsPage />);

    const generateBtn = screen.getByRole("button", { name: /generate pdf/i });
    fireEvent.click(generateBtn);

    expect(screen.getByText(/please enter a valid experiment id/i)).toBeInTheDocument();
  });

  it("displays the composite target hard gate disclosure", () => {
    render(<ReportsPage />);

    expect(
      screen.getByText(/composite targets remain safely blocked pending evidence resolution/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /scientific integrity & report generation standards/i }),
    ).toBeInTheDocument();
  });
});
