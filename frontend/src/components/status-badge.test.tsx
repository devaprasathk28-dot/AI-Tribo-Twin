import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./status-badge";

describe("StatusBadge", () => {
  it("makes blocked readiness explicit", () => {
    render(<StatusBadge status="BLOCKED" />);
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
  });

  it("normalizes status labels", () => {
    render(<StatusBadge status="received_unreviewed" />);
    expect(screen.getByText("RECEIVED UNREVIEWED")).toBeInTheDocument();
  });
});
