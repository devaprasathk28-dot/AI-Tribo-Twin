type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toUpperCase();
  const variant =
    normalized === "READY"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : normalized === "BLOCKED"
        ? "border-amber-200 bg-amber-50 text-amber-800"
        : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide ${variant}`}
    >
      {normalized.replaceAll("_", " ")}
    </span>
  );
}
