"use client";

import { useEffect, useState } from "react";
import type { BorderGeometry, Dataset, DatasetSummary, GeoData } from "./types";

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`failed to load ${url}: ${res.status}`);
  return res.json();
}

/** Loads the shared base map once and the dataset registry, then the selected
 * dataset whenever it changes. */
export function useData(selectedId: string | null) {
  const [geo, setGeo] = useState<GeoData | null>(null);
  const [border, setBorder] = useState<BorderGeometry | null>(null);
  const [index, setIndex] = useState<DatasetSummary[]>([]);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<GeoData>("/data/geo.json").then(setGeo).catch((e) => setError(String(e)));
    // border is decorative — if it fails to load the map still works, so don't error
    getJSON<BorderGeometry>("/data/border.json").then(setBorder).catch(() => {});
    getJSON<DatasetSummary[]>("/data/datasets/index.json")
      .then(setIndex)
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setDataset(null);
    getJSON<Dataset>(`/data/datasets/${selectedId}.json`)
      .then(setDataset)
      .catch((e) => setError(String(e)));
  }, [selectedId]);

  return { geo, border, index, dataset, error };
}
