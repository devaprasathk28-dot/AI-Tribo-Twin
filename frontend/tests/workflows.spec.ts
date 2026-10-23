import { expect, test, type Page, type Route } from "@playwright/test";

type MockRecord = {
  id: number;
  experiment_id: string;
  record_status: "PLANNED" | "MEASURED";
  material_system_as_recorded: string;
  planned_by: string;
  composition_as_recorded: string;
  composition_source_reference: string;
  replicate_group_id: string;
  planned_conditions: Record<string, number>;
  measured_conditions: Record<string, number>;
  measurements: Record<string, unknown>;
  instrument_id: string;
  operator: string;
  experiment_date: string | null;
  source_artifact: string;
  source_location: string;
  notes: string;
  recorded_at_utc: string;
  created_at_utc: string;
  import_sha256: string;
};

const targets = [
  ["COF", "Coefficient of friction"],
  ["WEAR_RATE", "Wear rate"],
  ["SPECIFIC_WEAR_RATE", "Specific wear rate"],
  ["WEAR_VOLUME_LOSS", "Wear volume loss"],
].map(([target_id, target_name]) => ({
  target_id,
  target_name,
  status: "BLOCKED",
  evidence: "Required measurements and traceability remain unresolved.",
  required_evidence: "Verified row-level measurements, units, and run mapping are required.",
}));

