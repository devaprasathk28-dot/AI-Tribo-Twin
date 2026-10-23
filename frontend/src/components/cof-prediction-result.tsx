import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Notice } from "@/components/notice";
import type { CofPredictionResponse } from "@/lib/api";

function shortHash(value: string): string {
  return value.length > 20 ? `${value.slice(0, 12)}…${value.slice(-8)}` : value;
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}

const CONDITION_UNITS: Record<string, { label: string; unit: string }> = {
  tow_type: { label: "Tow type", unit: "" },
  normal_load_n: { label: "Normal load", unit: "N" },
  nominal_pressure_mpa: { label: "Nominal pressure", unit: "MPa" },
  contact_width_mm: { label: "Contact width", unit: "mm" },
  contact_area_mm2: { label: "Contact area", unit: "mm²" },
  contact_length_scanned_mm: { label: "Contact length (scanned)", unit: "mm" },
  contact_half_width_a_mm: { label: "Contact half-width a", unit: "mm" },
  percent_contact_length: { label: "Contact length", unit: "%" },
};

export function CofPredictionResult({
  result,
  submittedConditions,
}: {
  result: CofPredictionResponse;
  submittedConditions?: Record<string, string | number>;
}) {
  const outOfDomain = result.domain_status === "OUT_OF_DOMAIN";
  const { metrics, provenance } = result;

  return (
    <div className="mt-5 border-t border-line pt-5" aria-live="polite" data-testid="cof-prediction-result">
      {/* Prominent Result Header */}
      <div className="rounded-xl border border-line bg-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-muted">
              Model-estimated coefficient of friction · not a measurement
            </div>
            <div className="mt-1 text-3xl font-semibold text-ink" data-testid="cof-prediction-value">
              {result.predicted_coefficient_of_friction.toFixed(4)}
            </div>
            <div className="mt-1 text-xs text-muted">
              {result.target} · {result.target_unit}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${
                outOfDomain
                  ? "border-amber-300 bg-amber-50 text-amber-900"
                  : "border-emerald-200 bg-emerald-50 text-emerald-800"
              }`}
            >
              {outOfDomain ? (
                <AlertTriangle size={14} aria-hidden="true" />
              ) : (
                <CheckCircle2 size={14} aria-hidden="true" />
              )}
              {outOfDomain ? "OUT OF DOMAIN" : "IN DOMAIN"}
            </span>
            <span className="text-[11px] text-muted">
              Point prediction only · No prediction intervals produced
            </span>
          </div>
        </div>

        {/* Submitted input conditions table */}
        {submittedConditions && Object.keys(submittedConditions).length > 0 && (
          <div className="mt-5 border-t border-line/60 pt-4">
            <h4 className="m-0 text-xs font-semibold uppercase tracking-wider text-muted">
              Evaluated Input Conditions
            </h4>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4 lg:grid-cols-8">
              {Object.entries(submittedConditions).map(([key, val]) => {
                const info = CONDITION_UNITS[key];
                const label = info ? info.label : key.replaceAll("_", " ");
                const unit = info?.unit ? ` ${info.unit}` : "";
                const displayVal = typeof val === "number" ? val.toFixed(key.includes("half_width") ? 6 : 3) : String(val);
                return (
                  <div key={key} className="rounded bg-slate-50 p-2">
                    <span className="block text-[10px] uppercase text-muted truncate" title={label}>{label}</span>
                    <span className="font-semibold text-ink break-words">{displayVal}{unit}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {outOfDomain && (
        <div className="mt-4">
          <Notice tone="warning" title="Input outside the training range">
            One or more inputs sit outside the range spanned by the Cambridge training
            observations. This numerical extrapolation is not validated for decision-making.
          </Notice>
          <ul className="mt-3 list-disc pl-5 text-xs leading-relaxed text-muted">
            {result.out_of_domain_features.map((flag) => (
              <li key={flag.feature} className="font-mono">
                {flag.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Evaluation Performance Metrics */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MiniMetric label="Holdout MAE" value={metrics.mae.toFixed(4)} />
        <MiniMetric label="Holdout RMSE" value={metrics.rmse.toFixed(4)} />
        <MiniMetric label="Holdout R²" value={metrics.r2.toFixed(4)} />
        <MiniMetric label="Mean baseline MAE" value={metrics.baseline_mae.toFixed(4)} />
      </div>

      {/* Model & Artifact Provenance */}
      <dl className="mt-5 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Model</dt>
          <dd className="mt-0.5 text-sm font-semibold">{provenance.model_id}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Selected estimator</dt>
          <dd className="mt-0.5 text-sm">{provenance.selected_model}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Source</dt>
          <dd className="mt-0.5 text-sm">{provenance.source_name}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Source workbook</dt>
          <dd className="mt-0.5 text-sm">{provenance.source_workbook}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Workbook SHA-256</dt>
          <dd className="mt-0.5 break-words font-mono text-xs">{shortHash(provenance.source_workbook_sha256)}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-muted">Dataset SHA-256</dt>
          <dd className="mt-0.5 break-words font-mono text-xs">{shortHash(provenance.dataset_sha256)}</dd>
        </div>
      </dl>

      <p className="mb-0 mt-4 text-xs leading-relaxed text-muted">
        {provenance.observation_count} observations ({provenance.training_rows} train /{" "}
        {provenance.holdout_rows} holdout) across{" "}
        {provenance.training_groups + provenance.holdout_groups} labelled test runs; their
        independence is unverified because specimen serial numbers are unavailable. The
        reported metrics are the held-out evaluation of the {provenance.selected_model} model
        selected by group cross-validation; the mean-baseline numbers are shown alongside for
        reference.
      </p>

      <div className="mt-4">
        <Notice tone="warning" title="Domain limitation">
          {result.domain_limitation}
        </Notice>
      </div>

      <p className="mb-0 mt-3 text-xs leading-relaxed text-muted">{result.note}</p>
      <p className="mb-0 mt-2 text-xs text-muted">
        Composite targets trained by this response: {result.composite_targets_trained ? "yes" : "no"}.
      </p>
    </div>
  );
}
