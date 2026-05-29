# Israelytics — Design

**Date:** 2026-05-29
**Goal:** A generic web platform that visualizes datasets about Israeli cities on a
map of Israel with a timeline slider. The user picks a dataset; the map colors each
city by that dataset's value at the selected time-step. The first dataset is Haredi
(ultra-orthodox) vote share per city across Knesset elections 19–25. New datasets can
be added later by dropping a JSON file and registering it — no code changes.

## Core principle

Separate the **base map** (geometry of Israeli cities — built once, shared by all
datasets) from **datasets** (values per city per time-step). The frontend joins them
by a canonical city key. This separation is what makes the platform generic.

## Decisions (see also docs/DECISIONS.md, which this project maintains)

- **Stack:** Next.js (App Router, TypeScript) deployed on Vercel. Chosen over a
  static/no-build site and over Vite — user preference, one-click deploy, room to grow.
- **Data model:** timeline-always. Every dataset is city × timeline; a single snapshot
  is a timeline of length 1 and the slider hides itself. One code path.
- **Geo / dataset split:** shared `geo.json` (geometry only) + per-dataset value files,
  joined by canonical city key.
- **Join key:** normalized Hebrew city name (e.g. `"בני ברק"`), human-readable.
  Numeric `סמל ישוב` considered but rejected for now (datasets would all have to carry it).
- **Color scale:** each dataset declares a generic `colorScale` block (sequential or
  diverging, a d3 scheme name, domain, optional power/midpoint) so new datasets render
  without new code.
- **Dot size:** a dataset-independent `weight` (≈ city electorate size) lives in
  `geo.json`.
- **Haredi parties:** `{שס, ג}` (Shas + UTJ), configurable in the builder.
- **Projection:** planar `d3.geoIdentity` with longitude×cos(lat) aspect correction —
  deliberately NOT a spherical projection, because the source polygons have inconsistent
  ring winding that makes spherical projections (Mercator) render inside-out.

## Architecture

Two layers: an offline **Python pipeline** that emits standard JSON, and a **Next.js
frontend** that renders it. The frontend never parses raw data; the pipeline never
knows about rendering.

### Data formats

**`public/data/geo.json`** — shared base map, keyed by canonical city key:
```jsonc
{ "cities": {
  "בני ברק":   { "nameHe":"בני ברק", "kind":"polygon", "geometry":{...GeoJSON...}, "weight":95000 },
  "כפר ורדים": { "nameHe":"כפר ורדים", "kind":"point", "lat":32.9, "lon":35.2, "weight":4200 }
}}
```

**`public/data/datasets/<id>.json`** — one dataset:
```jsonc
{
  "id": "haredi-vote",
  "title": "Haredi vote share", "titleHe": "שיעור ההצבעה החרדית",
  "descriptionHe": "ש\"ס + יהדות התורה מתוך כלל הקולות הכשרים",
  "unit": "percent",
  "colorScale": { "type":"sequential", "scheme":"Purples", "domain":[0,1], "power":0.55 },
  "timesteps": [ {"id":19,"label":"בחירות 19","sub":"Jan 2013"}, /* ... */ ],
  "cities": { "בני ברק": [0.85,0.83,0.88,0.89,0.90,0.88,0.90] /* aligned to timesteps; null=no data */ }
}
```

**`public/data/datasets/index.json`** — registry for the picker:
`[ {"id":"haredi-vote","titleHe":"...","description":"..."} ]`.

### Pipeline (Python)
```
pipeline/
  common/
    normalize.py     name canonicalization (BOM, parens, שבט, geresh/gershayim, hyphens)
    geo_index.py     loads polygons+coords, exposes resolve(name) -> (canonical_key, kind)
                     — SINGLE SOURCE OF TRUTH for the join key, used by every builder
  build_geo.py       polygons + coords -> public/data/geo.json (+ weight, variant merge,
                     ring rewinding, foreign-mis-geocode bbox filter)
  build_haredi.py    election CSVs -> datasets/haredi-vote.json; registers in index.json;
                     writes coverage_report.txt
  sources/           raw inputs (election CSVs, polygon repo, coords) — large ones gitignored
  tests/             pytest: normalize, resolve, haredi math, variant merge
```
Both builders call `geo_index.resolve`, so dataset city keys always line up with geo
keys. Cities a dataset can't resolve are reported, never silently dropped.

