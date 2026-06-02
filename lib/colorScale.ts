import * as d3 from "d3";
import type { ColorSpec } from "./types";

// Theme token (resolved by the SVG/CSS at render time) so "no data" cells follow
// light/dark instead of being a fixed blue-gray. Works as an SVG fill and in CSS.
export const NO_DATA_COLOR = "var(--map-empty)";

// Earth diverging scheme: earth-purple (t=0) -> warm neutral -> earth-orange
// (t=1). The site's UI is monochrome, so the data palette carries all the color;
// these two earthy poles are the project's signature divergence. Orientation
// (purple low / orange high) is fixed here so a dataset just names the scheme.
const earthDiv = d3.interpolateRgbBasis([
  "#4a2a73", // earth purple (strong)
  "#7d6aa3",
  "#efe9df", // warm neutral midpoint
  "#dd9a55",
  "#b8470c", // earth orange (strong)
]);

// d3 scheme name -> interpolator. Extend as new datasets need new schemes.
const INTERPOLATORS: Record<string, (t: number) => string> = {
  Purples: d3.interpolatePurples,
  Blues: d3.interpolateBlues,
  Greens: d3.interpolateGreens,
  Reds: d3.interpolateReds,
  Oranges: d3.interpolateOranges,
  Viridis: d3.interpolateViridis,
  RdBu: d3.interpolateRdBu,
  RdYlBu: d3.interpolateRdYlBu,
  BrBG: d3.interpolateBrBG,
  EarthDiv: earthDiv,
};

/**
 * Build a value -> CSS color function from a dataset's ColorSpec.
 * - sequential: maps [domain] -> [0,1], optional `power` boosts low-end contrast,
 *   reads the scheme low->high.
 * - diverging: maps around `midpoint` (default domain center) so the scheme's
 *   endpoints sit at the domain extremes.
 */
export function makeColor(spec: ColorSpec): (v: number | null | undefined) => string {
  const interp = INTERPOLATORS[spec.scheme] ?? d3.interpolatePurples;
  const [lo, hi] = spec.domain;
  const span = hi - lo || 1;

  if (spec.type === "diverging") {
    const mid = spec.midpoint ?? (lo + hi) / 2;
    return (v) => {
      if (v == null || Number.isNaN(v)) return NO_DATA_COLOR;
      const half = Math.max(hi - mid, mid - lo) || 1;
      const t = 0.5 + (v - mid) / (2 * half); // mid -> 0.5, extremes -> 0/1
      return interp(clamp01(t));
    };
  }

  const power = spec.power ?? 1;
  return (v) => {
    if (v == null || Number.isNaN(v)) return NO_DATA_COLOR;
    const norm = clamp01((v - lo) / span);
    const t = Math.pow(norm, power);
    return interp(0.08 + 0.92 * t); // keep 0 faintly visible, 1 darkest
  };
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}
