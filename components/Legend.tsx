"use client";

import { useMemo } from "react";
import type { Dataset } from "@/lib/types";
import { makeColor, NO_DATA_COLOR } from "@/lib/colorScale";

export default function Legend({ dataset }: { dataset: Dataset }) {
  const { gradient, lo, hi } = useMemo(() => {
    const color = makeColor(dataset.colorScale);
    const [a, b] = dataset.colorScale.domain;
    const stops = Array.from({ length: 9 }, (_, i) => {
      const t = i / 8;
      return `${color(a + t * (b - a))} ${t * 100}%`;
    });
    return { gradient: `linear-gradient(to right, ${stops.join(",")})`, lo: a, hi: b };
  }, [dataset]);

  const fmt = (v: number) =>
    dataset.unit === "percent" ? `${Math.round(v * 100)}%` : `${v}`;

  return (
    <div className="legend">
      <span className="kicker">מקרא</span>
      <div className="legend-bar" style={{ background: gradient }} />
      <div className="legend-ends">
        <span className="mono">{fmt(lo)}</span>
        <span className="mono">{fmt((lo + hi) / 2)}</span>
        <span className="mono">{fmt(hi)}</span>
      </div>
      <div className="legend-nodata">
        <span className="swatch" style={{ background: NO_DATA_COLOR }} /> אין נתונים
      </div>
    </div>
  );
}
