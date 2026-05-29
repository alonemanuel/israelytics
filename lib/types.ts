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

export interface Dataset {
  id: string;
  title: string;
  titleHe: string;
  description?: string;
  descriptionHe?: string;
  unit: string;
  colorScale: ColorSpec;
  timesteps: Timestep[];
  cities: Record<string, Record<string, number>>; // CBS code -> {timestep_id -> value}
}

export interface DatasetSummary {
  id: string;
  title: string;
  titleHe: string;
  descriptionHe?: string;
}
