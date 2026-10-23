"use client";

import { AlertTriangle, ArrowRight, BookOpen, FileText, ShieldAlert } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { CofPredictionForm } from "@/components/cof-prediction-form";
import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { StatusBadge } from "@/components/status-badge";
import {
  API_BASE,
  api,
  type ExternalHoldoutSlice,
  type ExternalModelReport,
  type ModelStatus,
} from "@/lib/api";

export default function ModelsPage() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.modelStatus()
      .then(setStatus)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const report = status?.demo_report;
  const external = status?.external_model;
  const externalReport = external?.report ?? null;

  return (
    <>
      <PageHeading
        eyebrow="Model experience & transparency"
        title="Predictive Models & Scientific Evidence"
        description="Transparent machine-learning interfaces strictly bounded by verified scientific evidence, training domains, and held-out evaluation."
        action={
          <a
            href={api.getModelsPdfUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="button-secondary text-xs"
            title="Download formal model evaluation and provenance audit PDF"
          >
            <FileText size={15} aria-hidden="true" />
            Export Audit Report (PDF)
          </a>
        }
      />

      {/* Top Banner: Strict Model Boundaries */}
      <div className="mb-6">
        <Notice tone="warning" title="Model Separation & Experimental Target Gating">
          <p className="mb-1 text-xs leading-relaxed text-amber-950">
            AI-TriboTwin strictly separates <strong>(1) External Benchmark Models</strong>,{" "}
            <strong>(2) Synthetic Code Demonstrations</strong>, and{" "}
            <strong>(3) Blocked Experimental Composite Targets</strong>.
          </p>
          <p className="mb-0 text-xs text-amber-900 font-medium">
            The external friction model is evaluated only on Cambridge carbon-fibre tow-on-tool data. The original glass-fibre/epoxy composite targets remain strictly <code>BLOCKED / NO_GO</code>.
          </p>
        </Notice>
      </div>

      {error && (
        <div className="mb-5">
          <Notice tone="error" title="Model service error">
            {error}
          </Notice>
        </div>
      )}

      {loading ? (
        <div className="panel p-6 text-sm text-muted" role="status">
          Loading verified model manifests and evaluation reports…
        </div>
      ) : status ? (
        <div className="space-y-8">
          {/* TIER 1: EXTERNAL REAL-DATA CAMBRIDGE MODEL */}
          <ExternalModelSection
            external={external}
            report={externalReport}
            plotAvailable={external?.plot_available ?? false}
          />

          {/* TIER 2: SYNTHETIC CODE DEMONSTRATION */}
          <SyntheticDemoSection
            status={status.demo_status}
            report={report ?? null}
            plotAvailable={status.plot_available}
          />

          {/* TIER 3: BLOCKED COMPOSITE TARGETS GATING */}
          <BlockedCompositeTargetsSection targets={status.experimental_targets} />
        </div>
      ) : null}
    </>
  );
}

/* =========================================================================
   TIER 1: EXTERNAL CAMBRIDGE TOW-ON-TOOL MODEL SECTION
   ========================================================================= */
