"use client";

import { ArrowRight, ClipboardList, ExternalLink, Info } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { StatusBadge } from "@/components/status-badge";
import { api, type Experiment } from "@/lib/api";

export default function PlanningPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted" role="status">Loading planning workflow…</p>}>
      <PlanningContent />
    </Suspense>
  );
}

function PlanningContent() {
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<Experiment[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form state initialized with optional query parameters from model recommendations
  const candidateId = searchParams.get("candidate_id") || "";
  const initialMaterial = searchParams.get("material") || "";
  const initialLoad = searchParams.get("load_n") || "";
  const initialVelocity = searchParams.get("velocity") || "";
  const initialDistance = searchParams.get("distance") || "";
  const initialDuration = searchParams.get("duration") || "";
  const initialNotes = searchParams.get("notes") || "";

  const [formValues, setFormValues] = useState({
    experiment_id: candidateId ? `PLAN-${candidateId}` : "",
    planned_by: "Engineering Planning Module",
    material: initialMaterial,
    composition: initialMaterial ? `Specimen formulated as ${initialMaterial}` : "",
    composition_source_reference: candidateId ? "Cambridge tow-on-tool candidate design" : "",
    replicate_group_id: candidateId ? `GRP-${candidateId}` : "",
    load_n: initialLoad,
    velocity: initialVelocity || "0.05",
    distance: initialDistance || "0.8",
    duration: initialDuration || "16",
    notes: initialNotes,
  });

  const isFromCandidate = Boolean(candidateId || initialMaterial || initialLoad);

  const refresh = () => {
    setLoading(true);
    api.experiments("PLANNED")
      .then(setPlans)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");

    const payload = {
      experiment_id: formValues.experiment_id.trim(),
      record_status: "PLANNED",
      planned_by: formValues.planned_by.trim(),
      material_system_as_recorded: formValues.material.trim(),
      composition_as_recorded: formValues.composition.trim(),
      composition_source_reference: formValues.composition_source_reference.trim(),
      replicate_group_id: formValues.replicate_group_id.trim(),
      planned_conditions: {
        load_n: Number(formValues.load_n),
        sliding_velocity_m_per_s: Number(formValues.velocity),
        sliding_distance_m: Number(formValues.distance),
        test_duration_min: Number(formValues.duration),
      },
      notes: formValues.notes.trim(),
    };

    try {
      await api.createPlan(payload);
      setMessage(`Plan '${payload.experiment_id}' persisted as PLANNED. No measured responses were created.`);
      setFormValues({
        experiment_id: "",
        planned_by: "Engineering Planning Module",
        material: "",
        composition: "",
        composition_source_reference: "",
        replicate_group_id: "",
        load_n: "",
        velocity: "0.05",
        distance: "0.8",
        duration: "16",
        notes: "",
      });
      refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Plan could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="Physical validation"
        title="Experiment planning"
        description="Record proposed test conditions, composition as stated, and the provenance required to connect future measurements."
      />

      {isFromCandidate && (
        <div className="mb-5">
          <Notice tone="info" title="Candidate pre-populated from model recommendation">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>
                Pre-filled from test candidate {candidateId ? `(${candidateId})` : ""}. Review parameters, specify laboratory protocol details, and save as a formal planned record.
              </span>
              <Link href="/models" className="text-xs font-semibold text-accent hover:underline flex items-center gap-1">
                Back to model recommendations <ArrowRight size={13} />
              </Link>
            </div>
          </Notice>
        </div>
      )}

      <div className="mb-5">
        <Notice tone="warning" title="A plan is not an AI recommendation">
          No validated response model, uncertainty estimate, or optimum is available.
          These fields record human-proposed conditions only; qualified laboratory
          personnel must approve the design and protocol.
        </Notice>
      </div>

      {error && <div className="mb-4"><Notice tone="error" title="Planning action failed">{error}</Notice></div>}
      {message && (
        <div className="mb-4">
          <Notice tone="success" title="Plan saved">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>{message}</span>
              <Link href="/experiments?record_status=PLANNED" className="button-secondary text-xs font-semibold">
                View in registry <ArrowRight size={13} className="ml-1" />
              </Link>
            </div>
          </Notice>
        </div>
      )}

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.7fr)]">
        <form className="panel p-5 sm:p-6" onSubmit={submit}>
          <div className="mb-5 flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-accent"><ClipboardList size={18} aria-hidden="true" /></span>
            <div>
              <h2 className="m-0 text-base font-semibold">Proposed conditions</h2>
              <p className="mb-0 mt-0.5 text-xs text-muted">Required values must be positive.</p>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="field-label">Experiment plan ID *</span>
              <input
                className="field"
                name="experiment_id"
                required
                value={formValues.experiment_id}
                onChange={(e) => setFormValues((v) => ({ ...v, experiment_id: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Prepared by</span>
              <input
                className="field"
                name="planned_by"
                value={formValues.planned_by}
                onChange={(e) => setFormValues((v) => ({ ...v, planned_by: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Material system exactly as proposed *</span>
              <input
                className="field"
                name="material"
                required
                value={formValues.material}
                onChange={(e) => setFormValues((v) => ({ ...v, material: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Composition / preparation description *</span>
              <input
                className="field"
                name="composition"
                required
                value={formValues.composition}
                onChange={(e) => setFormValues((v) => ({ ...v, composition: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Composition record reference</span>
              <input
                className="field"
                name="composition_source_reference"
                value={formValues.composition_source_reference}
                onChange={(e) => setFormValues((v) => ({ ...v, composition_source_reference: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Replicate/shared-control group ID</span>
              <input
                className="field"
                name="replicate_group_id"
                value={formValues.replicate_group_id}
                onChange={(e) => setFormValues((v) => ({ ...v, replicate_group_id: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Load (N) *</span>
              <input
                className="field"
                name="load_n"
                required
                type="number"
                step="any"
                min="0.000001"
                value={formValues.load_n}
                onChange={(e) => setFormValues((v) => ({ ...v, load_n: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Sliding velocity (m/s) *</span>
              <input
                className="field"
                name="velocity"
                required
                type="number"
                step="any"
                min="0.000001"
                value={formValues.velocity}
                onChange={(e) => setFormValues((v) => ({ ...v, velocity: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Sliding distance (m) *</span>
              <input
                className="field"
                name="distance"
                required
                type="number"
                step="any"
                min="0.000001"
                value={formValues.distance}
                onChange={(e) => setFormValues((v) => ({ ...v, distance: e.target.value }))}
              />
            </label>
            <label>
              <span className="field-label">Duration (min) *</span>
              <input
                className="field"
                name="duration"
                required
                type="number"
                step="any"
                min="0.000001"
                value={formValues.duration}
                onChange={(e) => setFormValues((v) => ({ ...v, duration: e.target.value }))}
              />
            </label>
            <label className="sm:col-span-2">
              <span className="field-label">Planning rationale and pending protocol checks</span>
              <textarea
                className="field min-h-24"
                name="notes"
                value={formValues.notes}
                onChange={(e) => setFormValues((v) => ({ ...v, notes: e.target.value }))}
              />
            </label>
          </div>
          <button className="button-primary mt-5" disabled={busy} type="submit">{busy ? "Saving…" : "Save planned experiment"}</button>
        </form>
        <aside className="panel p-5">
          <div className="flex items-center gap-2 font-semibold"><Info size={17} className="text-accent" aria-hidden="true" />Recordkeeping cues</div>
          <ul className="mt-4 space-y-3 pl-4 text-sm leading-relaxed text-muted">
            <li>Record material composition as provided by the qualified source; do not infer the unresolved Zr filler pair.</li>
            <li>Assign replicate, batch, or shared-control identifiers before testing.</li>
            <li>Keep planned setpoints separate from measured conditions and instrument outputs.</li>
            <li>Capture measurement names and units exactly as recorded, plus instrument and source references.</li>
          </ul>
          <div className="mt-5 border-t border-line pt-4">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="m-0 text-sm font-semibold">Saved plans</h3>
                <Link href="/experiments?record_status=PLANNED" className="text-[11px] text-accent hover:underline flex items-center gap-1 mt-0.5">
                  View all in registry <ArrowRight size={11} />
                </Link>
              </div>
              <StatusBadge status="PLANNED" />
            </div>
            {loading ? <p className="text-xs text-muted">Loading plans…</p> : plans.length ? (
              <ul className="m-0 space-y-2 p-0">
                {plans.map((plan) => (
                  <li className="list-none rounded-lg bg-slate-50 p-3 text-xs" key={plan.experiment_id}>
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-ink">{plan.experiment_id} · {plan.material_system_as_recorded}</div>
                      <Link
                        href={`/experiments?query=${encodeURIComponent(plan.experiment_id)}`}
                        className="text-accent hover:underline text-[11px] flex items-center gap-1 font-medium"
                        title="Inspect in registry"
                      >
                        Inspect <ExternalLink size={11} />
                      </Link>
                    </div>
                    <div className="mt-1 text-muted">{Object.entries(plan.planned_conditions).map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`).join(" · ")}</div>
                  </li>
                ))}
              </ul>
            ) : <p className="mb-0 text-xs text-muted">No plans have been saved.</p>}
          </div>
        </aside>
      </div>
    </>
  );
}

