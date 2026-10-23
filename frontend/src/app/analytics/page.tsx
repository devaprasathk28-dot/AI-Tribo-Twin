"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Calendar,
  CheckCircle2,
  Database,
  Download,
  FileText,
  Info,
  Layers,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { Notice } from "@/components/notice";
import { PageHeading } from "@/components/page-heading";
import { StatusBadge } from "@/components/status-badge";
import { api, type AnalyticsResponse } from "@/lib/api";

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted" role="status">Loading engineering analytics…</p>}>
      <AnalyticsContent />
    </Suspense>
  );
}

function AnalyticsContent() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [materialFilter, setMaterialFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "MEASURED" | "PLANNED">("ALL");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Active wear group selection for wear distribution tab
  const [selectedWearGroupIndex, setSelectedWearGroupIndex] = useState(0);

  // Active condition for relationship scatter chart
  const [activeScatterCondition, setActiveScatterCondition] = useState<"load_n" | "sliding_velocity_m_per_s" | "sliding_distance_m">("load_n");

  const loadData = useCallback(() => {
    setLoading(true);
    setError("");
    api.analytics({
      material: materialFilter === "ALL" ? undefined : materialFilter,
      status: statusFilter === "ALL" ? undefined : statusFilter,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    })
      .then((res) => {
        setData(res);
        setSelectedWearGroupIndex(0);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [materialFilter, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const hasActiveFilters = materialFilter !== "ALL" || statusFilter !== "ALL" || Boolean(dateFrom) || Boolean(dateTo);

  const resetFilters = () => {
    setMaterialFilter("ALL");
    setStatusFilter("ALL");
    setDateFrom("");
    setDateTo("");
  };

  // Pie chart breakdown for measured vs planned
  const statusPieData = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Measured", value: data.kpis.measured_records, color: "#187b68" },
      { name: "Planned", value: data.kpis.planned_records, color: "#b96618" },
    ].filter((item) => item.value > 0);
  }, [data]);

  // Wear distribution active group
  const activeWearGroup = useMemo(() => {
    if (!data?.wear_distribution.groups.length) return null;
    return data.wear_distribution.groups[selectedWearGroupIndex] || data.wear_distribution.groups[0];
  }, [data, selectedWearGroupIndex]);

  // Scatter relationship data points
  const scatterData = useMemo(() => {
    if (!data?.cof_relationships.points.length) return [];
    return data.cof_relationships.points
      .filter((pt) => pt[activeScatterCondition] !== null && pt[activeScatterCondition] !== undefined)
      .map((pt) => ({
        x: pt[activeScatterCondition],
        y: pt.coefficient_of_friction,
        id: pt.experiment_id,
        material: pt.material_system,
      }));
  }, [data, activeScatterCondition]);

  const scatterConditionLabels: Record<string, { label: string; unit: string }> = {
    load_n: { label: "Normal Load", unit: "N" },
    sliding_velocity_m_per_s: { label: "Sliding Speed", unit: "m/s" },
    sliding_distance_m: { label: "Sliding Distance", unit: "m" },
  };

  return (
    <>
      <PageHeading
        eyebrow="Data intelligence"
        title="Engineering analytics & visualizations"
        description="Exploratory distributions, experimental trends, and physical condition relationships calculated directly from verified database records."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <a
              href={api.getAnalyticsPdfUrl({
                material_system: materialFilter === "ALL" ? undefined : materialFilter,
                date_start: dateFrom || undefined,
                date_end: dateTo || undefined,
                status: statusFilter === "ALL" ? undefined : statusFilter,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="button-secondary text-xs"
              title="Download PDF report of current analytics view"
            >
              <FileText size={15} aria-hidden="true" />
              Export PDF
            </a>
            <a
              href={api.getAnalyticsCsvUrl({
                material_system: materialFilter === "ALL" ? undefined : materialFilter,
                date_start: dateFrom || undefined,
                date_end: dateTo || undefined,
                status: statusFilter === "ALL" ? undefined : statusFilter,
              })}
              target="_blank"
              rel="noopener noreferrer"
              className="button-secondary text-xs"
              title="Download CSV summary of analytics metrics"
            >
              <Download size={15} aria-hidden="true" />
              Export CSV
            </a>
            <button
              aria-label="Refresh analytics data"
              className="button-secondary !p-2"
              onClick={loadData}
              title="Refresh analytics"
              type="button"
            >
              <RefreshCw size={16} aria-hidden="true" className={loading ? "animate-spin" : ""} />
            </button>
            <Link className="button-secondary" href="/experiments">
              View records registry
            </Link>
          </div>
        }
      />

      {/* Scientific Integrity Advisory Banner */}
      <div className="mb-6 rounded-xl border border-line bg-slate-50/80 p-4 shadow-sm text-xs text-muted flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Info size={16} className="text-accent shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong className="text-ink font-semibold">Scientific Safeguard Notice:</strong> All figures and distributions are computed from active records in PostgreSQL without silent imputation. Descriptive correlation between test parameters and friction does not establish causation. Original glass-fibre/epoxy composite targets remain <span className="font-semibold text-warning">BLOCKED / NO_GO</span>.
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <StatusBadge status="BLOCKED" />
          <span className="text-[11px] font-mono text-slate-500">Composite ML Gated</span>
        </div>
      </div>

      {error && (
        <div className="mb-6">
          <Notice tone="error" title="Analytics query error">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button type="button" className="underline ml-2" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          </Notice>
        </div>
      )}

      {/* Filter Toolbar */}
      <section className="panel mb-6 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3 mb-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={15} className="text-accent" aria-hidden="true" />
            <h2 className="m-0 text-sm font-semibold text-ink">Analytical Filters</h2>
          </div>
          {hasActiveFilters && (
            <button
              type="button"
              className="text-xs text-muted hover:text-ink underline"
              onClick={resetFilters}
            >
              Reset all filters
            </button>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
          {/* Material Filter */}
          <div>
            <label className="field-label" htmlFor="filter-material">Material System</label>
            <select
              id="filter-material"
              className="field"
              value={materialFilter}
              onChange={(e) => setMaterialFilter(e.target.value)}
            >
              <option value="ALL">All material systems</option>
              {data?.distinct_material_names.map((mat) => (
                <option key={mat} value={mat}>
                  {mat}
                </option>
              ))}
            </select>
          </div>

          {/* Record Status Filter */}
          <div>
            <label className="field-label" htmlFor="filter-status">Record Status</label>
            <select
              id="filter-status"
              className="field"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            >
              <option value="ALL">All states (Measured & Planned)</option>
              <option value="MEASURED">Measured only</option>
              <option value="PLANNED">Planned only</option>
            </select>
          </div>

          {/* Date From */}
          <div>
            <label className="field-label" htmlFor="filter-date-from">Experiment Date (From)</label>
            <input
              id="filter-date-from"
              type="date"
              className="field"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>

          {/* Date To */}
          <div>
            <label className="field-label" htmlFor="filter-date-to">Experiment Date (To)</label>
            <input
              id="filter-date-to"
              type="date"
              className="field"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* KPI Summary Cards */}
      <section className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <KpiCard
          title="Total Records"
          value={data?.kpis.total_records ?? "—"}
          subtitle="Filtered cohort"
          icon={Database}
          highlight
        />
        <KpiCard
          title="Measured Observations"
          value={data?.kpis.measured_records ?? "—"}
          subtitle="Verified physical runs"
          icon={CheckCircle2}
          color="emerald"
        />
        <KpiCard
          title="Planned Conditions"
          value={data?.kpis.planned_records ?? "—"}
          subtitle="Proposed test designs"
          icon={Calendar}
          color="amber"
        />
        <KpiCard
          title="Material Systems"
          value={data?.kpis.distinct_materials_count ?? "—"}
          subtitle="Distinct formulations"
          icon={Layers}
        />
        <KpiCard
          title="With Measured COF"
          value={data?.kpis.records_with_cof ?? "—"}
          subtitle="Finite coefficient values"
          icon={Activity}
          color="teal"
        />
        <KpiCard
          title="With Measured Wear"
          value={data?.kpis.records_with_wear ?? "—"}
          subtitle="Traceable wear metrics"
          icon={BarChart3}
        />
      </section>

      {loading && !data ? (
        <div className="panel p-16 text-center text-sm text-muted" role="status">
          <RefreshCw size={24} className="mx-auto mb-3 animate-spin text-accent" />
          Loading engineering analytics…
        </div>
      ) : data?.kpis.total_records === 0 ? (
        <div className="panel p-16 text-center">
          <AlertTriangle size={32} className="mx-auto mb-2 text-warning" />
          <h3 className="m-0 text-base font-semibold text-ink">No experimental records match the current filters</h3>
          <p className="mt-1 text-sm text-muted max-w-md mx-auto">
            Try broadening your material system selection, resetting the date boundaries, or clearing status restrictions.
          </p>
          <button type="button" className="button-secondary mt-4" onClick={resetFilters}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Row 1: Timeline & Status Breakdown */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Timeline */}
            <div className="panel p-5 lg:col-span-2">
              <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
                <div>
                  <h3 className="m-0 text-sm font-semibold text-ink">Experiment Records Over Time</h3>
                  <p className="m-0 text-xs text-muted">Chronological accumulation by month (N={data?.kpis.total_records})</p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="inline-flex items-center gap-1.5 font-medium text-emerald-800">
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" /> Measured
                  </span>
                  <span className="inline-flex items-center gap-1.5 font-medium text-amber-800">
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> Planned
                  </span>
                </div>
              </div>

              {data && data.timeline.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={200}>
                    <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e6" vertical={false} />
                      <XAxis dataKey="period" stroke="#687985" fontSize={11} tickLine={false} />
                      <YAxis stroke="#687985" fontSize={11} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                        formatter={(val: number, name: string) => [`${val} records`, name === "measured" ? "Measured" : "Planned"]}
                        labelFormatter={(label) => `Period: ${label}`}
                      />
                      <Area type="monotone" dataKey="measured" stackId="1" stroke="#187b68" fill="#187b68" fillOpacity={0.7} />
                      <Area type="monotone" dataKey="planned" stackId="1" stroke="#b96618" fill="#b96618" fillOpacity={0.7} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="chart-empty">No chronological observations in scope</div>
              )}
            </div>

            {/* Status Ratio Pie */}
            <div className="panel p-5">
              <div className="border-b border-line pb-3 mb-4">
                <h3 className="m-0 text-sm font-semibold text-ink">State Segregation</h3>
                <p className="m-0 text-xs text-muted">Planned vs measured records (N={data?.kpis.total_records})</p>
              </div>

              {statusPieData.length > 0 ? (
                <div className="flex flex-col items-center">
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={180}>
                      <PieChart>
                        <Pie
                          data={statusPieData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={3}
                        >
                          {statusPieData.map((entry) => (
                            <Cell key={entry.name} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                          formatter={(val: number) => [`${val} records (${((val / (data?.kpis.total_records || 1)) * 100).toFixed(1)}%)`]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-2 flex w-full justify-around border-t border-line pt-3 text-xs">
                    <div className="text-center">
                      <div className="text-muted">Measured</div>
                      <div className="text-base font-bold text-emerald-800">{data?.kpis.measured_records}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-muted">Planned</div>
                      <div className="text-base font-bold text-amber-800">{data?.kpis.planned_records}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="chart-empty">No status data available</div>
              )}
            </div>
          </div>

          {/* Row 2: Material System Distribution */}
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between border-b border-line pb-3 mb-4 gap-2">
              <div>
                <h3 className="m-0 text-sm font-semibold text-ink">Experiment Count by Material System</h3>
                <p className="m-0 text-xs text-muted">Comparative observation volume per recorded material formulation</p>
              </div>
              <span className="text-xs font-mono text-muted">
                {data?.materials.length} material systems identified
              </span>
            </div>

            {data && data.materials.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={200}>
                  <BarChart data={data.materials.slice(0, 10)} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e6" vertical={false} />
                    <XAxis
                      dataKey="material_system"
                      stroke="#687985"
                      fontSize={10}
                      tickLine={false}
                      angle={-20}
                      textAnchor="end"
                      height={40}
                    />
                    <YAxis stroke="#687985" fontSize={11} tickLine={false} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                      formatter={(val: number, name: string) => [`${val} records`, name === "measured_count" ? "Measured" : "Planned"]}
                    />
                    <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "5px" }} />
                    <Bar dataKey="measured_count" name="Measured" fill="#187b68" stackId="a" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="planned_count" name="Planned" fill="#b96618" stackId="a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="chart-empty">No material system records found</div>
            )}
          </div>

          {/* Row 3: Measured Friction (COF) & Wear Distributions */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Friction Distribution */}
            <div className="panel p-5">
              <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
                <div>
                  <h3 className="m-0 text-sm font-semibold text-ink">Measured Friction Coefficient (COF) Distribution</h3>
                  <p className="m-0 text-xs text-muted">
                    Binned frequency of valid experimental values (N={data?.cof_distribution.observation_count})
                  </p>
                </div>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-mono text-ink">
                  Unit: dimensionless
                </span>
              </div>

              {data?.cof_distribution.has_data && data.cof_distribution.stats ? (
                <>
                  <div className="mb-4 grid grid-cols-4 gap-2 rounded-lg bg-slate-50 p-2.5 text-center text-xs">
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Mean</span>
                      <span className="font-semibold text-ink">{data.cof_distribution.stats.mean}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Median</span>
                      <span className="font-semibold text-ink">{data.cof_distribution.stats.median}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Min</span>
                      <span className="font-semibold text-ink">{data.cof_distribution.stats.min}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Max</span>
                      <span className="font-semibold text-ink">{data.cof_distribution.stats.max}</span>
                    </div>
                  </div>

                  <div className="h-56 w-full">
                    <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={180}>
                      <BarChart data={data.cof_distribution.bins} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e6" vertical={false} />
                        <XAxis
                          dataKey="bin_label"
                          stroke="#687985"
                          fontSize={10}
                          tickLine={false}
                          angle={-15}
                          textAnchor="end"
                        />
                        <YAxis stroke="#687985" fontSize={11} tickLine={false} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                          formatter={(val: number) => [`${val} observations`, "Count"]}
                          labelFormatter={(label) => `COF Range: ${label}`}
                        />
                        <Bar dataKey="count" fill="#187b68" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-2 text-[11px] text-muted italic text-center">
                    {data.cof_distribution.note}
                  </div>
                </>
              ) : (
                <div className="chart-empty flex flex-col gap-1 p-8">
                  <span className="font-medium text-ink">No Measured COF Data Available</span>
                  <span className="text-xs text-muted max-w-xs text-center">
                    {data?.cof_distribution.note || "No verified friction measurements recorded for the active filter set."}
                  </span>
                </div>
              )}
            </div>

            {/* Wear Distribution */}
            <div className="panel p-5">
              <div className="flex flex-wrap items-center justify-between border-b border-line pb-3 mb-4 gap-2">
                <div>
                  <h3 className="m-0 text-sm font-semibold text-ink">Measured Wear Distribution</h3>
                  <p className="m-0 text-xs text-muted">
                    Grouped by compatible measurement & unit (Total N={data?.wear_distribution.total_wear_observations})
                  </p>
                </div>
                {data && data.wear_distribution.groups.length > 1 && (
                  <div className="flex items-center gap-1">
                    {data.wear_distribution.groups.map((grp, idx) => (
                      <button
                        key={`${grp.measurement_name}-${grp.unit}`}
                        type="button"
                        className={`rounded px-2 py-0.5 text-[11px] font-medium transition ${
                          selectedWearGroupIndex === idx
                            ? "bg-accent text-white"
                            : "bg-slate-100 text-muted hover:text-ink"
                        }`}
                        onClick={() => setSelectedWearGroupIndex(idx)}
                      >
                        {grp.measurement_name} ({grp.unit})
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {activeWearGroup && activeWearGroup.stats ? (
                <>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">
                      {activeWearGroup.measurement_name} ({activeWearGroup.unit})
                    </span>
                    <span className="text-xs font-mono text-muted">
                      N = {activeWearGroup.observation_count}
                    </span>
                  </div>

                  <div className="mb-4 grid grid-cols-4 gap-2 rounded-lg bg-slate-50 p-2.5 text-center text-xs">
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Mean</span>
                      <span className="font-semibold text-ink">{activeWearGroup.stats.mean}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Median</span>
                      <span className="font-semibold text-ink">{activeWearGroup.stats.median}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Min</span>
                      <span className="font-semibold text-ink">{activeWearGroup.stats.min}</span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px] uppercase">Max</span>
                      <span className="font-semibold text-ink">{activeWearGroup.stats.max}</span>
                    </div>
                  </div>

                  <div className="h-56 w-full">
                    <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={180}>
                      <BarChart data={activeWearGroup.bins} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e6" vertical={false} />
                        <XAxis
                          dataKey="bin_label"
                          stroke="#687985"
                          fontSize={10}
                          tickLine={false}
                          angle={-15}
                          textAnchor="end"
                        />
                        <YAxis stroke="#687985" fontSize={11} tickLine={false} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                          formatter={(val: number) => [`${val} observations`, "Count"]}
                          labelFormatter={(label) => `Range: ${label} ${activeWearGroup.unit}`}
                        />
                        <Bar dataKey="count" fill="#264872" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : (
                <div className="chart-empty flex flex-col gap-1 p-8">
                  <span className="font-medium text-ink">No Compatible Wear Measurements</span>
                  <span className="text-xs text-muted max-w-xs text-center">
                    {data?.wear_distribution.note || "No verified wear observations recorded. Scientific rules forbid combining incompatible wear headings or converting missing units."}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Row 4: COF vs Test Conditions (Relationships) */}
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between border-b border-line pb-3 mb-4 gap-3">
              <div>
                <h3 className="m-0 text-sm font-semibold text-ink">
                  Relationship: Measured Friction vs. Test Conditions
                </h3>
                <p className="m-0 text-xs text-muted">
                  Scatter observations across recorded operating variables (N={data?.cof_relationships.observation_count})
                </p>
              </div>

              {/* Selector for X-Axis Variable */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-muted mr-1">X-Axis Variable:</span>
                {(["load_n", "sliding_velocity_m_per_s", "sliding_distance_m"] as const).map((key) => (
                  <button
                    key={key}
                    type="button"
                    className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                      activeScatterCondition === key
                        ? "bg-accent text-white"
                        : "bg-slate-100 text-muted hover:text-ink"
                    }`}
                    onClick={() => setActiveScatterCondition(key)}
                  >
                    {scatterConditionLabels[key].label} ({scatterConditionLabels[key].unit})
                  </button>
                ))}
              </div>
            </div>

            {data?.cof_relationships.has_sufficient_data && scatterData.length >= 3 ? (
              <>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={220}>
                    <ScatterChart margin={{ top: 15, right: 20, left: -10, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e6" />
                      <XAxis
                        type="number"
                        dataKey="x"
                        name={scatterConditionLabels[activeScatterCondition].label}
                        unit={` ${scatterConditionLabels[activeScatterCondition].unit}`}
                        stroke="#687985"
                        fontSize={11}
                        tickLine={false}
                      />
                      <YAxis
                        type="number"
                        dataKey="y"
                        name="Friction Coefficient"
                        unit=""
                        stroke="#687985"
                        fontSize={11}
                        tickLine={false}
                        domain={["auto", "auto"]}
                      />
                      <ZAxis range={[50, 50]} />
                      <Tooltip
                        cursor={{ strokeDasharray: "3 3" }}
                        contentStyle={{ backgroundColor: "#0c1928", borderColor: "#162e4a", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                        formatter={(val: number, name: string) => [
                          name === "Friction Coefficient" ? val.toFixed(4) : `${val} ${scatterConditionLabels[activeScatterCondition].unit}`,
                          name,
                        ]}
                      />
                      <Scatter
                        name="Experiment Observations"
                        data={scatterData}
                        fill="#187b68"
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-3 rounded-lg border border-line bg-slate-50/60 p-3 text-xs text-muted flex items-start gap-2">
                  <Info size={15} className="text-accent shrink-0 mt-0.5" aria-hidden="true" />
                  <span>
                    <strong>Scientific Notice:</strong> {data.cof_relationships.scientific_disclaimer}
                  </span>
                </div>
              </>
            ) : (
              <div className="chart-empty flex flex-col gap-1 p-10">
                <span className="font-medium text-ink">Insufficient Observations for Reliable Relationship Plot</span>
                <span className="text-xs text-muted max-w-md text-center">
                  At least 3 compatible measured observations with recorded {scatterConditionLabels[activeScatterCondition].label} and COF are required to render this plot honestly without misleading trend extrapolation.
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  highlight,
}: {
  title: string;
  value: number | string;
  subtitle: string;
  icon: React.ComponentType<{ size?: number; className?: string; "aria-hidden"?: boolean | "true" | "false" }>;
  color?: "emerald" | "amber" | "teal";
  highlight?: boolean;
}) {
  const colorStyles = {
    emerald: "text-emerald-800 bg-emerald-50",
    amber: "text-amber-800 bg-amber-50",
    teal: "text-teal-800 bg-teal-50",
  };

  return (
    <div className={`panel p-4 ${highlight ? "border-accent/40 bg-slate-50/30" : ""}`}>
      <div className="flex items-center justify-between">
        <span className="field-label !mb-0">{title}</span>
        <div className={`rounded-lg p-2 ${color ? colorStyles[color] : "bg-slate-100 text-muted"}`}>
          <Icon size={16} aria-hidden="true" />
        </div>
      </div>
      <div className="mt-2 text-2xl font-bold tracking-tight text-ink">{value}</div>
      <p className="mb-0 mt-1 text-xs text-muted">{subtitle}</p>
    </div>
  );
}
