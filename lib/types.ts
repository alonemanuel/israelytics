// Data-format contract shared between the Python pipeline and the frontend.
// See CLAUDE.md for the authoritative description.

export type Geometry =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] };

export interface PolygonCity {
  nameHe: string;
  kind: "polygon";
  geometry: Geometry;
  weight: number;
}
export interface PointCity {
  nameHe: string;
  kind: "point";
  lat: number;
  lon: number;
  weight: number;
}
export type City = PolygonCity | PointCity;

export interface GeoData {
  cities: Record<string, City>;
}

// National outline (public/data/border.json) — a single dissolved landmass that
// contains every city, built by pipeline/basemap/build_border.py.
export type BorderGeometry = Geometry;

export interface ColorSpec {
  type: "sequential" | "diverging";
  scheme: string; // d3 scheme name, e.g. "Purples", "RdBu"
  domain: [number, number];
  power?: number; // <1 boosts low-end contrast (sequential)
  midpoint?: number; // diverging center (default mean of domain)
}

export interface Timestep {
  id: string;
  label: string;
  sub?: string;
}

// One component of a city's value breakdown (e.g. a party's vote share).
// Generic: `tag` is an optional category marker a dataset can use to group/
// color parts (right-left uses "R"/"L"); the frontend treats it as opaque.
export interface Part {
  labelHe: string;
  value: number;
  tag?: string;
}

// A city's value at one timestep. Either a bare number, or an object carrying
// the same scalar in `v` plus an optional breakdown in `parts`. `cellValue`
// normalizes the two forms; `cellParts` pulls the breakdown when present.
export type Cell = number | { v: number; parts?: Part[] };

export function cellValue(cell: Cell | null | undefined): number | null {
  if (cell == null) return null;
  return typeof cell === "number" ? cell : cell.v;
}

export function cellParts(cell: Cell | null | undefined): Part[] | null {
  if (cell == null || typeof cell === "number") return null;
  return cell.parts ?? null;
}

export interface Dataset {
  id: string;
  title: string;
  titleHe: string;
  description?: string;
  descriptionHe?: string;
  info?: string; // longer reader-facing methodology (markdown-lite)
  infoHe?: string;
  unit: string;
  colorScale: ColorSpec;
  timesteps: Timestep[];
  cities: Record<string, Record<string, Cell>>; // CBS code -> {timestep_id -> cell}
}

export interface DatasetSummary {
  id: string;
  title: string;
  titleHe: string;
  descriptionHe?: string;
}