function ExternalModelSection({
  external,
  report,
  plotAvailable,
}: {
  external: ModelStatus["external_model"] | undefined;
  report: ExternalModelReport | null;
  plotAvailable: boolean;
}) {
  const statusValue = external?.status ?? "NOT_RUN";

  return (
    <section
      id="external-model"
      aria-label="External Cambridge benchmark model"
      className="panel p-6 border-l-4 border-l-blue-600"
    >
      {/* Header & Pillar Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-bold text-blue-800 tracking-wide uppercase">
              Tier 1 · External Benchmark
            </span>
            <span className="text-xs text-muted">Carbon-fibre tow-on-tool friction</span>
          </div>
          <h2 className="m-0 mt-1 text-lg font-bold text-ink">
            Cambridge Tow-on-Tool Friction Model ({report ? report.model_id : "TOW-TOOL-COF-CAMBRIDGE"})
          </h2>
          <p className="mb-0 mt-0.5 text-xs text-muted">
            Trained and held-out evaluated on University of Cambridge carbon-fibre friction data. Separate from AI-TriboTwin composite targets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/planning" className="button-secondary text-xs font-semibold">
            <span>Planning Workspace</span>
            <ArrowRight size={12} className="ml-1" />
          </Link>
          <StatusBadge status={statusValue} />
        </div>
      </div>

      {report ? (
        <>
          {/* Scientific Scope & Summary */}
          <div className="mt-4 rounded-lg bg-slate-50 p-4 border border-line">
            <h3 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
              Model Scope & Interpretation
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-ink">
              {report.interpretation}
            </p>
            <p className="mb-0 mt-1 text-xs text-muted">
              <strong>Measurement protocol:</strong> {report.measurement_protocol}
            </p>
          </div>

          {/* Dataset Identity & Provenance DL */}
          <dl className="mt-5 grid gap-x-6 gap-y-2.5 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <DetailRow label="Material Domain" value={report.material_domain} />
            <DetailRow label="Predicted Target" value={`${report.target} (${report.target_unit})`} />
            <DetailRow label="Source Dataset" value={report.source_name} />
            <DetailRow label="Source Workbook" value={report.source_workbook} />
            <DetailRow label="Workbook SHA-256" value={shortHash(report.source_workbook_sha256)} mono />
            <DetailRow label="Processed Table SHA-256" value={report.processed_table_sha256 ? shortHash(report.processed_table_sha256) : "Unavailable"} mono />
          </dl>

          {/* Primary Holdout Performance Metrics */}
          <div className="mt-6">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
                Verified Held-Out Evaluation Metrics (Source of Truth)
              </h3>
              <span className="text-[11px] text-muted font-mono">
                GroupShuffleSplit · 7 train / 3 holdout runs
              </span>
            </div>
            <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Selected Estimator" value={report.selected_model} sublabel={report.selection_basis} />
              <Metric label="Held-Out MAE" value={report.holdout_metrics.mae.toFixed(4)} sublabel={`Baseline: ${report.baseline_metrics.mae.toFixed(4)}`} />
              <Metric label="Held-Out RMSE" value={report.holdout_metrics.rmse.toFixed(4)} sublabel={`Baseline: ${report.baseline_metrics.rmse.toFixed(4)}`} />
              <Metric label="Held-Out R²" value={report.holdout_metrics.r2.toFixed(4)} sublabel={`Baseline: ${report.baseline_metrics.r2.toFixed(4)}`} />
            </div>
          </div>

          <p className="mb-0 mt-3 text-xs text-muted">
            Evaluated on {report.observation_count} total observations ({report.training_rows} training rows / {report.holdout_rows} held-out rows) across {report.training_groups + report.holdout_groups} labelled test runs.
            Held-out test sweeps: <span className="font-semibold text-ink">{report.holdout_group_ids.join(", ")}</span>.
          </p>

          {/* Stratified Breakdown: Tow Types (60E vs 50C) */}
          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            <HoldoutSliceTable
              title="Held-Out Generalization by Tow Type"
              slices={report.holdout_slices.by_tow_type}
            />
            <HoldoutSliceTable
              title="Held-Out Performance by Individual Run"
              slices={report.holdout_slices.by_test_run}
            />
          </div>

          {/* 50C Failure Investigation Warning */}
          {report.failure_investigation_50c && (
            <div className="mt-5 rounded-lg border border-amber-300 bg-amber-50/60 p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-800" />
                <h4 className="m-0 text-xs font-semibold uppercase tracking-wider text-amber-900">
                  Known Limitation · 50C Generalization Deficit ({report.failure_investigation_50c.held_out_run})
                </h4>
              </div>
              <ul className="mt-2 space-y-1 pl-4 text-xs leading-relaxed text-amber-950 list-disc">
                {report.failure_investigation_50c.findings.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
              <p className="mb-0 mt-2 text-xs font-semibold text-amber-900">
                Implication: {report.failure_investigation_50c.implication}
              </p>
            </div>
          )}

          {/* Specimen Independence Disclosure */}
          {report.specimen_independence_disclosure && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted">
                Specimen Independence Disclosure ({report.specimen_independence_disclosure.labelled_runs} labelled sweeps)
              </div>
              <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
                {report.specimen_independence_disclosure.statement}
              </p>
            </div>
          )}

          {/* Uncertainty Calibration Disclosure */}
          {report.uncertainty_assessment && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Prediction Interval Feasibility ({report.uncertainty_assessment.status})
                </span>
                <span className="text-[11px] font-semibold text-amber-800">Uncalibrated</span>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                <span className="font-semibold text-ink">Mathematical Floor:</span>{" "}
                {report.uncertainty_assessment.mathematical_requirement}
              </p>
              <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
                <span className="font-semibold text-ink">Scientific Validity:</span>{" "}
                {report.uncertainty_assessment.scientific_validity_distinction}
              </p>
            </div>
          )}

          {/* Candidate Cross-Validation Comparison Table */}
          <div className="mt-6">
            <h3 className="m-0 text-sm font-semibold text-ink">
              Candidate Estimator Comparison · Training-Fold Group Cross-Validation
            </h3>
            <div className="table-scroll mt-2">
              <table>
                <thead>
                  <tr>
                    <th>Candidate Estimator</th>
                    <th>Cross-Validation MAE (Mean ± SD)</th>
                    <th>CV RMSE (Mean)</th>
                    <th>CV R² (Mean)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.model_comparison).map(([name, metrics]) => (
                    <tr key={name} className={name === report.selected_model ? "bg-blue-50/40" : ""}>
                      <td className="font-semibold">
                        {name} {name === report.selected_model && <span className="text-blue-700 text-xs font-bold">(Selected)</span>}
                      </td>
                      <td>{metrics.cv_mae_mean.toFixed(4)} ± {metrics.cv_mae_std.toFixed(4)}</td>
                      <td>{metrics.cv_rmse_mean.toFixed(4)}</td>
                      <td>{metrics.cv_r2_mean.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Predictions Scatter Plot */}
          {plotAvailable && (
            <figure className="mt-6">
              <Image
                alt="Observed versus predicted external tow-on-tool coefficient of friction on held-out test runs"
                className="mx-auto max-h-[500px] max-w-full rounded-lg border border-line"
                src={`${API_BASE}/api/v1/models/external/predictions.png`}
                width={975}
                height={900}
                unoptimized
              />
              <figcaption className="mt-2 text-center text-xs text-muted">
                Observed versus predicted coefficient of friction on held-out Cambridge test sweeps.
              </figcaption>
            </figure>
          )}

          {/* Interactive Prediction Form & Recommendation Workspace */}
          {report.feature_schema && <CofPredictionForm schema={report.feature_schema} />}
        </>
      ) : (
        <p className="mb-0 mt-4 text-sm text-muted">
          The external model artifacts were not found in this environment. Run
          <span className="font-semibold"> python -m src.models.external_cof</span> to build and verify the external bundle.
        </p>
      )}
    </section>
  );
}

