import type { ReactNode } from "react";

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.15em] text-accent">{eyebrow}</p>
        <h1 className="m-0 text-2xl font-semibold tracking-tight text-ink sm:text-[30px]">{title}</h1>
        <p className="mb-0 mt-2 max-w-2xl text-sm leading-relaxed text-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
