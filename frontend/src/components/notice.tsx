import { AlertTriangle, CheckCircle2, CircleAlert, Info } from "lucide-react";

const styles = {
  error: "border-rose-200 bg-rose-50 text-rose-900",
  warning: "border-amber-200 bg-amber-50 text-amber-950",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  info: "border-sky-200 bg-sky-50 text-sky-950",
};

const icons = {
  error: CircleAlert,
  warning: AlertTriangle,
  success: CheckCircle2,
  info: Info,
};

export function Notice({
  tone,
  title,
  children,
}: {
  tone: keyof typeof styles;
  title: string;
  children: React.ReactNode;
}) {
  const Icon = icons[tone];
  return (
    <div className={`flex gap-3 rounded-lg border p-4 ${styles[tone]}`} role={tone === "error" ? "alert" : "status"}>
      <Icon className="mt-0.5 shrink-0" size={17} aria-hidden="true" />
      <div>
        <div className="text-sm font-semibold">{title}</div>
        <div className="mt-1 text-sm leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
