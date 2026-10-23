"use client";

import { AlertTriangle, ArrowRight, Info, Loader2, Play, Sliders } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { CofPredictionResult } from "@/components/cof-prediction-result";
import { Notice } from "@/components/notice";
import {
  api,
  type CofCandidateValidationResult,
  type CofPredictionRequest,
  type CofPredictionResponse,
  type CofRecommendationResponse,
  type ExternalFeatureInput,
  type ExternalFeatureSchema,
} from "@/lib/api";

const FEATURE_CONFIG: Record<string, { label: string; unit: string; description: string }> = {
  normal_load_n: {
    label: "Normal load",
    unit: "N",
    description: "Applied normal force on the tow patch (0.078 N – 49.15 N)",
  },
  nominal_pressure_mpa: {
    label: "Nominal pressure",
    unit: "MPa",
    description: "Derived automatically from normal load / contact area",
  },
  contact_width_mm: {
    label: "Contact width",
    unit: "mm",
    description: "Transverse tow width measured across the contact zone",
  },
  contact_area_mm2: {
    label: "Contact area",
    unit: "mm²",
    description: "Projected contact surface area under the applied load",
  },
  contact_length_scanned_mm: {
    label: "Contact length (scanned)",
    unit: "mm",
    description: "Total scanned contact length along tow sweep",
  },
  contact_half_width_a_mm: {
    label: "Contact half-width a",
    unit: "mm",
    description: "Hertzian-equivalent contact half-width a",
  },
  percent_contact_length: {
    label: "Contact length",
    unit: "%",
    description: "Percentage of total specimen length in direct contact",
  },
  tow_type: {
    label: "Tow type",
    unit: "categorical",
    description: "Carbon-fibre tow type and sizing treatment",
  },
};

function trimNumber(value: number): string {
  return String(Number(value.toPrecision(6)));
}

function defaultText(feature: ExternalFeatureInput): string {
  if (feature.median !== undefined) return trimNumber(feature.median);
  if (feature.min !== undefined && feature.max !== undefined) {
    return trimNumber((feature.min + feature.max) / 2);
  }
  return "";
}

function rangeHint(feature: ExternalFeatureInput): string {
  if (feature.min === undefined || feature.max === undefined) return feature.unit;
  return `${trimNumber(feature.min)} – ${trimNumber(feature.max)} ${feature.unit}`.trim();
}

function initialValues(schema: ExternalFeatureSchema): Record<string, string> {
  const values: Record<string, string> = {};
  for (const feature of schema.features) {
    if (!feature.required) continue;
    values[feature.name] =
      feature.dtype === "categorical"
        ? (feature.allowed_values?.[0] ?? "")
        : defaultText(feature);
  }
  return values;
}

function parsePayload(
  values: Record<string, string>,
  schema: ExternalFeatureSchema,
): { payload: CofPredictionRequest; submitted: Record<string, string | number> } {
  const payload: Record<string, number | string> = {};
  const submitted: Record<string, string | number> = {};

  for (const feature of schema.features) {
    if (!feature.required) continue;
    if (feature.name === "nominal_pressure_mpa") continue;
    const raw = (values[feature.name] ?? "").trim();
    if (feature.dtype === "categorical") {
      payload[feature.name] = raw;
      submitted[feature.name] = raw;
      continue;
    }
    const parsed = Number(raw);
    if (raw === "" || !Number.isFinite(parsed)) {
      throw new Error(`${FEATURE_CONFIG[feature.name]?.label ?? feature.name} must be a finite number.`);
    }
    if (parsed <= 0) {
      throw new Error(`${FEATURE_CONFIG[feature.name]?.label ?? feature.name} must be greater than zero.`);
    }
    payload[feature.name] = parsed;
    submitted[feature.name] = parsed;
  }

  const normalLoad = Number(values.normal_load_n);
  const contactArea = Number(values.contact_area_mm2);
  if (
    !Number.isFinite(normalLoad) ||
    normalLoad <= 0 ||
    !Number.isFinite(contactArea) ||
    contactArea <= 0
  ) {
    throw new Error("Normal load and contact area are required to derive nominal pressure.");
  }
  const derivedPressure = normalLoad / contactArea;
  payload.nominal_pressure_mpa = derivedPressure;
  submitted.nominal_pressure_mpa = derivedPressure;

  return { payload: payload as CofPredictionRequest, submitted };
}

