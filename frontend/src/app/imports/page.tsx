"use client";

import { ArrowRight, Check, Database, FileUp, History, Upload } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { api, type ImportHistoryItem, type ImportPreviewResult } from "@/lib/api";

export default function ImportsPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [history, setHistory] = useState<ImportHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadHistory = useCallback(() => {
    setLoadingHistory(true);
    api.importHistory()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false));
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function validate(selected: File | null) {
    setFile(selected);
    setPreview(null);
    setMessage("");
    setError("");
    if (!selected) return;
    setBusy(true);
    try {
      setPreview(await api.previewImport(selected));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload could not be validated.");
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!file || !preview) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.confirmImport(file, preview.sha256);
      setMessage(`${result.records_imported} records persisted. Original file SHA-256: ${result.sha256}`);
      setPreview(null);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      loadHistory();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Import could not be committed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="Data management"
        title="Import and validate"
        description="Review schema, source metadata, measurement units, and duplicate checks before committing an experiment-template CSV."
      />
      <div className="mb-5">
        <Notice tone="info" title="Two-step import">
          Preview validates the selected file and computes its fingerprint. Only
          an explicit confirmation persists the original artifact and records.
          The protected raw dataset is never modified.
        </Notice>
      </div>
      {error && <div className="mb-4"><Notice tone="error" title="Import error">{error}</Notice></div>}
      {message && (
        <div className="mb-4">
          <Notice tone="success" title="Import saved">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>{message}</span>
              <Link href="/experiments" className="button-secondary text-xs font-semibold">
                View in registry <ArrowRight size={14} className="ml-1" />
              </Link>
            </div>
          </Notice>
        </div>
      )}

      <section className="panel p-5 sm:p-7">
        <label className="flex min-h-48 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-5 text-center transition hover:border-accent hover:bg-emerald-50/40">
          <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-white text-accent shadow-sm">
            <FileUp size={22} aria-hidden="true" />
          </span>
          <span className="font-semibold">Select an experiment CSV</span>
          <span className="mt-1 text-xs text-muted">UTF-8 or Latin-1 CSV · maximum 10 MB</span>
          <input
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(event) => void validate(event.currentTarget.files?.[0] ?? null)}
            ref={inputRef}
            type="file"
          />
        </label>
        {busy && <p className="mt-4 text-sm text-muted" role="status">Validating / saving import…</p>}
      </section>

      {preview && (
        <section className="panel mt-5 overflow-hidden">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line p-5">
            <div>
              <div className="flex items-center gap-2 font-semibold"><Upload size={17} aria-hidden="true" />{preview.filename}</div>
              <div className="mt-2 text-xs text-muted">
                {preview.format_name} · {preview.row_count} rows · {(preview.size_bytes / 1024).toFixed(1)} KB
              </div>
              <code className="mt-2 block break-all text-[11px] text-muted">SHA-256 {preview.sha256}</code>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${preview.can_confirm_import ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"}`}>
                {preview.can_confirm_import ? "READY TO COMMIT" : "CONFIRMATION BLOCKED"}
              </span>
              <button
                className="button-primary"
                disabled={busy || !preview.can_confirm_import}
                onClick={() => void confirm()}
                type="button"
              >
                <Check size={16} aria-hidden="true" />
                Confirm import
              </button>
            </div>
          </div>

          {/* Row Analysis Summary */}
          <div className="grid grid-cols-2 gap-3 border-b border-line bg-slate-50/60 p-5 sm:grid-cols-4">
            <div className="rounded-lg border border-line bg-white p-3 text-center">
              <span className="text-[11px] uppercase tracking-wide text-muted">Total Rows</span>
              <div className="text-xl font-bold text-ink">{preview.row_count}</div>
            </div>
            <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 text-center">
              <span className="text-[11px] uppercase tracking-wide text-emerald-800">Accepted Rows</span>
              <div className="text-xl font-bold text-emerald-800">{preview.accepted_rows}</div>
            </div>
            <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 text-center">
              <span className="text-[11px] uppercase tracking-wide text-amber-800">Duplicate Rows</span>
              <div className="text-xl font-bold text-amber-800">{preview.duplicate_rows}</div>
            </div>
            <div className="rounded-lg border border-rose-200 bg-rose-50/50 p-3 text-center">
              <span className="text-[11px] uppercase tracking-wide text-rose-800">Rejected / Errors</span>
              <div className="text-xl font-bold text-rose-800">{preview.rejected_rows}</div>
            </div>
          </div>

          {/* Duplicate Warnings */}
          {preview.is_duplicate_artifact && (
            <div className="p-5 border-b border-line">
              <Notice tone="error" title="Duplicate CSV artifact detected">
                This exact CSV file has already been persisted with cryptographic hash {preview.sha256}. Re-importing identical artifacts is blocked to maintain database integrity.
              </Notice>
            </div>
          )}

          {preview.duplicate_experiment_ids && preview.duplicate_experiment_ids.length > 0 && (
            <div className="p-5 border-b border-line">
              <Notice tone="warning" title={`${preview.duplicate_experiment_ids.length} colliding experiment identifier(s)`}>
                The following experiment identifiers already exist in PostgreSQL or appear multiple times in the uploaded file:
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {preview.duplicate_experiment_ids.map((id) => (
                    <span key={id} className="rounded bg-amber-100 px-2 py-0.5 font-mono text-[11px] text-amber-900">
                      {id}
                    </span>
                  ))}
                </div>
              </Notice>
            </div>
          )}

          {!preview.can_confirm_import && !preview.is_duplicate_artifact && (preview.duplicate_experiment_ids?.length ?? 0) === 0 && (
            <div className="p-5">
              <Notice tone="warning" title="This file cannot be committed as experiment records">
                Only valid files using the experiment-record template without schema errors can be committed.
                Existing source-extraction files remain evidence artifacts and are not
                silently remapped to new experimental runs.
              </Notice>
            </div>
          )}

          {!!preview.errors.length && <FindingList title="Validation errors" findings={preview.errors} tone="error" />}
          {!!preview.warnings.length && <FindingList title="Review warnings" findings={preview.warnings} tone="warning" />}
          {!!preview.preview_rows.length && (
            <div className="border-t border-line p-5">
              <h2 className="mb-3 mt-0 text-sm font-semibold">First rows (preview only)</h2>
              <div className="table-scroll">
                <table>
                  <thead><tr>{Object.keys(preview.preview_rows[0]).slice(0, 7).map((key) => <th key={key}>{key}</th>)}</tr></thead>
                  <tbody>
                    {preview.preview_rows.slice(0, 5).map((row, index) => (
                      <tr key={index}>{Object.keys(preview.preview_rows[0]).slice(0, 7).map((key) => <td className="max-w-56 truncate" key={key}>{row[key] || "—"}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Import History Section */}
      <section className="panel mt-8 p-5 sm:p-6" aria-label="Import history">
        <div className="flex flex-wrap items-center justify-between border-b border-line pb-4 gap-2">
          <div className="flex items-center gap-2">
            <History size={18} className="text-accent" aria-hidden="true" />
            <h2 className="m-0 text-base font-semibold text-ink">Import History</h2>
          </div>
          <span className="text-xs text-muted">
            {history.length} persisted artifact{history.length === 1 ? "" : "s"}
          </span>
        </div>

        {loadingHistory ? (
          <p className="mt-4 text-xs text-muted">Loading import history…</p>
        ) : history.length ? (
          <div className="table-scroll mt-4">
            <table>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Format</th>
                  <th>Rows</th>
                  <th>Size</th>
                  <th>SHA-256 Fingerprint</th>
                  <th>Import Date (UTC)</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold text-ink">{item.filename}</td>
                    <td className="text-xs text-muted">{item.format_name}</td>
                    <td>{item.row_count}</td>
                    <td className="text-xs text-muted">{(item.size_bytes / 1024).toFixed(1)} KB</td>
                    <td className="font-mono text-xs text-muted" title={item.sha256}>
                      {item.sha256.slice(0, 10)}…{item.sha256.slice(-6)}
                    </td>
                    <td className="text-xs text-muted">
                      {new Date(item.created_at_utc).toLocaleString()}
                    </td>
                    <td>
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                        {item.validation_outcome}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-muted">
            <Database size={24} className="mx-auto mb-2 text-slate-300" aria-hidden="true" />
            No CSV imports have been committed to the database yet.
          </div>
        )}
      </section>
    </>
  );
}

function FindingList({
  title,
  findings,
  tone,
}: {
  title: string;
  findings: { code: string; message: string; row_number?: number }[];
  tone: "error" | "warning";
}) {
  return (
    <div className="border-t border-line p-5">
      <h2 className={`mb-3 mt-0 text-sm font-semibold ${tone === "error" ? "text-rose-800" : "text-amber-900"}`}>{title} · {findings.length}</h2>
      <ul className="m-0 space-y-2 pl-5 text-xs text-muted">
        {findings.slice(0, 30).map((finding, index) => (
          <li key={`${finding.code}-${index}`}>
            <strong>{finding.code}</strong>{finding.row_number ? ` · row ${finding.row_number}` : ""}: {finding.message}
          </li>
        ))}
      </ul>
    </div>
  );
}

