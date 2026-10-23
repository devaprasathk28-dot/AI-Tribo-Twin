"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Beaker,
  BrainCircuit,
  ChevronRight,
  Database,
  FileText,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  ListChecks,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type NavItem = {
  href: string;
  label: string;
  badge?: string;
  icon: React.ComponentType<{ size?: number; className?: string; "aria-hidden"?: boolean | "true" | "false" }>;
  description: string;
};

export const navItems: NavItem[] = [
  {
    href: "/",
    label: "Overview",
    icon: LayoutDashboard,
    description: "System health, models and quick actions",
  },
  {
    href: "/models",
    label: "Models & Prediction",
    badge: "1 Active",
    icon: BrainCircuit,
    description: "Tow-on-tool friction predictions & benchmarks",
  },
  {
    href: "/experiments",
    label: "Experiment Records",
    icon: Beaker,
    description: "Measured observations and verified records",
  },
  {
    href: "/analytics",
    label: "Analytics & Visuals",
    icon: BarChart3,
    description: "Distributions, correlations & registry metrics",
  },
  {
    href: "/planning",
    label: "Experiment Planning",
    icon: ListChecks,
    description: "Proposed conditions and test designs",
  },
  {
    href: "/imports",
    label: "Data Intake",
    icon: Database,
    description: "CSV validation and SHA-256 intake",
  },
  {
    href: "/reports",
    label: "Reports & Export",
    icon: FileText,
    description: "PDF engineering reports and CSV data export",
  },
];

