"use client";

import {
  ArrowRight,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Edit2,
  Eye,
  FileText,
  Info,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { StatusBadge } from "@/components/status-badge";
import { API_BASE, api, type Experiment } from "@/lib/api";

export default function ExperimentsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted" role="status">Loading experiments…</p>}>
      <ExperimentsContent />
    </Suspense>
  );
}

function ExperimentsContent() {
  const searchParams = useSearchParams();
  const [records, setRecords] = useState<Experiment[]>([]);
  const [status, setStatus] = useState<"ALL" | "PLANNED" | "MEASURED">("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [materialFilter, setMaterialFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState<"id" | "experiment_id" | "record_status" | "material_system_as_recorded" | "experiment_date" | "created_at_utc">("id");
  const [sortDesc, setSortDesc] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  // Modals state
  const [detailRecord, setDetailRecord] = useState<Experiment | null>(null);
  const [editRecord, setEditRecord] = useState<Experiment | null>(null);
  const [deleteRecord, setDeleteRecord] = useState<Experiment | null>(null);
  const [showCreate, setShowCreate] = useState(searchParams.get("new") === "1");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    api.experiments({
      status: status === "ALL" ? undefined : status,
      query: searchQuery.trim() || undefined,
      material: materialFilter === "ALL" ? undefined : materialFilter,
      sortBy,
      sortDesc,
      limit: 500,
    })
      .then((data) => {
        setRecords(data);
        setPage(1);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [status, searchQuery, materialFilter, sortBy, sortDesc]);

  useEffect(() => {
    load();
  }, [load]);

  // Collect distinct material systems for filter dropdown
  const distinctMaterials = useMemo(() => {
    const set = new Set<string>();
    for (const r of records) {
      if (r.material_system_as_recorded) {
        set.add(r.material_system_as_recorded.trim());
      }
    }
    return Array.from(set).sort();
  }, [records]);

  // Client-side pagination slice
  const paginatedRecords = useMemo(() => {
    const start = (page - 1) * pageSize;
    return records.slice(start, start + pageSize);
  }, [records, page, pageSize]);

  const totalPages = Math.max(1, Math.ceil(records.length / pageSize));

  // Build CSV export URL matching active filters
  const exportUrl = useMemo(() => {
    const params = new URLSearchParams();
    if (status !== "ALL") params.set("record_status", status);
    if (searchQuery.trim()) params.set("query", searchQuery.trim());
    if (materialFilter !== "ALL") params.set("material_system", materialFilter);
    const qs = params.toString();
    return `${API_BASE}/api/v1/exports/experiments.csv${qs ? `?${qs}` : ""}`;
  }, [status, searchQuery, materialFilter]);

  async function handleDeleteConfirm() {
    if (!deleteRecord) return;
    try {
      await api.deleteExperiment(deleteRecord.experiment_id);
      setSaved(`Experiment record "${deleteRecord.experiment_id}" was deleted.`);
      setDeleteRecord(null);
      if (detailRecord?.experiment_id === deleteRecord.experiment_id) {
        setDetailRecord(null);
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete experiment record.");
      setDeleteRecord(null);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="Data management"
        title="Experiment records"
        description="Complete lifecycle management for planned experiments and measured observations with full provenance."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <a
              href={api.getRegistryPdfUrl({
                status: status === "ALL" ? undefined : status,
                material_system: materialFilter === "ALL" ? undefined : materialFilter,
                query: searchQuery || undefined,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="button-secondary text-xs"
              title="Download PDF report for current filtered view"
            >
              <FileText size={15} aria-hidden="true" />
              Export PDF
            </a>
            <a
              href={api.getRegistryCsvUrl({
                status: status === "ALL" ? undefined : status,
                material_system: materialFilter === "ALL" ? undefined : materialFilter,
                query: searchQuery || undefined,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="button-secondary text-xs"
              title="Download structured CSV for current filtered view"
            >
              <Download size={15} aria-hidden="true" />
              Export CSV
            </a>
            <button
              className="button-primary"
              id="btn-new-experiment"
              onClick={() => setShowCreate(true)}
              type="button"
            >
              <Plus size={16} aria-hidden="true" />
              New experiment
            </button>
          </div>
        }
      />

      {saved && (
        <div className="mb-4">
          <Notice tone="success" title="Record updated">
            <div className="flex items-center justify-between">
              <span>{saved}</span>
              <button
                type="button"
                className="ml-3 text-xs underline text-muted hover:text-ink"
                onClick={() => setSaved("")}
              >
                Dismiss
              </button>
            </div>
          </Notice>
        </div>
      )}

      {error && (
        <div className="mb-4">
          <Notice tone="error" title="Error">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button
                type="button"
                className="ml-3 text-xs underline text-muted hover:text-ink"
                onClick={() => setError("")}
              >
                Dismiss
              </button>
            </div>
          </Notice>
        </div>
      )}

      {/* Main Registry Panel */}
      <section className="panel">
        <div className="flex flex-col gap-4 border-b border-line px-5 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="m-0 text-base font-semibold">Registry</h2>
              <p className="mb-0 mt-1 text-xs text-muted">
                Persisted in PostgreSQL. Total matching records:{" "}
                <span className="font-semibold text-ink">{records.length}</span>
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                aria-label="Refresh records"
                className="button-secondary !p-2"
                onClick={load}
                title="Refresh records"
                type="button"
              >
                <RefreshCw size={16} aria-hidden="true" className={loading ? "animate-spin" : ""} />
              </button>
              <a
                className="button-secondary py-2"
                href={exportUrl}
                download="ai-tribotwin-experiments.csv"
                title="Export currently filtered records to CSV"
              >
                <Download size={15} aria-hidden="true" />
                Export CSV
              </a>
            </div>
          </div>

          {/* Filter & Search Toolbar */}
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
            {/* Search Input */}
            <div className="sm:col-span-2 relative">
              <label className="sr-only" htmlFor="experiment-search">Search experiments</label>
              <Search size={16} className="pointer-events-none absolute left-3 top-3 text-muted" aria-hidden="true" />
              <input
                className="field pl-9"
                id="experiment-search"
                placeholder="Search ID, material, operator, notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Status Filter */}
            <div>
              <label className="sr-only" htmlFor="status-filter">Filter by status</label>
              <select
                className="field"
                id="status-filter"
                value={status}
                onChange={(e) => setStatus(e.target.value as typeof status)}
              >
                <option value="ALL">All statuses</option>
                <option value="MEASURED">Measured only</option>
                <option value="PLANNED">Planned only</option>
              </select>
            </div>

            {/* Material Filter */}
            <div>
              <label className="sr-only" htmlFor="material-filter">Filter by material</label>
              <select
                className="field"
                id="material-filter"
                value={materialFilter}
                onChange={(e) => setMaterialFilter(e.target.value)}
              >
                <option value="ALL">All materials</option>
                {distinctMaterials.map((mat) => (
                  <option key={mat} value={mat}>
                    {mat}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-1.5">
              <label className="sr-only" htmlFor="sort-by">Sort records</label>
              <select
                className="field flex-1"
                id="sort-by"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              >
                <option value="id">Sort by creation ID</option>
                <option value="experiment_id">Sort by experiment ID</option>
                <option value="material_system_as_recorded">Sort by material</option>
                <option value="record_status">Sort by status</option>
                <option value="experiment_date">Sort by date</option>
              </select>
              <button
                type="button"
                className="button-secondary !p-2"
                onClick={() => setSortDesc((v) => !v)}
                title={sortDesc ? "Descending (click for Ascending)" : "Ascending (click for Descending)"}
                aria-label="Toggle sort order"
              >
                <ArrowUpDown size={16} aria-hidden="true" className={sortDesc ? "text-accent" : ""} />
              </button>
            </div>
          </div>
        </div>

        {/* Data Table */}
        {loading ? (
          <div className="p-12 text-center text-sm text-muted" role="status">
            <RefreshCw size={24} className="mx-auto mb-2 animate-spin text-accent" />
            Loading experiment records…
          </div>
        ) : records.length ? (
          <>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Experiment ID</th>
                    <th>Status</th>
                    <th>Material System & Composition</th>
                    <th>Test Conditions</th>
                    <th>Measured Responses</th>
                    <th>Provenance / Source</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedRecords.map((record) => (
                    <tr key={record.experiment_id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="whitespace-nowrap font-semibold">
                        <button
                          type="button"
                          className="text-accent underline font-semibold hover:text-emerald-900"
                          onClick={() => setDetailRecord(record)}
                        >
                          {record.experiment_id}
                        </button>
                        {record.replicate_group_id && (
                          <div className="text-[11px] font-normal text-muted">
                            Rep: {record.replicate_group_id}
                          </div>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={record.record_status} />
                      </td>
                      <td className="min-w-44">
                        <Link
                          href={`/analytics?material=${encodeURIComponent(record.material_system_as_recorded)}`}
                          className="font-medium text-ink hover:text-accent hover:underline inline-flex items-center gap-1 group"
                          title={`View engineering analytics for ${record.material_system_as_recorded}`}
                        >
                          <span>{record.material_system_as_recorded}</span>
                          <ArrowRight size={11} className="opacity-0 group-hover:opacity-100 transition-opacity text-accent" />
                        </Link>
                        {record.composition_as_recorded && (
                          <div className="mt-0.5 text-xs text-muted line-clamp-2">
                            {record.composition_as_recorded}
                          </div>
                        )}
                      </td>
                      <td className="min-w-48 text-xs text-muted">
                        {formatConditions(
                          record.record_status === "PLANNED"
                            ? record.planned_conditions
                            : record.measured_conditions,
                        )}
                      </td>
                      <td className="min-w-44 text-xs text-muted">
                        {record.record_status === "PLANNED" ? (
                          <span className="italic text-slate-400">Planned — awaiting measurement</span>
                        ) : (
                          formatMeasurements(record.measurements)
                        )}
                      </td>
                      <td className="min-w-48 text-xs text-muted">
                        <div>{record.source_artifact || "No source artifact"}</div>
                        {record.source_location && (
                          <div className="text-slate-500">{record.source_location}</div>
                        )}
                        {record.operator && (
                          <div className="text-[11px] text-slate-400">Op: {record.operator}</div>
                        )}
                      </td>
                      <td className="whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            className="button-outline !px-2.5 !py-1.5"
                            onClick={() => setDetailRecord(record)}
                            title="View full record details"
                            aria-label={`View record ${record.experiment_id}`}
                          >
                            <Eye size={14} aria-hidden="true" />
                            View
                          </button>
                          <button
                            type="button"
                            className="button-outline !px-2.5 !py-1.5"
                            onClick={() => setEditRecord(record)}
                            title="Edit record"
                            aria-label={`Edit record ${record.experiment_id}`}
                          >
                            <Edit2 size={14} aria-hidden="true" />
                            Edit
                          </button>
                          <button
                            type="button"
                            className="button-outline !px-2.5 !py-1.5 text-red-600 hover:border-red-300 hover:bg-red-50"
                            onClick={() => setDeleteRecord(record)}
                            title="Delete record"
                            aria-label={`Delete record ${record.experiment_id}`}
                          >
                            <Trash2 size={14} aria-hidden="true" />
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3 text-xs text-muted">
              <div className="flex items-center gap-2">
                <span>Rows per page:</span>
                <select
                  className="rounded border border-line bg-white px-2 py-1 text-xs text-ink"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
                <span>
                  Showing {(page - 1) * pageSize + 1} to{" "}
                  {Math.min(page * pageSize, records.length)} of {records.length} records
                </span>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  className="button-outline !px-2 !py-1"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  aria-label="Previous page"
                >
                  <ChevronLeft size={14} aria-hidden="true" />
                  Prev
                </button>
                <span className="px-2 font-medium text-ink">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  className="button-outline !px-2 !py-1"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  aria-label="Next page"
                >
                  Next
                  <ChevronRight size={14} aria-hidden="true" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="px-6 py-14 text-center">
            <div className="text-sm font-semibold">No records match the current filters</div>
            <p className="mx-auto mb-4 mt-1 max-w-md text-sm text-muted">
              {searchQuery || status !== "ALL" || materialFilter !== "ALL"
                ? "Try clearing or broadening your search queries and filter selections."
                : "Add a traceable measured observation or create a planned condition."}
            </p>
            <div className="flex justify-center gap-3">
              {(searchQuery || status !== "ALL" || materialFilter !== "ALL") && (
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => {
                    setSearchQuery("");
                    setStatus("ALL");
                    setMaterialFilter("ALL");
                  }}
                >
                  Clear all filters
                </button>
              )}
              <button
                type="button"
                className="button-primary"
                onClick={() => setShowCreate(true)}
              >
                Create new experiment
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Detail Modal */}
      {detailRecord && (
        <DetailModal
          record={detailRecord}
          onClose={() => setDetailRecord(null)}
          onEdit={() => {
            const r = detailRecord;
            setDetailRecord(null);
            setEditRecord(r);
          }}
          onDelete={() => {
            const r = detailRecord;
            setDetailRecord(null);
            setDeleteRecord(r);
          }}
        />
      )}

      {/* Edit Modal */}
      {editRecord && (
        <EditModal
          record={editRecord}
          onClose={() => setEditRecord(null)}
          onSaved={(msg) => {
            setSaved(msg);
            setEditRecord(null);
            load();
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteRecord && (
        <DeleteConfirmModal
          record={deleteRecord}
          onClose={() => setDeleteRecord(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}

      {/* Create Experiment Modal */}
      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onSaved={(msg) => {
            setSaved(msg);
            setShowCreate(false);
            load();
          }}
        />
      )}
    </>
  );
}

// -----------------------------------------------------------------------------
// Format Helpers
// -----------------------------------------------------------------------------

function formatConditions(conditions?: Record<string, number>) {
  if (!conditions || !Object.keys(conditions).length) {
    return "No conditions recorded";
  }
  const labels: Record<string, string> = {
    load_n: "N",
    sliding_velocity_m_per_s: "m/s",
    sliding_distance_m: "m",
    test_duration_min: "min",
  };
  return Object.entries(conditions)
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${value} ${labels[key] ?? ""}`)
    .join(" · ");
}

function formatMeasurements(measurements?: Record<string, unknown>) {
  if (!measurements || !Object.keys(measurements).length) {
    return "No responses recorded";
  }
  const items: string[] = [];
  if (measurements.coefficient_of_friction && typeof measurements.coefficient_of_friction === "object") {
    const cof = measurements.coefficient_of_friction as { value: number; unit_as_recorded: string };
    items.push(`COF: ${cof.value} ${cof.unit_as_recorded || ""}`);
  }
  if (measurements.wear_measurement && typeof measurements.wear_measurement === "object") {
    const wm = measurements.wear_measurement as { value: number; unit_as_recorded: string };
    const name = (measurements.wear_measurement_name_as_recorded as string) || "wear";
    items.push(`${name}: ${wm.value} ${wm.unit_as_recorded || ""}`);
  }
  return items.length ? items.join(" · ") : "No responses recorded";
}

// -----------------------------------------------------------------------------
// Detail Modal Component
// -----------------------------------------------------------------------------

function DetailModal({
  record,
  onClose,
  onEdit,
  onDelete,
}: {
  record: Experiment;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="detail-modal-title"
    >
      <div className="panel max-h-[90vh] w-full max-w-3xl overflow-y-auto p-6 shadow-2xl">
        <div className="flex items-start justify-between border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 id="detail-modal-title" className="m-0 text-xl font-bold text-ink">
                {record.experiment_id}
              </h2>
              <StatusBadge status={record.record_status} />
            </div>
            <p className="mt-1 text-xs text-muted">
              Database ID #{record.id} · Created: {new Date(record.created_at_utc).toLocaleString()}
            </p>
          </div>
          <button
            type="button"
            className="rounded p-1 text-muted hover:bg-slate-100 hover:text-ink"
            onClick={onClose}
            aria-label="Close detail modal"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6 space-y-6 text-sm">
          {/* Planned record contextual banner */}
          {record.record_status === "PLANNED" && (
            <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-3.5 text-xs text-amber-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-start sm:items-center gap-2.5">
                <Info size={16} className="text-amber-800 shrink-0 mt-0.5 sm:mt-0" aria-hidden="true" />
                <span>
                  <strong>Planned Test Design:</strong> These conditions represent prospective laboratory parameters. No physical measurements exist until experiments are performed.
                </span>
              </div>
              <Link href="/planning" className="button-secondary !py-1 !px-2.5 text-xs font-semibold whitespace-nowrap self-start sm:self-auto">
                Planning Module
              </Link>
            </div>
          )}

          {/* Material & Identification */}
          <section>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
              Material System & Composition
            </h3>
            <div className="mt-2 grid gap-4 rounded-lg bg-slate-50 p-4 sm:grid-cols-2">
              <div>
                <div className="flex items-center justify-between">
                  <span className="field-label">Material System</span>
                  <Link
                    href={`/analytics?material=${encodeURIComponent(record.material_system_as_recorded)}`}
                    className="text-[11px] font-medium text-accent hover:underline inline-flex items-center gap-1"
                    title={`View analytics for ${record.material_system_as_recorded}`}
                  >
                    <span>View Analytics</span>
                    <ArrowRight size={11} />
                  </Link>
                </div>
                <span className="font-semibold text-ink">{record.material_system_as_recorded}</span>
              </div>
              <div>
                <span className="field-label">Composition As Recorded</span>
                <span className="text-ink">{record.composition_as_recorded || "Not specified"}</span>
              </div>
              <div>
                <span className="field-label">Composition Reference</span>
                <span className="text-ink">{record.composition_source_reference || "None"}</span>
              </div>
              <div>
                <span className="field-label">Replicate Group</span>
                <span className="text-ink">{record.replicate_group_id || "None"}</span>
              </div>
              {record.planned_by && (
                <div>
                  <span className="field-label">Planned By</span>
                  <span className="text-ink">{record.planned_by}</span>
                </div>
              )}
            </div>
          </section>

          {/* Test Conditions */}
          <section>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
              {record.record_status === "PLANNED" ? "Planned Test Conditions" : "Measured Test Conditions"}
            </h3>
            <div className="mt-2 grid gap-3 rounded-lg border border-line p-4 sm:grid-cols-2 md:grid-cols-4">
              {(() => {
                const c = record.record_status === "PLANNED" ? record.planned_conditions : record.measured_conditions;
                return (
                  <>
                    <div className="rounded bg-slate-50 p-2.5">
                      <span className="field-label">Normal Load</span>
                      <span className="text-base font-semibold text-ink">
                        {c?.load_n !== undefined && c.load_n !== null ? `${c.load_n} N` : "—"}
                      </span>
                    </div>
                    <div className="rounded bg-slate-50 p-2.5">
                      <span className="field-label">Sliding Speed</span>
                      <span className="text-base font-semibold text-ink">
                        {c?.sliding_velocity_m_per_s !== undefined && c.sliding_velocity_m_per_s !== null
                          ? `${c.sliding_velocity_m_per_s} m/s`
                          : "—"}
                      </span>
                    </div>
                    <div className="rounded bg-slate-50 p-2.5">
                      <span className="field-label">Sliding Distance</span>
                      <span className="text-base font-semibold text-ink">
                        {c?.sliding_distance_m !== undefined && c.sliding_distance_m !== null
                          ? `${c.sliding_distance_m} m`
                          : "—"}
                      </span>
                    </div>
                    <div className="rounded bg-slate-50 p-2.5">
                      <span className="field-label">Test Duration</span>
                      <span className="text-base font-semibold text-ink">
                        {c?.test_duration_min !== undefined && c.test_duration_min !== null
                          ? `${c.test_duration_min} min`
                          : "—"}
                      </span>
                    </div>
                  </>
                );
              })()}
            </div>
          </section>

          {/* Measured Responses */}
          <section>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
              Experimental Measurements
            </h3>
            {record.record_status === "PLANNED" ? (
              <div className="mt-2 rounded-lg border border-dashed border-line p-4 text-xs italic text-muted">
                This is a planned condition. Measurements have not been taken. Scientific safeguards prevent attributing unmeasured values to planned records.
              </div>
            ) : (
              <div className="mt-2 grid gap-3 rounded-lg border border-line p-4 sm:grid-cols-2">
                {(() => {
                  const m = record.measurements as Record<string, unknown> | undefined;
                  const cof = m?.coefficient_of_friction as { value: number; unit_as_recorded: string } | undefined;
                  const wm = m?.wear_measurement as { value: number; unit_as_recorded: string } | undefined;
                  const wmName = (m?.wear_measurement_name_as_recorded as string) || "Wear";
                  return (
                    <>
                      <div className="rounded bg-slate-50 p-3">
                        <span className="field-label">Coefficient of Friction</span>
                        <div className="text-xl font-bold text-ink">
                          {cof?.value !== undefined ? cof.value : "—"}
                        </div>
                        <span className="text-xs text-muted">{cof?.unit_as_recorded || "dimensionless"}</span>
                      </div>
                      <div className="rounded bg-slate-50 p-3">
                        <span className="field-label">{wmName}</span>
                        <div className="text-xl font-bold text-ink">
                          {wm?.value !== undefined ? wm.value : "—"}
                        </div>
                        <span className="text-xs text-muted">{wm?.unit_as_recorded || "Not recorded"}</span>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </section>

          {/* Provenance & Audit Trail */}
          <section>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
              Provenance & Instrument Tracking
            </h3>
            <div className="mt-2 grid gap-3 rounded-lg bg-slate-50 p-4 sm:grid-cols-2">
              <div>
                <span className="field-label">Source Artifact</span>
                <span className="font-mono text-xs text-ink">{record.source_artifact || "—"}</span>
              </div>
              <div>
                <span className="field-label">Source Location</span>
                <span className="text-ink">{record.source_location || "—"}</span>
              </div>
              <div>
                <span className="field-label">Operator</span>
                <span className="text-ink">{record.operator || "—"}</span>
              </div>
              <div>
                <span className="field-label">Instrument ID</span>
                <span className="text-ink">{record.instrument_id || "—"}</span>
              </div>
              <div>
                <span className="field-label">Experiment Date</span>
                <span className="text-ink">{record.experiment_date || "—"}</span>
              </div>
              <div>
                <span className="field-label">Import SHA-256</span>
                <span className="font-mono text-[11px] text-muted truncate block">
                  {record.import_sha256 || "Direct API entry"}
                </span>
              </div>
            </div>
          </section>

          {/* Notes */}
          {record.notes && (
            <section>
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Notes</h3>
              <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-ink whitespace-pre-wrap">
                {record.notes}
              </p>
            </section>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-line pt-4">
          <button
            type="button"
            className="button-outline text-red-600 hover:border-red-300 hover:bg-red-50"
            onClick={onDelete}
          >
            <Trash2 size={15} aria-hidden="true" />
            Delete record
          </button>
          <div className="flex flex-wrap items-center gap-2">
            <a
              href={api.getExperimentPdfUrl(record.experiment_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="button-secondary text-xs"
              title="Download formal engineering PDF report"
            >
              <FileText size={15} aria-hidden="true" />
              Download Report (PDF)
            </a>
            <button type="button" className="button-secondary" onClick={onClose}>
              Close
            </button>
            <button type="button" className="button-primary" onClick={onEdit}>
              <Edit2 size={15} aria-hidden="true" />
              Edit record
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Edit Modal Component
// -----------------------------------------------------------------------------

function EditModal({
  record,
  onClose,
  onSaved,
}: {
  record: Experiment;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const cond = record.record_status === "PLANNED" ? record.planned_conditions : record.measured_conditions;
  const meas = record.measurements as Record<string, unknown> | undefined;
  const cof = meas?.coefficient_of_friction as { value: number; unit_as_recorded: string } | undefined;
  const wm = meas?.wear_measurement as { value: number; unit_as_recorded: string } | undefined;

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");

    const data = new FormData(event.currentTarget);
    const optionalNumber = (name: string) => {
      const val = String(data.get(name) ?? "").trim();
      return val ? Number(val) : null;
    };

    const isPlanned = record.record_status === "PLANNED";

    const payload: Record<string, unknown> = {
      material_system_as_recorded: String(data.get("material") ?? "").trim(),
      composition_as_recorded: String(data.get("composition") ?? "").trim(),
      composition_source_reference: String(data.get("composition_source_reference") ?? "").trim(),
      replicate_group_id: String(data.get("replicate_group_id") ?? "").trim(),
      notes: String(data.get("notes") ?? "").trim(),
    };

    if (isPlanned) {
      payload.planned_by = String(data.get("planned_by") ?? "").trim();
      payload.planned_conditions = {
        load_n: optionalNumber("load_n"),
        sliding_velocity_m_per_s: optionalNumber("velocity"),
        sliding_distance_m: optionalNumber("distance"),
        test_duration_min: optionalNumber("duration"),
      };
    } else {
      payload.operator = String(data.get("operator") ?? "").trim();
      payload.instrument_id = String(data.get("instrument") ?? "").trim();
      payload.experiment_date = String(data.get("experiment_date") ?? "").trim() || null;
      payload.source_artifact = String(data.get("source_artifact") ?? "").trim();
      payload.source_location = String(data.get("source_location") ?? "").trim();
      payload.measured_conditions = {
        load_n: optionalNumber("load_n"),
        sliding_velocity_m_per_s: optionalNumber("velocity"),
        sliding_distance_m: optionalNumber("distance"),
        test_duration_min: optionalNumber("duration"),
      };
      const cofVal = optionalNumber("cof");
      const wearVal = optionalNumber("wear_val");
      const wearName = String(data.get("wear_name") ?? "").trim();
      const wearUnit = String(data.get("wear_unit") ?? "").trim();

      payload.measurements = {
        coefficient_of_friction: cofVal !== null ? {
          value: cofVal,
          unit_as_recorded: String(data.get("cof_unit") ?? "dimensionless").trim() || "dimensionless",
        } : null,
        wear_measurement_name_as_recorded: wearName,
        wear_measurement: wearVal !== null ? {
          value: wearVal,
          unit_as_recorded: wearUnit,
        } : null,
      };
    }

    try {
      await api.updateExperiment(record.experiment_id, payload);
      onSaved(`Experiment record "${record.experiment_id}" successfully updated.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Record could not be updated.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-modal-title"
    >
      <form
        onSubmit={submit}
        className="panel max-h-[90vh] w-full max-w-3xl overflow-y-auto p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 id="edit-modal-title" className="m-0 text-xl font-bold text-ink">
                Edit {record.experiment_id}
              </h2>
              <StatusBadge status={record.record_status} />
            </div>
            <p className="mt-1 text-xs text-muted">
              Modify conditions, provenance, and responses. Scientific constraints are strictly validated by the API.
            </p>
          </div>
          <button
            type="button"
            className="rounded p-1 text-muted hover:bg-slate-100 hover:text-ink"
            onClick={onClose}
            aria-label="Close edit modal"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        {error && (
          <div className="mt-4">
            <Notice tone="error" title="Update failed">{error}</Notice>
          </div>
        )}

        <div className="mt-6 space-y-5 text-sm">
          {/* Material & Identification */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Material system as recorded"
              name="material"
              defaultValue={record.material_system_as_recorded}
              required
            />
            {record.record_status === "PLANNED" ? (
              <Field
                label="Planned by"
                name="planned_by"
                defaultValue={record.planned_by}
              />
            ) : (
              <Field
                label="Replicate / Control group ID"
                name="replicate_group_id"
                defaultValue={record.replicate_group_id}
              />
            )}
            <Field
              label="Composition as recorded"
              name="composition"
              defaultValue={record.composition_as_recorded}
            />
            <Field
              label="Composition source reference"
              name="composition_source_reference"
              defaultValue={record.composition_source_reference}
            />
          </div>

          {/* Test Conditions */}
          <fieldset className="rounded-lg border border-line p-4">
            <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
              {record.record_status === "PLANNED" ? "Planned test conditions" : "Measured test conditions *"}
            </legend>
            <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
              <Field
                label="Load (N)"
                name="load_n"
                type="number"
                defaultValue={cond?.load_n?.toString() ?? ""}
                required={record.record_status === "MEASURED"}
              />
              <Field
                label="Velocity (m/s)"
                name="velocity"
                type="number"
                defaultValue={cond?.sliding_velocity_m_per_s?.toString() ?? ""}
                required={record.record_status === "MEASURED"}
              />
              <Field
                label="Distance (m)"
                name="distance"
                type="number"
                defaultValue={cond?.sliding_distance_m?.toString() ?? ""}
                required={record.record_status === "MEASURED"}
              />
              <Field
                label="Duration (min)"
                name="duration"
                type="number"
                defaultValue={cond?.test_duration_min?.toString() ?? ""}
              />
            </div>
          </fieldset>

          {/* Measured Responses (Only for MEASURED) */}
          {record.record_status === "MEASURED" && (
            <fieldset className="rounded-lg border border-line p-4">
              <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
                Measured Tribological Responses
              </legend>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field
                  label="COF value"
                  name="cof"
                  type="number"
                  defaultValue={cof?.value?.toString() ?? ""}
                />
                <Field
                  label="COF unit as recorded"
                  name="cof_unit"
                  defaultValue={cof?.unit_as_recorded ?? "dimensionless"}
                />
                <Field
                  label="Wear measurement name"
                  name="wear_name"
                  placeholder="e.g. specific wear rate"
                  defaultValue={(meas?.wear_measurement_name_as_recorded as string) ?? ""}
                />
                <div className="grid grid-cols-2 gap-2">
                  <Field
                    label="Wear value"
                    name="wear_val"
                    type="number"
                    defaultValue={wm?.value?.toString() ?? ""}
                  />
                  <Field
                    label="Wear unit"
                    name="wear_unit"
                    placeholder="e.g. mm3/N-m"
                    defaultValue={wm?.unit_as_recorded ?? ""}
                  />
                </div>
              </div>
            </fieldset>
          )}

          {/* Provenance (Only for MEASURED) */}
          {record.record_status === "MEASURED" && (
            <fieldset className="rounded-lg border border-line p-4">
              <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
                Source Provenance & Equipment
              </legend>
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                <Field
                  label="Operator"
                  name="operator"
                  defaultValue={record.operator}
                />
                <Field
                  label="Instrument ID"
                  name="instrument"
                  defaultValue={record.instrument_id}
                />
                <Field
                  label="Experiment date"
                  name="experiment_date"
                  type="date"
                  defaultValue={record.experiment_date ?? ""}
                />
                <Field
                  label="Source artifact"
                  name="source_artifact"
                  defaultValue={record.source_artifact}
                  required
                />
                <Field
                  label="Source location / run ID"
                  name="source_location"
                  defaultValue={record.source_location}
                  required
                />
              </div>
            </fieldset>
          )}

          {/* Notes */}
          <div>
            <label className="block">
              <span className="field-label">Notes</span>
              <textarea
                className="field min-h-20"
                name="notes"
                defaultValue={record.notes}
              />
            </label>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-2 border-t border-line pt-4">
          <button type="button" className="button-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button type="submit" className="button-primary" disabled={busy}>
            {busy ? "Saving changes…" : "Save changes"}
          </button>
        </div>
      </form>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Delete Confirmation Modal Component
// -----------------------------------------------------------------------------

function DeleteConfirmModal({
  record,
  onClose,
  onConfirm,
}: {
  record: Experiment;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  async function handleConfirm() {
    setBusy(true);
    await onConfirm();
    setBusy(false);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-sm"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      aria-describedby="delete-dialog-desc"
    >
      <div className="panel max-w-md w-full p-6 shadow-2xl">
        <h2 id="delete-dialog-title" className="m-0 text-lg font-bold text-ink">
          Confirm Deletion
        </h2>
        <p id="delete-dialog-desc" className="mt-2 text-sm text-muted">
          Are you sure you want to permanently delete experiment record{" "}
          <strong className="text-ink">{record.experiment_id}</strong>?
        </p>
        <div className="mt-3 rounded-lg bg-red-50 p-3 text-xs text-red-800">
          This record ({record.record_status}, {record.material_system_as_recorded}) will be permanently removed from PostgreSQL. This action cannot be undone.
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            className="button-secondary"
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            type="button"
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50"
            onClick={handleConfirm}
            disabled={busy}
          >
            {busy ? "Deleting…" : "Confirm Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Create Record Modal Component
// -----------------------------------------------------------------------------

function CreateModal({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const [mode, setMode] = useState<"MEASURED" | "PLANNED">("MEASURED");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");

    const data = new FormData(event.currentTarget);
    const optionalNumber = (name: string) => {
      const val = String(data.get(name) ?? "").trim();
      return val ? Number(val) : null;
    };

    if (mode === "MEASURED") {
      const payload = {
        experiment_id: String(data.get("experiment_id") ?? "").trim(),
        record_status: "MEASURED",
        material_system_as_recorded: String(data.get("material") ?? "").trim(),
        composition_as_recorded: String(data.get("composition") ?? "").trim(),
        composition_source_reference: String(data.get("composition_source_reference") ?? "").trim(),
        replicate_group_id: String(data.get("replicate_group_id") ?? "").trim(),
        measured_conditions: {
          load_n: optionalNumber("load_n"),
          sliding_velocity_m_per_s: optionalNumber("velocity"),
          sliding_distance_m: optionalNumber("distance"),
          test_duration_min: optionalNumber("duration"),
        },
        measurements: {
          coefficient_of_friction: optionalNumber("cof") === null ? null : {
            value: optionalNumber("cof"),
            unit_as_recorded: String(data.get("cof_unit") ?? "dimensionless").trim() || "dimensionless",
          },
        },
        operator: String(data.get("operator") ?? "").trim(),
        instrument_id: String(data.get("instrument") ?? "").trim(),
        experiment_date: String(data.get("experiment_date") ?? "").trim() || null,
        source_artifact: String(data.get("source_artifact") ?? "").trim(),
        source_location: String(data.get("source_location") ?? "").trim(),
        notes: String(data.get("notes") ?? "").trim(),
      };
      try {
        await api.createExperiment(payload);
        onSaved("Measured observation and provenance successfully recorded.");
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Record could not be saved.");
      } finally {
        setBusy(false);
      }
    } else {
      const payload = {
        experiment_id: String(data.get("experiment_id") ?? "").trim(),
        record_status: "PLANNED",
        planned_by: String(data.get("planned_by") ?? "").trim(),
        material_system_as_recorded: String(data.get("material") ?? "").trim(),
        composition_as_recorded: String(data.get("composition") ?? "").trim(),
        composition_source_reference: String(data.get("composition_source_reference") ?? "").trim(),
        planned_conditions: {
          load_n: optionalNumber("load_n"),
          sliding_velocity_m_per_s: optionalNumber("velocity"),
          sliding_distance_m: optionalNumber("distance"),
          test_duration_min: optionalNumber("duration"),
        },
        notes: String(data.get("notes") ?? "").trim(),
      };
      try {
        await api.createPlan(payload);
        onSaved("Planned experiment condition recorded.");
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Plan could not be saved.");
      } finally {
        setBusy(false);
      }
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-modal-title"
    >
      <form
        onSubmit={submit}
        className="panel max-h-[90vh] w-full max-w-3xl overflow-y-auto p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between border-b border-line pb-4">
          <div>
            <h2 id="create-modal-title" className="m-0 text-xl font-bold text-ink">
              Create Experiment Record
            </h2>
            <div className="mt-2 flex items-center gap-2">
              <button
                type="button"
                className={`rounded px-3 py-1 text-xs font-semibold ${
                  mode === "MEASURED"
                    ? "bg-accent text-white"
                    : "bg-slate-100 text-muted hover:text-ink"
                }`}
                onClick={() => setMode("MEASURED")}
              >
                Measured observation
              </button>
              <button
                type="button"
                className={`rounded px-3 py-1 text-xs font-semibold ${
                  mode === "PLANNED"
                    ? "bg-accent text-white"
                    : "bg-slate-100 text-muted hover:text-ink"
                }`}
                onClick={() => setMode("PLANNED")}
              >
                Planned experiment
              </button>
            </div>
          </div>
          <button
            type="button"
            className="rounded p-1 text-muted hover:bg-slate-100 hover:text-ink"
            onClick={onClose}
            aria-label="Close create modal"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        {error && (
          <div className="mt-4">
            <Notice tone="error" title="Creation failed">{error}</Notice>
          </div>
        )}

        <div className="mt-6 space-y-4 text-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Experiment ID" name="experiment_id" required />
            <Field label="Material system as recorded" name="material" required />
            {mode === "PLANNED" ? (
              <Field label="Planned by" name="planned_by" required />
            ) : (
              <Field label="Replicate / Control group ID" name="replicate_group_id" />
            )}
            <Field label="Composition as recorded" name="composition" required />
            <Field
              label="Composition source reference"
              name="composition_source_reference"
              placeholder="e.g. batch-01 / spec sheet"
              required={mode === "MEASURED"}
            />
          </div>

          <fieldset className="rounded-lg border border-line p-4">
            <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
              {mode === "MEASURED" ? "Measured Test Conditions *" : "Planned Test Conditions *"}
            </legend>
            <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
              <Field label="Load (N)" name="load_n" required type="number" />
              <Field label="Velocity (m/s)" name="velocity" required type="number" />
              <Field label="Distance (m)" name="distance" required type="number" />
              <Field label="Duration (min)" name="duration" type="number" />
            </div>
          </fieldset>

          {mode === "MEASURED" && (
            <>
              <fieldset className="rounded-lg border border-line p-4">
                <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
                  Experimental Responses *
                </legend>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="COF value" name="cof" type="number" required />
                  <Field label="COF unit as recorded" name="cof_unit" defaultValue="dimensionless" />
                </div>
              </fieldset>

              <fieldset className="rounded-lg border border-line p-4">
                <legend className="px-2 text-xs font-bold uppercase tracking-wider text-muted">
                  Source Provenance & Equipment *
                </legend>
                <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                  <Field label="Source artifact" name="source_artifact" placeholder="e.g. lab_run_01.csv" required />
                  <Field label="Page / Table / Run ID" name="source_location" placeholder="e.g. Table 2, Row 4" required />
                  <Field label="Operator" name="operator" />
                  <Field label="Instrument ID" name="instrument" />
                  <Field label="Experiment date" name="experiment_date" type="date" />
                </div>
              </fieldset>
            </>
          )}

          <div>
            <label className="block">
              <span className="field-label">Notes</span>
              <textarea className="field min-h-20" name="notes" />
            </label>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-2 border-t border-line pt-4">
          <button type="button" className="button-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button type="submit" className="button-primary" disabled={busy}>
            {busy ? "Saving record…" : `Save ${mode.toLowerCase()} record`}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
  placeholder,
  required,
  type = "text",
}: {
  label: string;
  name: string;
  defaultValue?: string;
  placeholder?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="field-label">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </span>
      <input
        className="field"
        defaultValue={defaultValue}
        name={name}
        placeholder={placeholder}
        required={required}
        step={type === "number" ? "any" : undefined}
        type={type}
      />
    </label>
  );
}
