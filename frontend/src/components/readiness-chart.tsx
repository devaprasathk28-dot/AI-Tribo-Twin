"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { TargetReadiness } from "@/lib/api";

const COLORS: Record<string, string> = {
  READY: "#187b68",
  BLOCKED: "#d18a3a",
  UNKNOWN: "#8b9aa3",
};

export function ReadinessChart({ targets }: { targets: TargetReadiness[] }) {
  const counts = targets.reduce<Record<string, number>>((result, target) => {
    result[target.status] = (result[target.status] ?? 0) + 1;
    return result;
  }, {});
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }));

  if (!data.length) {
    return <div className="chart-empty">Readiness data is not available.</div>;
  }

  return (
    <div aria-label="Target readiness distribution" className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={56} outerRadius={82} paddingAngle={4}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name] ?? COLORS.UNKNOWN} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => [`${value} targets`, "Count"]} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex justify-center gap-5 text-xs text-muted">
        {data.map((entry) => (
          <span className="flex items-center gap-2" key={entry.name}>
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: COLORS[entry.name] ?? COLORS.UNKNOWN }}
            />
            {entry.name.replaceAll("_", " ")} · {entry.value}
          </span>
        ))}
      </div>
    </div>
  );
}
