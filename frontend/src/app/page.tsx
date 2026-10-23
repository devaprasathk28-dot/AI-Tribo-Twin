"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Beaker,
  BrainCircuit,
  Database,
  FileSpreadsheet,
  Gauge,
  ListChecks,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Notice } from "@/components/notice";
import { ReadinessChart } from "@/components/readiness-chart";
import { StatusBadge } from "@/components/status-badge";

import {
  api,
  type Experiment,
  type ExperimentCounts,
  type ModelStatus,
  type Readiness,
} from "@/lib/api";

export default function OverviewPage() {
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [counts, setCounts] = useState<ExperimentCounts | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [recentExperiments, setRecentExperiments] = useState<Experiment[]>([]);
  const [healthStatus, setHealthStatus] = useState<{ status: string; database: string } | null>(null);

  const [loading, setLoading] = useState(true);
  const [healthError, setHealthError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadDashboardData = useCallback(() => {
    setLoading(true);
    setErrorMessage("");

    Promise.allSettled([
      api.health(),
      api.readiness(),
      api.counts(),
      api.modelStatus(),
      api.experiments(),
    ]).then(([healthRes, readinessRes, countsRes, modelStatusRes, experimentsRes]) => {
      if (healthRes.status === "fulfilled") {
        setHealthStatus(healthRes.value);
        setHealthError(false);
      } else {
        setHealthError(true);
      }

      if (readinessRes.status === "fulfilled") {
        setReadiness(readinessRes.value);
      }

      if (countsRes.status === "fulfilled") {
        setCounts(countsRes.value);
      }

      if (modelStatusRes.status === "fulfilled") {
        setModelStatus(modelStatusRes.value);
      }

      if (experimentsRes.status === "fulfilled") {
        setRecentExperiments(experimentsRes.value.slice(0, 5));
      }

      // Check if all primary data endpoints failed
      if (
        readinessRes.status === "rejected" &&
        countsRes.status === "rejected" &&
        modelStatusRes.status === "rejected"
      ) {
        setErrorMessage(
          "Could not connect to the AI-TriboTwin FastAPI backend. Ensure the backend service is running on the configured API port."
        );
      }

      setLoading(false);
    });
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const externalModel = modelStatus?.external_model;
  const externalReport = externalModel?.report;

  return (
    <div className="space-y-8">
      {/* Page Header with live system status badge & quick actions */}
      <div className="flex flex-col justify-between gap-4 border-b border-line pb-6 md:flex-row md:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
              Engineering Platform · Tribo-Informatics
            </span>
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <span
                className={`h-2 w-2 rounded-full ${
                  healthStatus?.status === "ok"
                    ? "bg-emerald-500"
                    : healthError
                      ? "bg-rose-500"
                      : "bg-amber-400"
                }`}
              />
              <span>
                {healthStatus?.status === "ok"
                  ? "Backend Operational"
                  : healthError
                    ? "Backend Offline"
                    : "Connecting…"}
              </span>
            </div>
          </div>
          <h1 className="m-0 mt-1.5 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Research & Experimentation Dashboard
          </h1>
          <p className="mb-0 mt-2 max-w-3xl text-sm leading-relaxed text-muted">
            Traceable repository for experimental tribology records, tow-on-tool friction modeling,
            and evidence-gated target verification.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            aria-label="Refresh dashboard metrics"
            className="button-outline"
            onClick={loadDashboardData}
            title="Refresh dashboard data"
            type="button"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} aria-hidden="true" />
            <span>Refresh</span>
          </button>
          <Link className="button-secondary" href="/experiments?new=1">
            <Plus size={15} aria-hidden="true" />
            <span>New Record</span>
          </Link>
          <Link className="button-primary" href="/models">
            <Sparkles size={15} aria-hidden="true" />
            <span>Tow COF Prediction</span>
          </Link>
        </div>
      </div>

      {/* Backend Disconnection Notice if applicable */}
      {errorMessage && (
        <Notice tone="error" title="Backend Connection Unavailable">
          {errorMessage}
        </Notice>
      )}

      {/* Scientific Safeguards Warning */}
      <section aria-label="Scientific readiness warning">
        <Notice tone="warning" title="Composite Experimental Target Gate Remains Closed (Sprint 9)">
          All 4 glass-fibre/epoxy composite targets (COF, Wear Rate, Specific Wear Rate, Wear Volume Loss)
          remain strictly <strong>BLOCKED</strong>. Sprint 9 evidence recovery established physical test condition
          contradictions (DOCX sliding distances of 50–100 m vs published 100–300 m) and 100% missing primary records.
          The Cambridge model is an external tow-on-tool carbon-fibre model and cannot predict composite outcomes.
        </Notice>
      </section>

      {/* Summary Metrics Grid */}
      <section aria-label="System summary metrics" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Metric 1: Model Availability */}
        <div className="panel p-5">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wide">Prediction Models</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-accent">
              <BrainCircuit size={17} aria-hidden="true" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
            {loading ? "—" : "1 Active"}
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted">
            <span className="font-medium text-emerald-700">1 External (Cambridge)</span>
            <span>·</span>
            <span className="font-medium text-amber-700">4 Gated</span>
          </div>
          <div className="mt-3 border-t border-line pt-2 text-[11px] text-muted">
            Composite targets require primary records
          </div>
        </div>

        {/* Metric 2: External Tow COF Model */}
        <div className="panel p-5">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wide">External Tow COF</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 text-sky-700">
              <Gauge size={17} aria-hidden="true" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
            {loading ? "—" : externalReport ? `R² ${externalReport.holdout_metrics.r2.toFixed(3)}` : "Available"}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted">
            <span className="font-medium text-slate-700">
              {externalReport ? `${externalReport.observation_count} observations` : "Tow-on-tool"}
            </span>
            <span>·</span>
            <span className="text-emerald-700">Evaluated</span>
          </div>
          <div className="mt-3 border-t border-line pt-2 text-[11px] text-muted">
            <Link className="font-medium text-accent hover:underline" href="/models">
              Run interactive predictions →
            </Link>
          </div>
        </div>

        {/* Metric 3: Experiment Records */}
        <div className="panel p-5">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wide">Experiment Records</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-warning">
              <Beaker size={17} aria-hidden="true" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
            {loading ? "—" : String(counts?.total ?? 0)}
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted">
            <span className="font-medium text-emerald-700">{counts?.MEASURED ?? 0} Measured</span>
            <span>·</span>
            <span className="font-medium text-slate-600">{counts?.PLANNED ?? 0} Planned</span>
          </div>
          <div className="mt-3 border-t border-line pt-2 text-[11px] text-muted">
            <Link className="font-medium text-accent hover:underline" href="/experiments">
              Browse experiment table →
            </Link>
          </div>
        </div>

        {/* Metric 4: System Health */}
        <div className="panel p-5">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wide">System Health</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
              <Activity size={17} aria-hidden="true" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
            {loading ? "Checking…" : healthStatus?.status === "ok" ? "Operational" : "Degraded"}
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted">
            <span>FastAPI: {healthStatus?.status ?? "offline"}</span>
            <span>·</span>
            <span>DB: {healthStatus?.database ?? "unavailable"}</span>
          </div>
          <div className="mt-3 border-t border-line pt-2 text-[11px] text-muted">
            PostgreSQL & API endpoints live
          </div>
        </div>
      </section>

      {/* Workspace Feature Shortcuts (Monolith AI style) */}
      <section aria-label="Research workspace modules">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="m-0 text-lg font-bold tracking-tight text-ink">Research Workspace Modules</h2>
            <p className="mb-0 mt-0.5 text-xs text-muted">Direct access to core computational tribology tools</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          <WorkspaceCard
            badge="1 Model Ready"
            badgeTone="emerald"
            description="Score candidate conditions with the Cambridge tow-on-tool model, explore recommendations, and review evaluation metrics."
            href="/models"
            icon={<BrainCircuit size={20} className="text-accent" aria-hidden="true" />}
            title="Models & Prediction"
          />
          <WorkspaceCard
            badge="Verified Records"
            badgeTone="slate"
            description="Explore verified observations, test conditions, friction and wear measurements with full traceability and filter options."
            href="/experiments"
            icon={<Beaker size={20} className="text-sky-700" aria-hidden="true" />}
            title="Experiment Records"
          />
          <WorkspaceCard
            badge="Interactive Visuals"
            badgeTone="emerald"
            description="Explore dynamic friction & wear distributions, timelines, condition scatter plots, and formulation breakdowns."
            href="/analytics"
            icon={<BarChart3 size={20} className="text-teal-700" aria-hidden="true" />}
            title="Analytics & Trends"
          />
          <WorkspaceCard
            badge="DOE Matrix"
            badgeTone="slate"
            description="Design prospective test conditions and experimental series without confusing planned parameters with measured results."
            href="/planning"
            icon={<ListChecks size={20} className="text-emerald-700" aria-hidden="true" />}
            title="Experiment Planning"
          />
          <WorkspaceCard
            badge="SHA-256 Validated"
            badgeTone="amber"
            description="Import experimental CSV files, inspect schemas, check missingness, and verify cryptographic hashes before committing to the database."
            href="/imports"
            icon={<Database size={20} className="text-amber-700" aria-hidden="true" />}
            title="Data Intake & CSV"
          />
        </div>
      </section>

      {/* Honest Model Separation Matrix (Three Distinct Tiers) */}
      <section aria-label="Model registry status and boundaries" className="panel p-6">
        <div className="border-b border-line pb-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="m-0 text-lg font-bold tracking-tight text-ink">
                Model Classification & Boundary Governance
              </h2>
              <p className="mb-0 mt-1 text-xs text-muted">
                Strict scientific demarcation between external experimental models, synthetic benchmarks, and gated composite targets
              </p>
            </div>
            <div className="flex items-center gap-1.5 rounded-full border border-line bg-slate-50 px-3 py-1 text-xs text-slate-600">
              <ShieldCheck size={14} className="text-accent" aria-hidden="true" />
              <span>Zero Model Conflation Guaranteed</span>
            </div>
          </div>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-3">
          {/* Tier 1: External Cambridge Model */}
          <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-slate-300">
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-800">
                  REAL EXPERIMENTAL DATA (EXTERNAL)
                </span>
                <span className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                  ACTIVE
                </span>
              </div>
              <h3 className="m-0 mt-3 text-base font-bold text-ink">
                Cambridge Tow-on-Tool Friction
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                Trained on 140 experimental tow-on-tool observations of carbon-fibre tow sliding over glass tooling.
                Evaluated on 3 held-out test runs with leave-one-run-out sensitivity analysis.
              </p>
              <div className="mt-4 space-y-2 rounded-lg bg-slate-50 p-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted">Target:</span>
                  <span className="font-semibold text-ink">COF (Tow-on-tool)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Held-out R²:</span>
                  <span className="font-semibold text-emerald-700">0.7826</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Held-out MAE:</span>
                  <span className="font-semibold text-ink">0.1340</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-muted">Domain Notice:</span>
                  <span className="font-medium text-amber-800">Carbon-fibre only</span>
                </div>
              </div>
            </div>
            <div className="mt-5 border-t border-line pt-4">
              <Link
                className="flex items-center justify-between text-xs font-semibold text-accent hover:underline"
                href="/models"
              >
                <span>Interactive prediction form</span>
                <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </div>

          {/* Tier 2: Synthetic Demonstration */}
          <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-slate-300">
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700">
                  SYNTHETIC PIPELINE BENCHMARK
                </span>
                <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                  DEMO ONLY
                </span>
              </div>
              <h3 className="m-0 mt-3 text-base font-bold text-ink">
                Synthetic Architecture Pipeline
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                Deterministic synthetic dataset used exclusively to verify group cross-validation splits,
                artifact hashing, and backend model persistence without real physics.
              </p>
              <div className="mt-4 space-y-2 rounded-lg bg-slate-50 p-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted">Target:</span>
                  <span className="font-semibold text-ink">SYNTHETIC-DEMO</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Purpose:</span>
                  <span className="font-semibold text-slate-700">Pipeline verification</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Physical Validity:</span>
                  <span className="font-semibold text-rose-700">None (Deterministic)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Model Type:</span>
                  <span className="font-medium text-slate-700">Random Forest Regressor</span>
                </div>
              </div>
            </div>
            <div className="mt-5 border-t border-line pt-4">
              <Link
                className="flex items-center justify-between text-xs font-semibold text-accent hover:underline"
                href="/models#synthetic-demo"
              >
                <span>Inspect demo evaluation metrics</span>
                <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </div>

          {/* Tier 3: Original Composite Targets (BLOCKED) */}
          <div className="flex flex-col justify-between rounded-xl border border-rose-200 bg-rose-50/30 p-5 shadow-card transition hover:border-rose-300">
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-800">
                  ORIGINAL COMPOSITE (GFRE)
                </span>
                <span className="inline-flex items-center rounded-full border border-rose-300 bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-800">
                  BLOCKED (NO_GO)
                </span>
              </div>
              <h3 className="m-0 mt-3 text-base font-bold text-ink">
                Glass-Fibre/Epoxy Targets
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-rose-950">
                Four response variables (COF, Wear Rate, Specific Wear Rate, Wear Volume Loss). Gated by
                the Step 4.10 scientific readiness protocol following Sprint 9 evidence recovery.
              </p>
              <div className="mt-4 space-y-2 rounded-lg bg-white/80 p-3 text-xs border border-rose-200">
                <div className="flex justify-between">
                  <span className="text-rose-900">Targets:</span>
                  <span className="font-semibold text-rose-950">COF, Wear, SWR, WVL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-rose-900">Sprint 9 Status:</span>
                  <span className="font-semibold text-rose-700">Traceability Failure</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-rose-900">Missing Data:</span>
                  <span className="font-semibold text-rose-700">100% SWR & WVL Blank</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-rose-900">Action:</span>
                  <span className="font-medium text-rose-900">Author Inquiry Required</span>
                </div>
              </div>
            </div>
            <div className="mt-5 border-t border-rose-200 pt-4">
              <span className="text-xs font-semibold text-rose-800">
                Gated: Training strictly prohibited
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Target Readiness Gate Table & Distribution */}
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(340px,0.85fr)]">
        <div className="panel">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div>
              <h2 className="m-0 text-base font-bold text-ink">Original Composite Readiness Gates</h2>
              <p className="mb-0 mt-1 text-xs text-muted">Evidence requirement register per Step 4.10 & Sprint 9</p>
            </div>
            <ShieldAlert size={18} className="text-warning" aria-hidden="true" />
          </div>
          {loading ? (
            <div className="p-6 text-sm text-muted" role="status">
              Loading target evidence register…
            </div>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Target Response</th>
                    <th>Gate Status</th>
                    <th>Blocking Scientific Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {(readiness?.targets ?? []).map((target) => (
                    <tr key={target.target_id}>
                      <td className="min-w-44 font-semibold text-ink">{target.target_name}</td>
                      <td>
                        <StatusBadge status={target.status} />
                      </td>
                      <td className="min-w-64 max-w-xl text-xs leading-relaxed text-muted">
                        {target.required_evidence}
                      </td>
                    </tr>
                  ))}
                  {!readiness?.targets.length && (
                    <tr>
                      <td className="py-8 text-center text-muted" colSpan={3}>
                        No readiness gate records available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
          <div className="border-t border-line px-5 py-3 text-xs text-muted">
            {readiness?.warning ?? "Readiness gate register loaded from project evidence."}
          </div>
        </div>

        {/* Readiness Distribution Chart */}
        <div className="panel p-5">
          <div>
            <h2 className="m-0 text-base font-bold text-ink">Target Gate Distribution</h2>
            <p className="mb-0 mt-1 text-xs text-muted">Counts of target clearance statuses</p>
          </div>
          <div className="mt-3">
            {loading ? (
              <div className="chart-empty">Loading distribution…</div>
            ) : (
              <ReadinessChart targets={readiness?.targets ?? []} />
            )}
          </div>
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-muted">
            All four original composite targets are currently classified as <strong>BLOCKED</strong>.
            Predictions cannot be generated until primary laboratory records and run-level mappings are provided.
          </div>
        </div>
      </section>

      {/* Recent Activity / Live Records Preview */}
      <section aria-label="Recent experimental activity" className="panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
          <div>
            <h2 className="m-0 text-base font-bold text-ink">Recent Database Activity</h2>
            <p className="mb-0 mt-1 text-xs text-muted">
              Live experiment records and planned runs currently stored in PostgreSQL
            </p>
          </div>
          <Link className="button-outline" href="/experiments">
            <span>View all experiments</span>
            <ArrowRight size={13} aria-hidden="true" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-muted">Loading experiment activity…</div>
        ) : recentExperiments.length > 0 ? (
          <div className="table-scroll mt-3">
            <table>
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Status</th>
                  <th>Material System</th>
                  <th>Planned / Measured Load</th>
                  <th>Velocity</th>
                  <th>Recorded At</th>
                </tr>
              </thead>
              <tbody>
                {recentExperiments.map((exp) => (
                  <tr key={exp.experiment_id}>
                    <td className="font-mono text-xs font-semibold text-ink">
                      <Link
                        href={`/experiments?query=${encodeURIComponent(exp.experiment_id)}`}
                        className="text-accent hover:underline"
                        title="Inspect in experiment registry"
                      >
                        {exp.experiment_id}
                      </Link>
                    </td>
                    <td>
                      <StatusBadge status={exp.record_status} />
                    </td>
                    <td className="text-xs text-ink">
                      <Link
                        href={`/analytics?material=${encodeURIComponent(exp.material_system_as_recorded)}`}
                        className="text-ink hover:text-accent hover:underline font-medium"
                        title={`View analytics for ${exp.material_system_as_recorded}`}
                      >
                        {exp.material_system_as_recorded || "—"}
                      </Link>
                    </td>
                    <td className="text-xs text-muted">
                      {exp.measured_conditions?.load_n !== undefined
                        ? `${exp.measured_conditions.load_n} N (measured)`
                        : exp.planned_conditions?.load_n !== undefined
                          ? `${exp.planned_conditions.load_n} N (planned)`
                          : "—"}
                    </td>
                    <td className="text-xs text-muted">
                      {exp.measured_conditions?.sliding_velocity_m_per_s !== undefined
                        ? `${exp.measured_conditions.sliding_velocity_m_per_s} m/s`
                        : exp.planned_conditions?.sliding_velocity_m_per_s !== undefined
                          ? `${exp.planned_conditions.sliding_velocity_m_per_s} m/s`
                          : "—"}
                    </td>
                    <td className="text-xs text-muted">{exp.recorded_at_utc ? exp.recorded_at_utc.slice(0, 10) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
              <FileSpreadsheet size={24} aria-hidden="true" />
            </div>
            <h3 className="m-0 mt-3 text-sm font-semibold text-ink">No Experiment Records Stored</h3>
            <p className="mb-0 mt-1 max-w-md text-xs leading-relaxed text-muted">
              The PostgreSQL database does not currently contain experimental observations.
              You can import verified source records or plan physical test series using the links below.
            </p>
            <div className="mt-4 flex gap-3">
              <Link className="button-secondary" href="/imports">
                <Database size={14} aria-hidden="true" />
                <span>Import CSV Template</span>
              </Link>
              <Link className="button-primary" href="/experiments?new=1">
                <Plus size={14} aria-hidden="true" />
                <span>Add Record Manually</span>
              </Link>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function WorkspaceCard({
  title,
  description,
  href,
  icon,
  badge,
  badgeTone,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  badgeTone?: "emerald" | "slate" | "amber";
}) {
  const toneClasses = {
    emerald: "bg-emerald-50 text-emerald-800 border-emerald-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
  }[badgeTone ?? "slate"];

  return (
    <Link
      className="card-interactive flex flex-col justify-between"
      href={href}
    >
      <div>
        <div className="flex items-center justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50 border border-line shadow-sm">
            {icon}
          </div>
          {badge && (
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${toneClasses}`}>
              {badge}
            </span>
          )}
        </div>
        <h3 className="m-0 mt-3 text-sm font-bold text-ink">{title}</h3>
        <p className="mb-0 mt-1.5 text-xs leading-relaxed text-muted">{description}</p>
      </div>
      <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-accent">
        <span>Open module</span>
        <ArrowRight size={13} aria-hidden="true" />
      </div>
    </Link>
  );
}
