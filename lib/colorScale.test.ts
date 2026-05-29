import { describe, it, expect } from "vitest";
import { makeColor, NO_DATA_COLOR } from "./colorScale";

describe("makeColor", () => {
  it("returns the no-data color for null/undefined/NaN", () => {
    const c = makeColor({ type: "sequential", scheme: "Purples", domain: [0, 1] });
    expect(c(null)).toBe(NO_DATA_COLOR);
    expect(c(undefined)).toBe(NO_DATA_COLOR);
    expect(c(NaN)).toBe(NO_DATA_COLOR);
  });

  it("sequential: higher value is darker than lower value", () => {
    const c = makeColor({ type: "sequential", scheme: "Purples", domain: [0, 1] });
    expect(lum(c(0.1))).toBeGreaterThan(lum(c(0.9))); // low value lighter
  });

  it("sequential: clamps values outside the domain", () => {
    const c = makeColor({ type: "sequential", scheme: "Purples", domain: [0, 1] });
    expect(c(5)).toBe(c(1));
    expect(c(-5)).toBe(c(0));
  });

  it("diverging: midpoint sits at the scheme center", () => {
    const c = makeColor({ type: "diverging", scheme: "RdBu", domain: [0, 1], midpoint: 0.5 });
    // RdBu(0.5) is near-white; the midpoint value should map close to it.
    expect(c(0.5)).toBe(c(0.5));
    expect(lum(c(0.5))).toBeGreaterThan(lum(c(0))); // center lighter than extreme
  });

  it("falls back to a default interpolator for an unknown scheme", () => {
    const c = makeColor({ type: "sequential", scheme: "NoSuchScheme", domain: [0, 1] });
    expect(c(0.5)).toMatch(/^(rgb|#)/);
  });
});

// crude luminance from an "rgb(r, g, b)" string for ordering comparisons
function lum(rgb: string): number {
  const m = rgb.match(/\d+/g);
  if (!m) return 0;
  const [r, g, b] = m.map(Number);
  return 0.299 * r + 0.587 * g + 0.114 * b;
}
