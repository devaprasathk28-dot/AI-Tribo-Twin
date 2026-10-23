"use client";

import {
  BarChart3,
  Beaker,
  BrainCircuit,
  Download,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { api } from "@/lib/api";

export default function ReportsPage() {
  // Registry Report State
  const [regStatus, setRegStatus] = useState<string>("ALL");
  const [regMaterial, setRegMaterial] = useState<string>("");
  const [regQuery, setRegQuery] = useState<string>("");

  // Analytics Report State
  const [anaMaterial, setAnaMaterial] = useState<string>("");
  const [anaStatus, setAnaStatus] = useState<string>("ALL");

  // Single Experiment State
  const [experimentId, setExperimentId] = useState<string>("");
  const [expError, setExpError] = useState<string>("");

  // In-flight download tracking
  const [downloading, setDownloading] = useState<string | null>(null);

  const triggerDownload = (url: string, reportName: string) => {
    setDownloading(reportName);
    try {
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
    } finally {
      setTimeout(() => setDownloading(null), 1000);
    }
  };

  const handleSingleExperimentDownload = () => {
    setExpError("");
    const trimmed = experimentId.trim();
    if (!trimmed) {
      setExpError("Please enter a valid Experiment ID.");
      return;
    }
    const url = api.getExperimentPdfUrl(trimmed);
    triggerDownload(url, `exp-${trimmed}`);
  };

  return (
    <>
      <PageHeading
        eyebrow="Documentation & Audit"
        title="Engineering Reports & Export"
        description="Generate, preview, and download publication-grade PDF summaries and structured CSV records with immutable evidence provenance."
      />

      {/* Main Notice on Scientific Report Standards */}
      <div className="mb-6">
        <Notice tone="info" title="Scientific Report Standards">
          All generated reports embed immutable UTC timestamps, stable report identifiers (
          <code>REP-EXP-*</code>, <code>REP-REG-*</code>, <code>REP-ANA-*</code>,{" "}
          <code>REP-MDL-*</code>), explicit unit labels, and complete evidence provenance. Planned
          screening conditions remain strictly segregated from physically measured experimental data.
        </Notice>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ===================================================================
            CARD 1: FILTERED EXPERIMENT REGISTRY REPORT
            =================================================================== */}
        <section className="panel p-6" aria-labelledby="heading-registry-report">
          <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Beaker className="text-accent shrink-0" size={18} />
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Experimental Data
                </span>
              </div>
              <h2 id="heading-registry-report" className="m-0 mt-1 text-base font-bold text-ink">
                Experiment Registry Summary Report
              </h2>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              PDF & CSV
            </span>
          </div>

          <p className="mt-3 text-xs leading-relaxed text-muted">
            Export a comprehensive summary of tested parameters, operating conditions (load, velocity,
            distance), measured responses (COF, wear rate), and source provenance. Planned records are
            explicitly flagged to prevent contamination of empirical benchmarks.
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div>
              <label className="field-label" htmlFor="reg-status">
                Record Status
              </label>
              <select
                id="reg-status"
                className="field text-xs"
                value={regStatus}
                onChange={(e) => setRegStatus(e.target.value)}
              >
                <option value="ALL">All Records</option>
                <option value="MEASURED">Measured Only</option>
                <option value="PLANNED">Planned Only</option>
              </select>
            </div>

            <div>
              <label className="field-label" htmlFor="reg-material">
                Material System
              </label>
              <input
                id="reg-material"
                type="text"
                placeholder="e.g. FeTiO3 or all"
                className="field text-xs"
                value={regMaterial}
                onChange={(e) => setRegMaterial(e.target.value)}
              />
            </div>

            <div>
              <label className="field-label" htmlFor="reg-query">
                Search Keyword
              </label>
              <input
                id="reg-query"
                type="text"
                placeholder="Operator, note, ID"
                className="field text-xs"
                value={regQuery}
                onChange={(e) => setRegQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <button
              type="button"
              className="button-primary"
              disabled={downloading === "reg-pdf"}
              onClick={() =>
                triggerDownload(
                  api.getRegistryPdfUrl({
                    status: regStatus,
                    material_system: regMaterial,
                    query: regQuery,
                  }),
                  "reg-pdf",
                )
              }
            >
              {downloading === "reg-pdf" ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <FileText size={15} />
              )}
              Download Registry Report (PDF)
            </button>

            <button
              type="button"
              className="button-outline"
              disabled={downloading === "reg-csv"}
              onClick={() =>
                triggerDownload(
                  api.getRegistryCsvUrl({
                    status: regStatus,
                    material_system: regMaterial,
                    query: regQuery,
                  }),
                  "reg-csv",
                )
              }
            >
              {downloading === "reg-csv" ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <FileSpreadsheet size={15} />
              )}
              Export Registry Records (CSV)
            </button>
          </div>
        </section>

        {/* ===================================================================
            CARD 2: ENGINEERING ANALYTICS SUMMARY REPORT
            =================================================================== */}
        <section className="panel p-6" aria-labelledby="heading-analytics-report">
          <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="text-accent shrink-0" size={18} />
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Analytics & Visuals
                </span>
              </div>
              <h2 id="heading-analytics-report" className="m-0 mt-1 text-base font-bold text-ink">
                Engineering Analytics Summary Report
              </h2>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              PDF & CSV
            </span>
          </div>

          <p className="mt-3 text-xs leading-relaxed text-muted">
            Download an aggregated synthesis of experimental registry KPIs, material system
            distributions, empirical friction coefficient (COF) statistics, and unit-segregated wear
            measurements. Includes explicit disclaimers on descriptive correlations.
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="field-label" htmlFor="ana-status">
                Filter by Status
              </label>
              <select
                id="ana-status"
                className="field text-xs"
                value={anaStatus}
                onChange={(e) => setAnaStatus(e.target.value)}
              >
                <option value="ALL">All Records</option>
                <option value="MEASURED">Measured Runs Only</option>
                <option value="PLANNED">Planned Runs Only</option>
              </select>
            </div>

            <div>
              <label className="field-label" htmlFor="ana-material">
                Filter Material System
              </label>
              <input
                id="ana-material"
                type="text"
                placeholder="e.g. FeTiO3:SiO2 or all"
                className="field text-xs"
                value={anaMaterial}
                onChange={(e) => setAnaMaterial(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <button
              type="button"
              className="button-primary"
              disabled={downloading === "ana-pdf"}
              onClick={() =>
                triggerDownload(
                  api.getAnalyticsPdfUrl({
                    status: anaStatus,
                    material_system: anaMaterial,
                  }),
                  "ana-pdf",
                )
              }
            >
              {downloading === "ana-pdf" ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <FileText size={15} />
              )}
              Download Analytics Summary (PDF)
            </button>

            <button
              type="button"
              className="button-outline"
              disabled={downloading === "ana-csv"}
              onClick={() =>
                triggerDownload(
                  api.getAnalyticsCsvUrl({
                    status: anaStatus,
                    material_system: anaMaterial,
                  }),
                  "ana-csv",
                )
              }
            >
              {downloading === "ana-csv" ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <FileSpreadsheet size={15} />
              )}
              Export Analytics KPIs (CSV)
            </button>
          </div>
        </section>

        {/* ===================================================================
            CARD 3: MODEL EVALUATION & PROVENANCE REPORT
            =================================================================== */}
        <section className="panel p-6" aria-labelledby="heading-models-report">
          <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
            <div>
              <div className="flex items-center gap-2">
                <BrainCircuit className="text-accent shrink-0" size={18} />
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Model Provenance
                </span>
              </div>
              <h2 id="heading-models-report" className="m-0 mt-1 text-base font-bold text-ink">
                Model Evaluation & Provenance Audit
              </h2>
            </div>
            <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
              Verified Source of Truth
            </span>
          </div>

          <p className="mt-3 text-xs leading-relaxed text-muted">
            Generates a formal scientific audit of the evaluated Cambridge carbon-fibre tow-on-tool
            model (MAE 0.1340, RMSE 0.2263, R² 0.7826), stratified 60E vs 50C slices, 50C Step 0
            deficit findings, specimen independence limitations, synthetic demo status, and currently
            blocked composite target readiness gates.
          </p>

          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-xs leading-relaxed text-amber-950">
            <strong>Scope Disclaimer:</strong> The external benchmark applies strictly to carbon-fibre
            tow sliding on glass tools under a 14-step ramp. It does not predict glass-fibre/epoxy
            composite friction. Composite targets remain safely blocked pending evidence resolution.
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <button
              type="button"
              className="button-primary"
              disabled={downloading === "models-pdf"}
              onClick={() => triggerDownload(api.getModelsPdfUrl(), "models-pdf")}
            >
              {downloading === "models-pdf" ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <FileText size={15} />
              )}
              Download Model Audit Report (PDF)
            </button>

            <Link href="/models" className="button-outline text-xs">
              View Interactive Model Page
            </Link>
          </div>
        </section>

        {/* ===================================================================
            CARD 4: INDIVIDUAL EXPERIMENT REPORT
            =================================================================== */}
        <section className="panel p-6" aria-labelledby="heading-single-report">
          <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FileCheck className="text-accent shrink-0" size={18} />
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Individual Record
                </span>
              </div>
              <h2 id="heading-single-report" className="m-0 mt-1 text-base font-bold text-ink">
                Individual Experiment Engineering Report
              </h2>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
              Single Run PDF
            </span>
          </div>

          <p className="mt-3 text-xs leading-relaxed text-muted">
            Lookup and download a publication-grade engineering report for a single experiment or
            planned condition set. Formatted with operating conditions, measured responses with units,
            laboratory instrument ID, technician notes, and SHA-256 provenance fingerprint.
          </p>

          <div className="mt-4">
            <label className="field-label" htmlFor="single-exp-id">
              Experiment Identifier
            </label>
            <div className="mt-1 flex gap-2">
              <input
                id="single-exp-id"
                type="text"
                placeholder="e.g. EXP-001 or PLAN-001"
                className="field flex-1 text-xs"
                value={experimentId}
                onChange={(e) => {
                  setExperimentId(e.target.value);
                  setExpError("");
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleSingleExperimentDownload();
                  }
                }}
              />
              <button
                type="button"
                className="button-primary"
                disabled={downloading === `exp-${experimentId.trim()}`}
                onClick={handleSingleExperimentDownload}
              >
                {downloading === `exp-${experimentId.trim()}` ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Download size={15} />
                )}
                Generate PDF
              </button>
            </div>
            {expError && <p className="mb-0 mt-1.5 text-xs text-red-600 font-medium">{expError}</p>}
          </div>

          <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-xs text-muted">
            <span>Need to find an experiment ID?</span>
            <Link href="/experiments" className="text-accent hover:underline font-semibold">
              Browse Experiment Registry →
            </Link>
          </div>
        </section>
      </div>

      {/* ===================================================================
          SCIENTIFIC INTEGRITY & STANDARDS REGISTER
          =================================================================== */}
      <section className="panel mt-8 p-6 border-l-4 border-l-accent" aria-labelledby="heading-standards">
        <div className="flex items-center gap-2">
          <ShieldAlert className="text-accent shrink-0" size={20} />
          <h2 id="heading-standards" className="m-0 text-base font-bold text-ink">
            Scientific Integrity & Report Generation Standards
          </h2>
        </div>
        <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
          All engineering artifacts and exported reports adhere to strict computational and laboratory
          safeguards:
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-line bg-slate-50/70 p-3.5">
            <div className="text-xs font-bold text-ink">1. Stable Document IDs</div>
            <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
              Every PDF report generates a unique, persistent identifier (e.g. <code>REP-EXP-*</code>)
              and exact UTC timestamp for full lab notebook cross-referencing.
            </p>
          </div>

          <div className="rounded-lg border border-line bg-slate-50/70 p-3.5">
            <div className="text-xs font-bold text-ink">2. Status Segregation</div>
            <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
              Planned prospective parameters are visually and methodologically distinguished from
              physically measured observations in all PDF and CSV exports.
            </p>
          </div>

          <div className="rounded-lg border border-line bg-slate-50/70 p-3.5">
            <div className="text-xs font-bold text-ink">3. Segregated Wear Units</div>
            <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
              Incompatible wear metrics (e.g. depth in microns vs specific wear rate in mm³/N·m) are
              never pooled into a composite metric.
            </p>
          </div>

          <div className="rounded-lg border border-line bg-slate-50/70 p-3.5">
            <div className="text-xs font-bold text-ink">4. Composite Target Gate</div>
            <p className="mb-0 mt-1 text-xs leading-relaxed text-muted">
              Original glass-fibre/epoxy composite targets remain marked <code>BLOCKED / NO_GO</code>{" "}
              pending author clarification and run-to-paper mapping resolution.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