/* =========================================================================
   TIER 2: SYNTHETIC CODE DEMONSTRATION SECTION
   ========================================================================= */
function SyntheticDemoSection({
  status,
  report,
  plotAvailable,
}: {
  status: string;
  report: ModelStatus["demo_report"];
  plotAvailable: boolean;
}) {
  return (
    <section
      id="synthetic-demo"
      aria-label="Synthetic demonstration pipeline"
      className="panel p-6 border-l-4 border-l-slate-400"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold text-slate-700 tracking-wide uppercase">
              Tier 2 · Synthetic Demonstration
            </span>
            <span className="text-xs text-muted">Deterministic code fixture</span>
          </div>
          <h2 className="m-0 mt-1 text-lg font-bold text-ink">
            Synthetic Pipeline Demonstration (SYNTHETIC-DEMO)
          </h2>
          <p className="mb-0 mt-0.5 text-xs text-muted">
            A software pipeline test fixture verifying model serialization and group-split logic. Non-physical data with zero laboratory validity.
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50/80 p-3.5">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-slate-600" />
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            Software Pipeline Demonstration Only
          </span>
        </div>
        <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
          This model is trained purely on synthetic fixture data. It demonstrates cross-validation, artifact hashing,
          and model serialization. It is explicitly non-physical and cannot be used for engineering design or experimental inference.
        </p>
      </div>

      {report ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Selected Model" value={report.selected_model} />
            <Metric label="Synthetic Holdout MAE" value={report.holdout_metrics.mae.toFixed(4)} />
            <Metric label="Synthetic Holdout RMSE" value={report.holdout_metrics.rmse.toFixed(4)} />
            <Metric label="Synthetic Holdout R²" value={report.holdout_metrics.r2.toFixed(4)} />
          </div>

          <p className="mb-0 mt-3 text-xs text-muted">
            {report.training_rows} training rows across {report.training_groups} groups; {report.holdout_rows} held-out rows across {report.holdout_groups} groups; {report.cross_validation_folds}-fold cross validation.
          </p>

          {plotAvailable && (
            <figure className="mt-5">
              <Image
                alt="Observed versus predicted values for held-out synthetic groups"
                className="mx-auto max-h-[460px] max-w-full rounded-lg border border-line"
                src={`${API_BASE}/api/v1/models/demo/predictions.png`}
                width={975}
                height={900}
                unoptimized
              />
              <figcaption className="mt-2 text-center text-xs text-muted">
                Observed versus predicted synthetic responses on the held-out groups.
              </figcaption>
            </figure>
          )}
        </>
      ) : (
        <p className="mb-0 mt-4 text-sm text-muted">
          The synthetic demonstration report is unavailable. Run the training module to generate local demo artifacts.
        </p>
      )}
    </section>
  );
}

