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

This repo keeps four docs in sync with reality. **When you change the project, update them:**

- **`README.md`** — what Israelytics is + how to run it + how to add a dataset (for newcomers).
- **`CLAUDE.md`** (this file) — architecture, the data-format contract, conventions.
- **`docs/DESIGN.md`** — design system: typefaces, type scale, colour tokens, glass surface, spacing.
  **When you change the visual design** (fonts, colours, layout, new UI components), update this file.
  It is the source of truth for any frontend styling decision.
- **`docs/DECISIONS.md`** — an append-only decision log.
  **When you make a decision with a non-obvious rationale, append an entry to
  `docs/DECISIONS.md`** (what was decided, why, and what was rejected). Don't bury such
  rationale only in code or commit messages. The stack choice (Next.js on Vercel), the
  timeline-always data model, and the name-based join key all live there — that's the
  bar for what belongs in that file.

## Architecture

```
pipeline/            Python: raw sources -> standard JSON (never knows about rendering)
  common/normalize.py    canonical city-name normalization (used for coords fallback)
  common/geo_index.py    lookup(cbs_code) -> (kind, name, geometry)  [CBS code join]
  common/elections.py    shared election reader + per-dataset vote math
                         (SOURCES_DIR, haredi_share, PARTIES/BLOC, right_left_margin, top_parties)
  basemap/               the shared map of Israel — a provenance package
    sources/             localities.geojson (CBS polygons), coords.csv, aliases.csv,
                         border-src/ (israel + west-bank outlines)
    SOURCE.md            where geometry came from + method
    build_geo.py         -> public/data/geo.json
    build_border.py      -> public/data/border.json (dissolved national outline)
  elections/             SHARED source: raw Knesset results, feeding many datasets
    sources/             raw election files 17-25 (per-locality CSVs + 17/18 ballot-box), committed
    SOURCE.md            source links + how the reader parses them
  datasets/              one provenance package per dataset (a reduction of a source)
    _TEMPLATE/           copy to start a new dataset (SOURCE.md, build.py, sources/)
    haredi-vote/         (Shas + UTJ) / valid  — reads ../../elections/sources
      SOURCE.md, build.py    -> public/data/datasets/haredi-vote.json (+ registers it)
    right-left-vote/     (R - L) / (R + L) margin + party breakdown — same source
      SOURCE.md, build.py    -> public/data/datasets/right-left-vote.json (+ registers it)
app/                 Next.js App Router (TypeScript)
  page.tsx               client view: picker + map + timeline + info panel
components/          DatasetPicker, MapView (D3 SVG + zoom/pan), Timeline, Legend, InfoButton, ThemeToggle
lib/                 types.ts, colorScale.ts, useData.ts
public/data/         geo.json, border.json, datasets/<id>.json, datasets/index.json
```

Each dataset (and the basemap) is a **provenance package**: `SOURCE.md` records
where its numbers came from + how they were derived, and `build.py` is the
reproducible builder. **Raw inputs live in `sources/`** (committed as-is, never
edited) — either the package's own, or a **shared source package** when more than
one consumer needs the same raw. The Knesset election results are such a shared
source (`pipeline/elections/`): the basemap reads them for the city universe +
size weight, and each election-derived dataset (`haredi-vote`, `right-left-vote`)
is a different *reduction* of them via `common/elections.py`. A new
election-based dataset is a new reduction, not a new copy of the raw.

The pipeline produces data; the frontend is a pure view. Keep that boundary.

## Data-format contract

**`geo.json`** — keyed by CBS locality code:
```jsonc
{ "cities": {
  "3000": { "nameHe":"ירושלים", "kind":"polygon", "geometry":{...GeoJSON...}, "weight":380000 },
  "1295": { "nameHe":"כפר ורדים", "kind":"point", "lat":32.9, "lon":35.2, "weight":4200 }
}}
```
`weight` ≈ city electorate size; drives dot radius and is dataset-independent.