### Frontend (Next.js App Router, TypeScript)
```
app/page.tsx                 client view composing picker + map + timeline
components/
  DatasetPicker.tsx          dropdown populated from datasets/index.json
  MapView.tsx                D3 SVG: polygons + dots, zoom/pan. D3 owns the SVG via a
                             useRef; React owns the surrounding controls.
  Timeline.tsx               range slider; hidden when a dataset has one time-step
  Legend.tsx                 renders from the dataset's colorScale block
lib/
  types.ts                   Dataset, GeoData, ColorSpec, City
  colorScale.ts              builds a d3 color function from a ColorSpec (unit-tested)
  useData.ts                 fetches geo.json once + the selected dataset
```
Rendering = join `dataset.cities[key]` onto `geo.cities[key]` at the current timestep,
color via `colorScale(dataset.colorScale)`. Zoom/pan and the planar projection are
ported from the existing israel-election-map.

### Documentation (maintained deliverables)

- **`README.md`** — newcomer-facing: what Israelytics is, how to run locally
  (`npm run dev`), how to rebuild data (`python pipeline/build_*.py`), and how to add a
  new dataset (write a builder that emits the dataset JSON + registers it).
- **`CLAUDE.md`** — agent/maintainer-facing: architecture summary, the data-format
  contract, the geo/dataset split, conventions, and an explicit rule:
  *"When you make a decision with a non-obvious rationale, append it to
  `docs/DECISIONS.md`."* Points readers to README for usage and DECISIONS for history.
- **`docs/DECISIONS.md`** — append-only decision log (lightweight ADR). Each entry:
  date, decision, rationale, and alternatives rejected. Seeded with the Decisions list
  above (Next.js+Vercel, timeline-always, geo/dataset split, name join key, generic
  color scale, weight in geo, Haredi={שס,ג}, planar projection, mis-geocode bbox filter).

## Data flow

1. Pipeline builds `geo.json` + `datasets/*.json` + `index.json` into `public/data/`.
2. Frontend loads `index.json` → fills the picker.
3. User picks a dataset → frontend fetches `geo.json` (cached) + `datasets/<id>.json`.
4. Map joins values onto geometry at the slider's timestep; legend reads colorScale.
5. Moving the slider recolors; zoom/pan/tooltips work as today.

## Error handling

- Pipeline: missing/renamed CSV columns fail loudly; unresolved cities reported in
  `coverage_report.txt` with vote counts; never silently dropped.
- Frontend: a dataset city key absent from geo is skipped (and counted in a console
  summary); a `null` value renders as the "no data" color.

## Testing

- Python (pytest): `normalize`, `geo_index.resolve`, `haredi_share`, `merge_shares` —
  port and extend the existing 35 tests.
- Frontend: `colorScale.ts` unit-tested (sequential, diverging, power, domain clamping);
  the map verified by a headless Playwright screenshot across two timesteps, as before.

## Deployment

Next app auto-deploys to Vercel on `git push`. `geo.json` (~3 MB) is served from
`/public` and fetched client-side — acceptable for a POC. If load feels heavy later,
switch to TopoJSON + geometry simplification (recorded as a future option in DECISIONS).

## Out of scope (YAGNI)

- More than one dataset at launch (Haredi only; the format proves extensibility).
- Auth, uploads, a dataset-authoring UI, a backend/database.
- Comparing two datasets side by side, or non-map chart types.
- Server-side rendering of the map (it's a client component).

## Open risks

- **3 MB geo payload** — fine now, may want simplification later.
- **Join-key coverage** — same normalization risk as before; quantified by the coverage
  report. A manual alias table (carried over) handles the big misses.
- **D3-in-React lifecycle** — zoom/pan state must survive re-renders; MapView keeps the
  D3 selection in refs and only re-colors on dataset/timestep change.
