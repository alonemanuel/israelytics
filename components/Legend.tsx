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
      <div className="ltitle">{dataset.titleHe}</div>
      <div className="bar" style={{ background: gradient }} />
      <div className="ends">
        <span>{fmt(lo)}</span>
        <span>{fmt((lo + hi) / 2)}</span>
        <span>{fmt(hi)}</span>
      </div>
      <div className="nodata">
        <span className="swatch" style={{ background: NO_DATA_COLOR }} /> אין נתונים
      </div>
    </div>
  );
}