**`datasets/<id>.json`**:
```jsonc
{
  "id": "right-left-vote",
  "title": "Right vs Left vote", "titleHe": "ימין מול שמאל",
  "descriptionHe": "...",          // one-line teaser shown under the header
  "infoHe": "**מה רואים כאן?**\n...", // OPTIONAL longer methodology (markdown-lite, ⓘ panel)
  "unit": "margin",                // "percent" | "margin" | ... drives value formatting
  "colorScale": { "type":"diverging", "scheme":"RdBu", "domain":[-1,1], "midpoint":0 },
  "timesteps": [ {"id":"k19","label":"הכנסת ה-19","sub":"Jan 2013"} /* ... */ ],
  "cities": {
    // a cell is EITHER a bare number…
    "3000": { "k19": 0.85, "k20": 0.83 },
    // …OR {v, parts}: same scalar in `v` + an optional breakdown for the tooltip
    "5000": { "k25": { "v": -0.38, "parts": [
      {"labelHe":"יש עתיד","value":0.33,"tag":"L"},
      {"labelHe":"הליכוד","value":0.17,"tag":"R"},
      {"labelHe":"אחר","value":0.14}
    ] } }
  }
}
```
Each dataset defines its own timeline. Timestep IDs are dataset-specific strings —
election-based datasets use `"k19"`, `"k20"`, etc.; year-based datasets use `"2020"`,
`"2021"`, etc. City values are objects keyed by timestep ID (missing key = no data).

A **cell** is either a bare `number` or `{v, parts}` — `v` is the scalar that
drives the color (the only thing the map needs); `parts` is an optional generic
breakdown `[{labelHe, value, tag?}]` rendered in the tooltip (`tag` is an opaque
category marker the frontend uses only to color bars, e.g. `"R"`/`"L"`). Mixing
the two forms within one dataset is allowed. The frontend reads cells through
`cellValue()` / `cellParts()` in `lib/types.ts` — never index `.v` directly.

`colorScale` is generic (`sequential`|`diverging`, a d3 scheme, domain, optional
`power`/`midpoint`) so new datasets render without frontend changes. `infoHe` is
optional; when present an ⓘ button opens a panel rendering it (markdown-lite:
`**bold**`, blank-line paragraphs, `- ` bullets).

**`datasets/index.json`** — registry for the picker: `[{id, titleHe, description}]`.

## Conventions

- **Join key** = CBS locality code (סמל יישוב). Election CSVs carry the CBS code
  directly; builders call `geo.lookup(cbs_code)` to get geometry. The polygon source
  is CBS statistical areas (`localities.geojson`, 1,387 localities); `coords.csv`
  provides point fallback for ~30 unrecognized Bedouin settlements.
- **Projection** is planar `d3.geoIdentity` with longitude×cos(lat) correction — NOT a
  spherical projection. The source polygons have inconsistent ring winding that renders
  inside-out under Mercator. See DECISIONS.
- **Never silently drop data.** Cities a dataset can't resolve go into a coverage report.
- **Tests:** Python logic (normalize, resolve, value math, merge) is unit-tested with
  pytest; `lib/colorScale.ts` is unit-tested; the map is verified by headless screenshot.

## Adding a dataset

1. `cp -r pipeline/datasets/_TEMPLATE pipeline/datasets/<id>`.
2. **Raw inputs:**
   - *New raw source* → drop the downloaded files into `<id>/sources/` (commit as-is).
   - *Reusing an existing shared source* (e.g. the Knesset results) → don't copy raw;
     read it via the shared package, e.g. `from elections import SOURCES_DIR`, and put
     your reduction in `common/` next to the others (see `right_left_margin`/`top_parties`).
3. Fill in `<id>/SOURCE.md` — **especially the source links and the method** (for a
   reused source, point at its package's `SOURCE.md` and document *your* reduction).
   Required, not optional: a folder of numbers with no provenance is the exact thing
   this structure exists to prevent.
4. Implement `<id>/build.py` to emit `public/data/datasets/<id>.json` keyed by CBS
   code, registering itself in `index.json`. It appears in the picker automatically.
   - Optionally set `infoHe` (ⓘ methodology panel) and emit `{v, parts}` cells to
     give each city a tooltip breakdown — both are generic, no frontend changes needed.

## Safety / workflow

- **Develop new features in a git worktree**, not directly on `main`. Create an
  isolated worktree (e.g. `git worktree add ../israelytics-<feature> -b <feature>`),
  build the feature there, then open a PR to merge back. Keeps `main` clean and
  lets the running dev server stay untouched.
- Don't `git push` or deploy without explicit go-ahead.
- Each dataset's raw lives in its own `sources/` and **is committed** (provenance).
  The only gitignored raw is the dead `pipeline/sources/` leftover.
