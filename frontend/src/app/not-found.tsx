import Link from "next/link";
import { ArrowLeft, FileQuestion, LayoutDashboard } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-500 shadow-sm border border-line">
        <FileQuestion size={32} aria-hidden="true" />
      </div>
      <h1 className="m-0 mt-4 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
        Page Not Found
      </h1>
      <p className="mb-0 mt-2 max-w-md text-sm leading-relaxed text-muted">
        The requested scientific module or experimental route does not exist or may have been relocated.
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Link className="button-primary" href="/">
          <LayoutDashboard size={16} aria-hidden="true" />
          <span>Return to Dashboard</span>
        </Link>
        <Link className="button-secondary" href="/models">
          <ArrowLeft size={16} aria-hidden="true" />
          <span>Friction Models</span>
        </Link>
      </div>

      <div className="mt-8 rounded-lg border border-line bg-white px-4 py-3 text-xs text-muted">
        <span>Available routes: </span>
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-ink">/</code> ·{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-ink">/models</code> ·{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-ink">/experiments</code> ·{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-ink">/planning</code> ·{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-ink">/imports</code>
      </div>
    </div>
  );
}
