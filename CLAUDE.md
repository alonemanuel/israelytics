# CLAUDE.md — Israelytics

Guidance for Claude (and any maintainer) working in this repo.

## What this is

Israelytics is a generic platform for visualizing data about Israeli cities on a map of
Israel with a timeline. The user selects a dataset; the map colors each city by that
dataset's value at the selected time-step; a slider moves through time.

The defining idea: **separate the base map from the data.**
- The **base map** (`public/data/geo.json`) is the geometry of Israeli cities — built
  once, shared by every dataset.
- Each **dataset** (`public/data/datasets/<id>.json`) is values per city per time-step,
  plus its own color spec.
- The frontend **joins them by CBS locality code** (סמל יישוב — a stable numeric
  identifier from the Israeli Central Bureau of Statistics).

This is what makes the platform extensible: a new dataset is a new JSON file, not new code.

## Maintain the docs

This repo keeps three docs in sync with reality. **When you change the project, update them:**

- **`README.md`** — what Israelytics is + how to run it + how to add a dataset (for newcomers).
- **`CLAUDE.md`** (this file) — architecture, the data-format contract, conventions.
- **`docs/DECISIONS.md`** — an append-only decision log.
  **When you make a decision with a non-obvious rationale, append an entry to
  `docs/DECISIONS.md`** (what was decided, why, and what was rejected). Don't bury such
  rationale only in code or commit messages. The stack choice (Next.js on Vercel), the
  timeline-always data model, and the name-based join key all live there — that's the
  bar for what belongs in that file.

## Architecture

```
pipeline/            Python: raw sources -> standard JSON (never knows about rendering)
  common/normalize.py    canonical city-name normalization
  common/geo_index.py    resolve(name) -> (canonical_key, kind) + CBS code mapping
  build_geo.py           polygons + coords -> public/data/geo.json
  build_haredi.py        election CSVs   -> public/data/datasets/haredi-vote.json
app/                 Next.js App Router (TypeScript)
  page.tsx               client view: picker + map + timeline
components/          DatasetPicker, MapView (D3 SVG + zoom/pan), Timeline, Legend
lib/                 types.ts, colorScale.ts, useData.ts
public/data/         geo.json, datasets/<id>.json, datasets/index.json
```

The pipeline produces data; the frontend is a pure view. Keep that boundary.

## Data-format contract

**`geo.json`** — keyed by CBS locality code:
```jsonc
{ "cities": {
  "3000": { "nameHe":"בני ברק", "kind":"polygon", "geometry":{...GeoJSON...}, "weight":95000 },
  "1295": { "nameHe":"כפר ורדים", "kind":"point", "lat":32.9, "lon":35.2, "weight":4200 }
}}
```
`weight` ≈ city electorate size; drives dot radius and is dataset-independent.

**`datasets/<id>.json`**:
```jsonc
{
  "id": "haredi-vote",
  "title": "Haredi vote share", "titleHe": "שיעור ההצבעה החרדית",
  "descriptionHe": "...",
  "unit": "percent",
  "colorScale": { "type":"sequential", "scheme":"Purples", "domain":[0,1], "power":0.55 },
  "timesteps": [ {"id":"k19","label":"הכנסת ה-19","sub":"Jan 2013"} /* ... */ ],
  "cities": { "3000": {"k19":0.85, "k20":0.83} }
}
```
Each dataset defines its own timeline. Timestep IDs are dataset-specific strings —
election-based datasets use `"k19"`, `"k20"`, etc.; year-based datasets use `"2020"`,
`"2021"`, etc. City values are objects keyed by timestep ID (missing key = no data).

`colorScale` is generic (`sequential`|`diverging`, a d3 scheme, domain, optional
`power`/`midpoint`) so new datasets render without frontend changes.

**`datasets/index.json`** — registry for the picker: `[{id, titleHe, description}]`.

## Conventions

- **Join key** = CBS locality code (סמל יישוב). Builders resolve raw names through
  `common/geo_index.resolve` for geometry, then call `cbs_code_for()` to get the
  stable numeric code used as the key in both `geo.json` and dataset files.
  CBS codes are registered via `elections.register_cbs_codes(geo, sources_dir)`.
- **Projection** is planar `d3.geoIdentity` with longitude×cos(lat) correction — NOT a
  spherical projection. The source polygons have inconsistent ring winding that renders
  inside-out under Mercator. See DECISIONS.
- **Never silently drop data.** Cities a dataset can't resolve go into a coverage report.
- **Tests:** Python logic (normalize, resolve, value math, merge) is unit-tested with
  pytest; `lib/colorScale.ts` is unit-tested; the map is verified by headless screenshot.

## Safety / workflow

- Don't `git push` or deploy without explicit go-ahead.
- Raw source files under `pipeline/sources/` may be large; keep them gitignored.