/* =========================================================================
   TIER 3: BLOCKED COMPOSITE TARGETS SECTION
   ========================================================================= */
function BlockedCompositeTargetsSection({
  targets,
}: {
  targets: ModelStatus["experimental_targets"];
}) {
  return (
    <section
      id="composite-targets"
      aria-label="Experimental target gates"
      className="panel p-6 border-l-4 border-l-red-600"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-800 tracking-wide uppercase">
              Tier 3 · Blocked / No Go
            </span>
            <span className="text-xs text-muted">AI-TriboTwin Composite Targets</span>
          </div>
          <h2 className="m-0 mt-1 text-lg font-bold text-ink">
            Experimental Target Readiness Gates
          </h2>
          <p className="mb-0 mt-0.5 text-xs text-muted">
            All original glass-fibre/epoxy composite targets are currently blocked pending evidence resolution. Predictions and optimization remain safely gated.
          </p>
        </div>
        <span className="rounded-full border border-red-300 bg-red-50 px-3 py-1 text-xs font-bold text-red-800">
          CURRENTLY BLOCKED
        </span>
      </div>

      <div className="mt-4 rounded-lg border border-red-200 bg-red-50/50 p-4">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 text-red-700 shrink-0" size={18} />
          <div className="text-xs leading-relaxed text-red-950">
            <span className="font-semibold block text-sm text-red-900 mb-1">
              Scientific Gate Enforced: Untrained Composite Targets
            </span>
            No model has been trained on AI-TriboTwin&apos;s glass-fibre/epoxy composite dataset. The composite prediction and optimization APIs
            are hard-gated by the scientific readiness register. Models will not be deployed for these targets until experimental group identities,
            material batch provenance, and wear measurement units are independently verified.
          </div>
        </div>
      </div>

      <div className="table-scroll mt-5">
        <table>
          <thead>
            <tr>
              <th>Target Property</th>
              <th>Gate Status</th>
              <th>Required Scientific Evidence</th>
            </tr>
          </thead>
          <tbody>
            {targets.map((target) => (
              <tr key={target.target_id}>
                <td className="font-semibold text-ink">{target.target_name}</td>
                <td>
                  <StatusBadge status={target.status} />
                </td>
                <td className="min-w-64 max-w-2xl text-xs leading-relaxed text-muted">
                  {target.required_evidence}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* =========================================================================
   HELPER COMPONENTS
   ========================================================================= */
function HoldoutSliceTable({
  title,
  slices,
}: {
  title: string;
  slices: Record<string, ExternalHoldoutSlice>;
}) {
  return (
    <div>
      <h4 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h4>
      <div className="table-scroll mt-2">
        <table>
          <thead>
            <tr>
              <th>Slice</th>
              <th>Rows</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>R²</th>
              <th>Mean Residual</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(slices).map(([name, metrics]) => (
              <tr key={name}>
                <td className="font-semibold">{name}</td>
                <td>{metrics.rows}</td>
                <td>{metrics.mae.toFixed(4)}</td>
                <td>{metrics.rmse.toFixed(4)}</td>
                <td className={`font-semibold ${metrics.r2 < 0 ? "text-amber-700" : "text-emerald-700"}`}>
                  {metrics.r2.toFixed(4)}
                </td>
                <td>{metrics.mean_residual.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</dt>
      <dd className={`mt-0.5 break-words ${mono ? "font-mono text-xs" : "text-sm text-ink"}`}>{value}</dd>
    </div>
  );
}

function shortHash(value: string): string {
  return value.length > 20 ? `${value.slice(0, 12)}…${value.slice(-8)}` : value;
}

function Metric({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3.5 border border-line">
      <div className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 break-words text-lg font-bold text-ink">{value}</div>
      {sublabel && <div className="mt-0.5 text-[11px] text-muted truncate" title={sublabel}>{sublabel}</div>}
    </div>
  );
}