export function CofPredictionForm({ schema }: { schema: ExternalFeatureSchema }) {
  const fields = useMemo(() => schema.features.filter((feature) => feature.required), [schema]);
  const derived = useMemo(
    () => schema.features.filter((feature) => feature.dtype === "derived"),
    [schema],
  );

  const [values, setValues] = useState<Record<string, string>>(() => initialValues(schema));
  const [submittedInputs, setSubmittedInputs] = useState<Record<string, string | number> | undefined>(undefined);
  const [result, setResult] = useState<CofPredictionResponse | null>(null);
  const [candidateValidation, setCandidateValidation] =
    useState<CofCandidateValidationResult | null>(null);
  const [recommendations, setRecommendations] =
    useState<CofRecommendationResponse | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [candidatePending, setCandidatePending] = useState(false);
  const [recommendPending, setRecommendPending] = useState(false);

  // Recommendation engine interactive controls
  const [recommendTowType, setRecommendTowType] = useState<string>("T700-12k-60E");
  const [recommendMinLoad, setRecommendMinLoad] = useState<string>("5.0");
  const [recommendMaxLoad, setRecommendMaxLoad] = useState<string>("40.0");
  const [recommendCandidateCount, setRecommendCandidateCount] = useState<number>(4);
  const [recommendCriterion, setRecommendCriterion] = useState<
    "lowest_predicted_cof" | "highest_predicted_cof" | "load_sweep_grid"
  >("lowest_predicted_cof");

  // Pre-submission input validation check
  const inputDomainWarnings = useMemo(() => {
    const warnings: string[] = [];
    for (const feature of schema.features) {
      if (feature.dtype === "categorical" || !feature.required || feature.name === "nominal_pressure_mpa") continue;
      const raw = values[feature.name]?.trim();
      const val = Number(raw);
      if (Number.isFinite(val)) {
        if (feature.min !== undefined && val < feature.min) {
          warnings.push(
            `${FEATURE_CONFIG[feature.name]?.label ?? feature.name} (${val}) is below training minimum (${trimNumber(feature.min)} ${feature.unit})`
          );
        } else if (feature.max !== undefined && val > feature.max) {
          warnings.push(
            `${FEATURE_CONFIG[feature.name]?.label ?? feature.name} (${val}) is above training maximum (${trimNumber(feature.max)} ${feature.unit})`
          );
        }
      }
    }
    return warnings;
  }, [values, schema]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setCandidateValidation(null);
    setRecommendations(null);

    let parsed: { payload: CofPredictionRequest; submitted: Record<string, string | number> };
    try {
      parsed = parsePayload(values, schema);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Invalid input.");
      return;
    }

    setPending(true);
    try {
      const response = await api.predictCof(parsed.payload);
      setResult(response);
      setSubmittedInputs(parsed.submitted);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Prediction failed.");
    } finally {
      setPending(false);
    }
  }

  async function handleCandidateValidation() {
    setError("");
    setCandidateValidation(null);
    setRecommendations(null);

    let parsed: { payload: CofPredictionRequest; submitted: Record<string, string | number> };
    try {
      parsed = parsePayload(values, schema);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Invalid input.");
      return;
    }

    setCandidatePending(true);
    try {
      const response = await api.validateCofCandidates([
        { candidate_id: "current-condition", conditions: parsed.payload },
      ]);
      setCandidateValidation(response.results[0] ?? null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Candidate validation failed.");
    } finally {
      setCandidatePending(false);
    }
  }

  async function handleRecommendations(useCustomSettings = false) {
    setError("");
    setRecommendations(null);
    setCandidateValidation(null);
    setResult(null);

    const towType = useCustomSettings ? recommendTowType : (values.tow_type || "T700-12k-60E");
    const minLoad = useCustomSettings ? Number(recommendMinLoad) : undefined;
    const maxLoad = useCustomSettings ? Number(recommendMaxLoad) : undefined;
    const numCandidates = useCustomSettings ? recommendCandidateCount : 4;
    const criterion = useCustomSettings ? recommendCriterion : "lowest_predicted_cof";

    if (useCustomSettings) {
      if (minLoad === undefined || !Number.isFinite(minLoad) || minLoad <= 0) {
        setError("Recommendation minimum load must be a positive number.");
        return;
      }
      if (maxLoad === undefined || !Number.isFinite(maxLoad) || maxLoad <= 0) {
        setError("Recommendation maximum load must be a positive number.");
        return;
      }
      if (minLoad >= maxLoad) {
        setError("Recommendation minimum load must be strictly less than maximum load.");
        return;
      }
      if (maxLoad > 48.36) {
        setError("Recommendation maximum load cannot exceed Cambridge training limit (48.36 N).");
        return;
      }
    }

    setRecommendPending(true);
    try {
      const response = await api.recommendCofExperiments({
        tow_type: towType,
        min_load_n: minLoad,
        max_load_n: maxLoad,
        num_candidates: numCandidates,
        target_criterion: criterion,
      });
      setRecommendations(response);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Recommendation failed.");
    } finally {
      setRecommendPending(false);
    }
  }

  return (
    <div className="mt-8 border-t border-line pt-6">
      <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50/40 p-4">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 text-blue-700 shrink-0" size={18} />
          <div className="text-xs leading-relaxed text-blue-950">
            <span className="font-semibold block text-sm text-blue-900 mb-1">
              Applicable Model Scope & Physical Domain
            </span>
            This interactive interface executes the verified <strong>Cambridge Tow-on-Tool Ridge Regression Model</strong>.
            Predictions are restricted strictly to dry carbon-fibre tow sliding over polished glass under 14-step ramp conditions
            (normal loads: <strong>0.078 N – 48.36 N</strong>). Supported tow types are <strong>T700-12k-60E</strong> and <strong>T700-12k-50C</strong>.
            This model <em>cannot</em> predict friction or wear for glass-fibre/epoxy composite laminates.
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="m-0 text-base font-semibold text-ink">Predict coefficient of friction</h3>
          <p className="mb-0 mt-1 text-xs text-muted">
            Enter one tow-on-tool condition. Predictions are available only inside the recorded
            training ranges; out-of-range extrapolations are blocked. Normal pressure is derived
            from load and contact area.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          Point estimate · No uncertainty bounds
        </span>
      </div>

      <form className="mt-5" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {fields.map((feature) => {
            const config = FEATURE_CONFIG[feature.name];
            return (
              <FeatureField
                key={feature.name}
                feature={feature}
                label={config?.label ?? feature.name}
                unit={config?.unit}
                value={
                  feature.name === "nominal_pressure_mpa"
                    ? pressureValue(values)
                    : values[feature.name] ?? ""
                }
                readOnly={feature.name === "nominal_pressure_mpa"}
                onChange={(next) => {
                  setCandidateValidation(null);
                  setRecommendations(null);
                  setValues((current) => ({ ...current, [feature.name]: next }));
                }}
              />
            );
          })}
        </div>

        {derived.map((feature) => (
          <p key={feature.name} className="mb-0 mt-3 text-xs text-muted">
            <span className="font-medium text-ink">{FEATURE_CONFIG[feature.name]?.label ?? feature.name}</span> is derived automatically: {feature.transformation}.
          </p>
        ))}

        {inputDomainWarnings.length > 0 && (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50/70 p-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
              <AlertTriangle size={14} />
              <span>Input Domain Guidance Warnings ({inputDomainWarnings.length})</span>
            </div>
            <ul className="mt-1.5 space-y-1 pl-4 text-xs text-amber-950 list-disc">
              {inputDomainWarnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button className="button-primary" type="submit" disabled={pending}>
            {pending ? (
              <Loader2 className="animate-spin" size={15} aria-hidden="true" />
            ) : (
              <Play size={15} aria-hidden="true" />
            )}
            {pending ? "Predicting…" : "Predict coefficient of friction"}
          </button>

          <button
            className="button-secondary"
            type="button"
            disabled={candidatePending}
            onClick={() => void handleCandidateValidation()}
          >
            {candidatePending ? "Validating candidate…" : "Validate physical-test candidate"}
          </button>

          <button
            className="button-secondary"
            type="button"
            disabled={recommendPending}
            onClick={() => void handleRecommendations(false)}
          >
            {recommendPending ? "Generating candidates…" : "Recommend physical-test conditions"}
          </button>
          <span className="text-xs text-muted">No prediction interval or feature attribution is produced.</span>
        </div>
        <p className="mb-0 mt-2 text-xs text-muted">
          Candidate validation checks recorded feature ranges and pressure consistency only. It
          does not rank conditions, predict an optimum, or establish a causal effect.
        </p>
      </form>

      {error && (
        <div className="mt-4">
          <Notice tone="error" title="Action could not be produced">
            {error}
          </Notice>
        </div>
      )}

      {candidateValidation && (
        <div className="mt-4" data-testid="candidate-validation-result">
          <Notice
            tone={candidateValidation.accepted_for_physical_testing ? "warning" : "error"}
            title={
              candidateValidation.accepted_for_physical_testing
                ? "Candidate is within the recorded limits"
                : "Candidate is not supported"
            }
          >
            {candidateValidation.accepted_for_physical_testing
              ? "This condition may be considered for physical testing only; it is not an optimum or validated recommendation."
              : [
                  ...candidateValidation.issues,
                  ...candidateValidation.out_of_domain_features.map((feature) => feature.message),
                ].join(" ")}
          </Notice>
        </div>
      )}

      {result && <CofPredictionResult result={result} submittedConditions={submittedInputs} />}

      {/* Constrained Recommendation Engine Section */}
      <div className="mt-10 rounded-xl border border-line bg-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Sliders size={18} className="text-accent" />
              <h4 className="m-0 text-sm font-semibold">Physical-test recommendation parameters</h4>
            </div>
            <p className="mb-0 mt-1 text-xs text-muted">
              Generate ranked physical test conditions strictly constrained to the Cambridge training domain and verified apparatus geometry.
            </p>
          </div>
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900">
            Model estimate · unproven optimum
          </span>
        </div>

        {/* Interactive Controls */}
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label>
            <span className="field-label">Tow type</span>
            <select
              className="field"
              value={recommendTowType}
              onChange={(e) => setRecommendTowType(e.target.value)}
            >
              <option value="T700-12k-60E">T700-12k-60E (60E sizing)</option>
              <option value="T700-12k-50C">T700-12k-50C (50C sizing)</option>
            </select>
          </label>

          <label>
            <span className="field-label">Min normal load (N)</span>
            <input
              className="field"
              type="number"
              step="any"
              value={recommendMinLoad}
              onChange={(e) => setRecommendMinLoad(e.target.value)}
            />
            <span className="mt-1 block text-[11px] text-muted">Training min: ~0.08 N</span>
          </label>

          <label>
            <span className="field-label">Max normal load (N)</span>
            <input
              className="field"
              type="number"
              step="any"
              value={recommendMaxLoad}
              onChange={(e) => setRecommendMaxLoad(e.target.value)}
            />
            <span className="mt-1 block text-[11px] text-muted">Training max: 48.36 N</span>
          </label>

          <label>
            <span className="field-label">Candidate count</span>
            <input
              className="field"
              type="number"
              min={2}
              max={10}
              value={recommendCandidateCount}
              onChange={(e) => setRecommendCandidateCount(Math.max(2, Math.min(10, Number(e.target.value) || 4)))}
            />
            <span className="mt-1 block text-[11px] text-muted">2 to 10 candidates</span>
          </label>

          <label>
            <span className="field-label">Ranking criterion</span>
            <select
              className="field"
              value={recommendCriterion}
              onChange={(e) =>
                setRecommendCriterion(
                  e.target.value as "lowest_predicted_cof" | "highest_predicted_cof" | "load_sweep_grid"
                )
              }
            >
              <option value="lowest_predicted_cof">Lowest estimated COF</option>
              <option value="highest_predicted_cof">Highest estimated COF</option>
              <option value="load_sweep_grid">Uniform load sweep grid</option>
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="mb-0 text-xs text-muted max-w-xl">
            <strong>Ranking explanation:</strong> Conditions are generated using tow-type specific contact geometry relations,
            bounded by training load limits, and ordered by the selected criterion ({recommendCriterion.replaceAll("_", " ")}).
          </p>
          <button
            className="button-primary"
            type="button"
            disabled={recommendPending}
            onClick={() => void handleRecommendations(true)}
          >
            {recommendPending ? (
              <Loader2 className="animate-spin" size={15} aria-hidden="true" />
            ) : (
              <Sliders size={15} aria-hidden="true" />
            )}
            {recommendPending ? "Generating candidates…" : "Generate physical-test candidates"}
          </button>
        </div>

        {recommendations && (
          <div className="mt-6 border-t border-line pt-4" data-testid="cof-recommendations-panel">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="m-0 text-sm font-semibold">Constrained physical-test candidates</h4>
                <p className="mb-0 mt-0.5 text-xs text-muted">
                  Candidate conditions for physical laboratory testing (not an established optimum) · {recommendations.model_id}
                </p>
              </div>
              <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-900">
                Model estimate · unproven optimum
              </span>
            </div>
            <div className="mt-3">
              <Notice tone="warning" title="Reliability notice">
                {recommendations.reliability_notice} {recommendations.causal_disclaimer}
                <div className="mt-1 font-semibold text-amber-950">
                  These ranked candidates are intended for laboratory physical screening only. They are not experimentally proven optimal settings.
                </div>
              </Notice>
            </div>

            <div className="table-scroll mt-4">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate ID</th>
                    <th>Tow type</th>
                    <th>Normal load (N)</th>
                    <th>Nominal pressure (MPa)</th>
                    <th>Estimated COF</th>
                    <th>Status</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.recommendations.map((rec) => (
                    <tr key={rec.candidate_id}>
                      <td className="font-semibold">{rec.rank}</td>
                      <td className="font-mono text-xs font-semibold">{rec.candidate_id}</td>
                      <td>{rec.conditions.tow_type}</td>
                      <td className="font-semibold">{rec.conditions.normal_load_n.toFixed(2)}</td>
                      <td>{rec.conditions.nominal_pressure_mpa.toFixed(4)}</td>
                      <td className="font-semibold text-accent">{rec.predicted_coefficient_of_friction.toFixed(4)}</td>
                      <td className="text-xs text-muted">Model estimate (test candidate)</td>
                      <td className="text-right whitespace-nowrap">
                        <Link
                          href={`/planning?candidate_id=${encodeURIComponent(rec.candidate_id)}&material=${encodeURIComponent(rec.conditions.tow_type)}&load_n=${encodeURIComponent(rec.conditions.normal_load_n.toString())}&notes=${encodeURIComponent(`Test candidate ${rec.candidate_id} from Cambridge tow-on-tool model (predicted COF: ${rec.predicted_coefficient_of_friction.toFixed(4)})`)}`}
                          className="button-secondary !py-1 !px-2.5 text-xs font-semibold inline-flex items-center gap-1"
                          title="Transfer condition to Experiment Planning"
                        >
                          <span>Plan test</span>
                          <ArrowRight size={12} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mb-0 mt-3 text-xs leading-relaxed text-muted">
              {recommendations.interpretation} Composite targets trained: {recommendations.composite_targets_trained ? "yes" : "no"}.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function FeatureField({
  feature,
  label,
  unit,
  value,
  readOnly = false,
  onChange,
}: {
  feature: ExternalFeatureInput;
  label: string;
  unit?: string;
  value: string;
  readOnly?: boolean;
  onChange: (next: string) => void;
}) {
  const inputId = `cof-feature-${feature.name}`;

  return (
    <div>
      <label className="field-label mt-0" htmlFor={inputId}>
        {label}
      </label>
      {feature.dtype === "categorical" ? (
        <select
          id={inputId}
          className="field"
          value={value}
          onChange={(event) => onChange(event.target.value)}
        >
          {(feature.allowed_values ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={inputId}
          className="field"
          type="number"
          inputMode="decimal"
          step="any"
          value={value}
          readOnly={readOnly}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
      <p className="mb-0 mt-1 text-xs text-muted">
        {readOnly
          ? "Computed from normal load / contact area."
          : `Unit: ${unit && unit !== "categorical" ? unit : "categorical"} · Valid range: ${rangeHint(feature)}`}
      </p>
    </div>
  );
}

function pressureValue(values: Record<string, string>): string {
  const load = Number(values.normal_load_n);
  const area = Number(values.contact_area_mm2);
  if (!Number.isFinite(load) || !Number.isFinite(area) || area <= 0) return "";
  return String(load / area);
}