async function mockWorkspaceApi(page: Page) {
  const records: MockRecord[] = [];
  let confirmedImports = 0;
  let measuredPayload: Record<string, unknown> | undefined;

  await page.route("**/api/v1/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path === "/api/v1/health" && method === "GET") {
      await route.fulfill({ json: { status: "ok", database: "ok" } });
      return;
    }
    if (path === "/api/v1/readiness" && method === "GET") {
      await route.fulfill({
        json: {
          targets,
          warning: "Readiness reflects documented evidence; no predictive model is available.",
        },
      });
      return;
    }
    if (path === "/api/v1/experiments/count" && method === "GET") {
      const planned = records.filter((record) => record.record_status === "PLANNED").length;
      const measured = records.filter((record) => record.record_status === "MEASURED").length;
      await route.fulfill({
        json: { PLANNED: planned, MEASURED: measured, total: records.length },
      });
      return;
    }
    if (path === "/api/v1/experiments" && method === "GET") {
      const status = new URL(request.url()).searchParams.get("record_status");
      await route.fulfill({
        json: status
          ? records.filter((record) => record.record_status === status)
          : records,
      });
      return;
    }
    if (
      (path === "/api/v1/experiments" || path === "/api/v1/plans") &&
      method === "POST"
    ) {
      const payload = request.postDataJSON() as Record<string, unknown>;
      if (path === "/api/v1/experiments") measuredPayload = payload;
      const record: MockRecord = {
        id: records.length + 1,
        experiment_id: String(payload.experiment_id),
        record_status: payload.record_status === "MEASURED" ? "MEASURED" : "PLANNED",
        material_system_as_recorded: String(payload.material_system_as_recorded ?? ""),
        planned_by: String(payload.planned_by ?? ""),
        composition_as_recorded: String(payload.composition_as_recorded ?? ""),
        composition_source_reference: String(payload.composition_source_reference ?? ""),
        replicate_group_id: String(payload.replicate_group_id ?? ""),
        planned_conditions: (payload.planned_conditions as Record<string, number> | undefined) ?? {},
        measured_conditions: (payload.measured_conditions as Record<string, number> | undefined) ?? {},
        measurements: (payload.measurements as Record<string, unknown> | undefined) ?? {},
        instrument_id: String(payload.instrument_id ?? ""),
        operator: String(payload.operator ?? ""),
        experiment_date: typeof payload.experiment_date === "string" ? payload.experiment_date : null,
        source_artifact: String(payload.source_artifact ?? ""),
        source_location: String(payload.source_location ?? ""),
        notes: String(payload.notes ?? ""),
        recorded_at_utc: "2026-01-01T00:00:00Z",
        created_at_utc: "2026-01-01T00:00:00Z",
        import_sha256: "",
      };
      records.push(record);
      await route.fulfill({ status: 201, json: record });
      return;
    }
    if (path === "/api/v1/imports/preview" && method === "POST") {
      await route.fulfill({
        json: {
          filename: "experiment-records.csv",
          sha256: "a".repeat(64),
          size_bytes: 128,
          format_name: "experiment-template",
          row_count: 1,
          valid: true,
          errors: [],
          warnings: [],
          preview_rows: [{ experiment_id: "LAB-001", record_status: "MEASURED" }],
          can_confirm_import: true,
        },
      });
      return;
    }
    if (path === "/api/v1/imports/confirm" && method === "POST") {
      confirmedImports += 1;
      await route.fulfill({
        json: {
          sha256: "a".repeat(64),
          records_imported: 1,
          message: "Import saved.",
        },
      });
      return;
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unexpected API request: ${method} ${path}` },
    });
  });

  return {
    get confirmedImports() {
      return confirmedImports;
    },
    get measuredPayload() {
      return measuredPayload;
    },
  };
}

test("overview shows unresolved target gates and no predictive release", async ({ page }) => {
  await mockWorkspaceApi(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Research workspace" })).toBeVisible();
  await expect(page.getByText("Predictive AI is not released")).toBeVisible();
  await expect(page.locator("tbody").getByText("BLOCKED")).toHaveCount(4);
  await expect(page.getByText("Verified row-level measurements, units, and run mapping are required.")).toHaveCount(4);
});

test("a measured observation is entered with its source provenance", async ({ page }) => {
  const api = await mockWorkspaceApi(page);
  await page.goto("/experiments?new=1");

  await page.getByLabel("Experiment ID").fill("LAB-001");
  await page.getByLabel("Material system as recorded").fill("Composite as recorded by lab");
  await page.getByLabel("Composition as recorded").fill("Composition pending source confirmation");
  await page.getByLabel("Composition source reference").fill("Lab notebook, page 12");
  await page.getByLabel("Measured load (N)").fill("10");
  await page.getByLabel("Measured velocity (m/s)").fill("0.2");
  await page.getByLabel("Measured distance (m)").fill("100");
  await page.getByLabel("COF value").fill("0.31");
  await page.getByLabel("COF unit as recorded").fill("dimensionless");
  await page.getByLabel("Source artifact").fill("lab-run-001.pdf");
  await page.getByLabel("Page / table / row / run ID").fill("Run 001");
  await page.getByRole("button", { name: "Save measured record" }).click();

  await expect(page.getByText("Record saved")).toBeVisible();
  await expect(page.getByText("Measured record and provenance were saved. It has not changed target readiness.")).toBeVisible();
  expect(api.measuredPayload).toMatchObject({
    experiment_id: "LAB-001",
    record_status: "MEASURED",
    source_artifact: "lab-run-001.pdf",
    source_location: "Run 001",
    measurements: {
      coefficient_of_friction: { value: 0.31, unit_as_recorded: "dimensionless" },
    },
  });
});

test("a proposed test is saved as a plan without measured responses", async ({ page }) => {
  await mockWorkspaceApi(page);
  await page.goto("/planning");

  await page.getByLabel("Experiment plan ID").fill("PLAN-001");
  await page.getByLabel("Prepared by").fill("Researcher");
  await page.getByLabel("Material system exactly as proposed").fill("Candidate material as proposed");
  await page.getByLabel("Composition / preparation description").fill("Awaiting protocol confirmation");
  await page.getByLabel("Load (N)").fill("10");
  await page.getByLabel("Sliding velocity (m/s)").fill("0.2");
  await page.getByLabel("Sliding distance (m)").fill("100");
  await page.getByLabel("Duration (min)").fill("30");
  await page.getByRole("button", { name: "Save planned experiment" }).click();

  await expect(page.getByText("Plan saved")).toBeVisible();
  await expect(page.getByText("PLAN-001 · Candidate material as proposed")).toBeVisible();
  await expect(page.getByText("No validated response model, uncertainty estimate, or optimum is available.")).toBeVisible();
});

test("CSV import requires explicit confirmation after preview", async ({ page }) => {
  const api = await mockWorkspaceApi(page);
  await page.goto("/imports");

  await page.locator('input[type="file"]').setInputFiles({
    name: "experiment-records.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("experiment_id,record_status\nLAB-001,MEASURED\n"),
  });

  await expect(page.getByText("SCHEMA VALID")).toBeVisible();
  await expect(page.getByRole("heading", { name: "First rows (preview only)" })).toBeVisible();
  expect(api.confirmedImports).toBe(0);

  await page.getByRole("button", { name: "Confirm import" }).click();
  await expect(page.getByText("Import saved")).toBeVisible();
  await expect(page.getByText(/1 records persisted/)).toBeVisible();
  expect(api.confirmedImports).toBe(1);
});
