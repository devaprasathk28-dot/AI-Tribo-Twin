import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "./shell";
import { api } from "@/lib/api";

// Mock next/navigation
const mockPathname = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
}));

// Mock api.health
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      health: vi.fn(),
    },
  };
});

describe("AppShell Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPathname.mockReturnValue("/");
    vi.mocked(api.health).mockResolvedValue({ status: "ok", database: "ok" });
  });

  it("renders the product branding and primary navigation links", async () => {
    render(
      <AppShell>
        <div>Test Page Content</div>
      </AppShell>
    );

    // Check branding
    expect(screen.getAllByText("AI-TriboTwin").length).toBeGreaterThanOrEqual(1);

    // Check primary navigation items
    expect(screen.getAllByText("Overview").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Models & Prediction").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Experiment Records").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Analytics & Visuals").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Experiment Planning").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Data Intake").length).toBeGreaterThanOrEqual(1);

    // Check children rendered
    expect(screen.getByText("Test Page Content")).toBeInTheDocument();
  });

  it("highlights the active route based on the pathname", async () => {
    mockPathname.mockReturnValue("/models");

    render(
      <AppShell>
        <div>Models View</div>
      </AppShell>
    );

    const activeLinks = screen.getAllByRole("link", { name: /Models & Prediction/i });
    const desktopActiveLink = activeLinks.find((link) => link.getAttribute("aria-current") === "page");
    expect(desktopActiveLink).toBeDefined();
    expect(desktopActiveLink).toHaveAttribute("aria-current", "page");
  });

  it("toggles the desktop sidebar collapse state", async () => {
    render(
      <AppShell>
        <div>Content</div>
      </AppShell>
    );

    const collapseButton = screen.getByRole("button", { name: /collapse sidebar/i });
    expect(collapseButton).toBeInTheDocument();

    // Click collapse
    fireEvent.click(collapseButton);

    // Now button should say expand sidebar
    expect(screen.getByRole("button", { name: /expand sidebar/i })).toBeInTheDocument();

    // Click expand
    fireEvent.click(screen.getByRole("button", { name: /expand sidebar/i }));
    expect(screen.getByRole("button", { name: /collapse sidebar/i })).toBeInTheDocument();
  });

  it("opens and closes the mobile navigation drawer", async () => {
    render(
      <AppShell>
        <div>Mobile Test Content</div>
      </AppShell>
    );

    const mobileMenuButton = screen.getByRole("button", { name: /open navigation menu/i });
    expect(mobileMenuButton).toBeInTheDocument();

    // Open drawer
    fireEvent.click(mobileMenuButton);

    // Mobile drawer should be visible with role="dialog"
    const drawer = screen.getByRole("dialog", { name: /mobile navigation drawer/i });
    expect(drawer).toBeInTheDocument();

    // Close button inside drawer
    const closeButton = screen.getByRole("button", { name: /close navigation/i });
    fireEvent.click(closeButton);

    // Drawer should have transition class indicating closed state
    expect(drawer).toHaveClass("-translate-x-full");
  });

  it("renders live backend health status from API", async () => {
    vi.mocked(api.health).mockResolvedValue({ status: "ok", database: "ok" });

    render(
      <AppShell>
        <div>Health Test</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/online/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("displays offline status when backend health check fails", async () => {
    vi.mocked(api.health).mockRejectedValue(new Error("Network Error"));

    render(
      <AppShell>
        <div>Offline Test</div>
      </AppShell>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/offline/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