const routeBreadcrumbs: Record<string, { category: string; page: string }> = {
  "/": { category: "Research Workspace", page: "Overview Dashboard" },
  "/models": { category: "Research Workspace", page: "ML Models & COF Prediction" },
  "/experiments": { category: "Research Workspace", page: "Experimental Records" },
  "/analytics": { category: "Research Workspace", page: "Engineering Analytics & Visualizations" },
  "/planning": { category: "Research Workspace", page: "Experiment Design & Planning" },
  "/imports": { category: "Research Workspace", page: "Data Intake & Validation" },
  "/reports": { category: "Research Workspace", page: "Engineering Reports & Export" },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [serviceState, setServiceState] = useState<"checking" | "online" | "offline">("checking");
  const [dbState, setDbState] = useState<string>("checking");
  const [isRefreshingHealth, setIsRefreshingHealth] = useState(false);

  const checkHealth = useCallback(() => {
    setIsRefreshingHealth(true);
    api.health()
      .then((res) => {
        setServiceState(res.status === "ok" ? "online" : "offline");
        setDbState(res.database ?? "ok");
      })
      .catch(() => {
        setServiceState("offline");
        setDbState("unavailable");
      })
      .finally(() => {
        setIsRefreshingHealth(false);
      });
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Close mobile drawer on route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Handle Escape key to close mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen]);

  const breadcrumb = routeBreadcrumbs[pathname] ?? {
    category: "Research Workspace",
    page: "Tribology System",
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      {/* Mobile top header bar */}
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-line bg-navy-900 px-4 text-white md:hidden">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white">
            <Gauge size={18} aria-hidden="true" />
          </div>
          <div>
            <span className="font-semibold tracking-tight text-white">AI-TriboTwin</span>
            <span className="ml-2 rounded bg-navy-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-slate-300">
              Platform
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div
            aria-label={`API status: ${serviceState}`}
            className="flex items-center gap-1.5 rounded-full bg-navy-800 px-2 py-0.5 text-xs text-slate-300"
          >
            <span
              className={`h-2 w-2 rounded-full ${
                serviceState === "online"
                  ? "bg-emerald-400"
                  : serviceState === "offline"
                    ? "bg-rose-400"
                    : "bg-amber-400"
              }`}
            />
            <span className="capitalize">{serviceState}</span>
          </div>
          <button
            aria-expanded={mobileOpen}
            aria-label={mobileOpen ? "Close menu" : "Open navigation menu"}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-navy-750 bg-navy-850 text-slate-200 transition hover:bg-navy-800 hover:text-white"
            onClick={() => setMobileOpen((open) => !open)}
            type="button"
          >
            {mobileOpen ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
          </button>
        </div>
      </header>

      {/* Mobile navigation drawer backdrop & panel */}
      {mobileOpen && (
        <div
          aria-hidden="true"
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div
        aria-label="Mobile navigation drawer"
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-navy-800 bg-navy-900 text-white transition-transform duration-200 ease-in-out md:hidden ${
          mobileOpen ? "translate-x-0 shadow-drawer" : "-translate-x-full"
        }`}
        role="dialog"
      >
        <div className="flex h-16 items-center justify-between border-b border-navy-800 px-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-white shadow-sm">
              <Gauge size={19} aria-hidden="true" />
            </div>
            <div>
              <div className="font-semibold leading-none tracking-tight">AI-TriboTwin</div>
              <div className="mt-1 text-[11px] text-slate-400">Tribological Research</div>
            </div>
          </div>
          <button
            aria-label="Close navigation"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-navy-800 hover:text-white"
            onClick={() => setMobileOpen(false)}
            type="button"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="Mobile main navigation" className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navItems.map(({ href, label, icon: Icon, badge }) => {
            const selected = pathname === href;
            return (
              <Link
                aria-current={selected ? "page" : undefined}
                className={`flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  selected
                    ? "border-l-2 border-emerald-400 bg-navy-800 text-white shadow-sm"
                    : "text-slate-300 hover:bg-navy-850 hover:text-white"
                }`}
                href={href}
                key={href}
                onClick={() => setMobileOpen(false)}
              >
                <div className="flex items-center gap-3">
                  <Icon aria-hidden="true" size={18} />
                  <span>{label}</span>
                </div>
                {badge && (
                  <span className="rounded bg-navy-750 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Mobile drawer safeguards */}
        <div className="border-t border-navy-800 p-4">
          <div className="rounded-lg border border-navy-750 bg-navy-850 p-3 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
              <ShieldCheck size={14} aria-hidden="true" />
              Scientific Safeguards
            </div>
            <p className="mb-0 mt-1.5 text-[11px] leading-relaxed text-slate-400">
              Composite targets remain strictly blocked awaiting primary evidence.
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  serviceState === "online" ? "bg-emerald-400" : "bg-rose-400"
                }`}
              />
              <span>FastAPI & DB: {serviceState}</span>
            </div>
            <button
              aria-label="Refresh API health"
              className="text-slate-400 hover:text-white"
              onClick={checkHealth}
              type="button"
            >
              <RefreshCw size={13} className={isRefreshingHealth ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
      </div>

      {/* Desktop + Mobile Responsive Shell */}
      <div
        className={`md:grid ${
          isCollapsed ? "md:grid-cols-[74px_minmax(0,1fr)]" : "md:grid-cols-[260px_minmax(0,1fr)]"
        } transition-all duration-200 min-h-screen`}
      >
        {/* Desktop Sidebar (hidden on mobile, visible on md and up) */}
        <aside
          aria-label="Application sidebar"
          className="hidden md:sticky md:top-0 md:flex md:h-screen md:flex-col md:justify-between border-r border-navy-800 bg-navy-900 text-white"
        >
          <div>
            {/* Logo / Header */}
            <div className="flex h-16 items-center justify-between border-b border-navy-800 px-4">
              <Link
                className="flex items-center gap-3 overflow-hidden text-white transition hover:opacity-90"
                href="/"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-white shadow-sm">
                  <Gauge size={20} aria-hidden="true" />
                </div>
                {!isCollapsed && (
                  <div className="min-w-0">
                    <div className="truncate font-semibold tracking-tight text-white">AI-TriboTwin</div>
                    <div className="truncate text-[11px] text-slate-400">Tribological Research</div>
                  </div>
                )}
              </Link>
              <button
                aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-navy-800 hover:text-white"
                onClick={() => setIsCollapsed((prev) => !prev)}
                title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                type="button"
              >
                {isCollapsed ? (
                  <PanelLeftOpen size={17} aria-hidden="true" />
                ) : (
                  <PanelLeftClose size={17} aria-hidden="true" />
                )}
              </button>
            </div>

            {/* Navigation items */}
            <nav aria-label="Main desktop navigation" className="space-y-1 p-3">
              {navItems.map(({ href, label, icon: Icon, badge }) => {
                const selected = pathname === href;
                return (
                  <Link
                    aria-current={selected ? "page" : undefined}
                    className={`group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                      selected
                        ? "border-l-2 border-emerald-400 bg-navy-800 text-white shadow-sm"
                        : "text-slate-300 hover:bg-navy-850 hover:text-white"
                    } ${isCollapsed ? "justify-center px-0" : ""}`}
                    href={href}
                    key={href}
                    title={isCollapsed ? label : undefined}
                  >
                    <Icon aria-hidden="true" className="shrink-0" size={18} />
                    {!isCollapsed && (
                      <div className="flex flex-1 items-center justify-between overflow-hidden">
                        <span className="truncate">{label}</span>
                        {badge && (
                          <span className="rounded bg-navy-750 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                            {badge}
                          </span>
                        )}
                      </div>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer */}
          <div className="border-t border-navy-800 p-3">
            {!isCollapsed ? (
              <>
                <div className="mb-3 rounded-xl border border-navy-750 bg-navy-850 p-3 text-xs">
                  <div className="flex items-center gap-2 font-semibold text-emerald-400">
                    <ShieldCheck size={15} aria-hidden="true" />
                    <span>Scientific Safeguards</span>
                  </div>
                  <p className="mb-0 mt-1.5 text-[11px] leading-relaxed text-slate-400">
                    Composite prediction gated per Sprint 9 evidence recovery protocol.
                  </p>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-navy-950 px-3 py-2 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <Activity size={14} aria-hidden="true" />
                    <span>Backend</span>
                    <span
                      aria-label={`API status ${serviceState}`}
                      className={`h-2 w-2 rounded-full ${
                        serviceState === "online"
                          ? "bg-emerald-400"
                          : serviceState === "offline"
                            ? "bg-rose-500"
                            : "bg-amber-400"
                      }`}
                    />
                    <span className="capitalize text-slate-400">{serviceState}</span>
                  </div>
                  <button
                    aria-label="Refresh API health status"
                    className="text-slate-400 transition hover:text-white"
                    onClick={checkHealth}
                    title="Refresh health check"
                    type="button"
                  >
                    <RefreshCw size={12} className={isRefreshingHealth ? "animate-spin" : ""} />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center gap-2 py-1">
                <div
                  aria-label={`API status: ${serviceState}`}
                  className={`h-2.5 w-2.5 rounded-full ${
                    serviceState === "online" ? "bg-emerald-400" : "bg-rose-500"
                  }`}
                  title={`API status: ${serviceState}`}
                />
              </div>
            )}
          </div>
        </aside>

        {/* Right content column */}
        <div className="min-w-0 flex-1">
          {/* Top contextual header bar (desktop only) */}
          <header className="sticky top-0 z-30 hidden h-16 items-center justify-between border-b border-line bg-white/95 px-6 backdrop-blur md:flex md:px-8">
            <div className="flex items-center gap-2 text-xs text-muted">
              <span className="font-medium text-slate-500">{breadcrumb.category}</span>
              <ChevronRight size={14} className="text-slate-400" aria-hidden="true" />
              <span className="font-semibold text-ink">{breadcrumb.page}</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 sm:flex">
                <FlaskConical size={13} className="text-accent" aria-hidden="true" />
                <span>Cambridge Tow Model Active</span>
                <span className="text-slate-300">|</span>
                <span className="font-medium text-amber-700">Composite Gated</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted">
                <span
                  aria-label={`API status ${serviceState}`}
                  className={`h-2 w-2 rounded-full ${
                    serviceState === "online"
                      ? "bg-emerald-500"
                      : serviceState === "offline"
                        ? "bg-rose-500"
                        : "bg-amber-500"
                  }`}
                />
                <span className="hidden capitalize font-medium sm:inline">{serviceState}</span>
                {dbState !== "ok" && dbState !== "checking" && (
                  <span className="text-[11px] text-amber-600">(DB: {dbState})</span>
                )}
              </div>
            </div>
          </header>

          {/* Main workspace container (single instance) */}
          <main className="mx-auto w-full max-w-[1440px] px-4 py-6 md:px-8 md:py-8">{children}</main>
        </div>
      </div>
    </div>
  );
}

