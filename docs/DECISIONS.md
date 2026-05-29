# Decisions

An append-only log of decisions made building Israelytics, and *why*. Newest entries at
the bottom. Add an entry whenever you make a choice whose rationale isn't obvious from
the code. Format: **what** / **why** / **rejected**.

---

### 2026-05-29 — Stack: Next.js (App Router, TypeScript) on Vercel
**What:** Build the site as a Next.js app deployed on Vercel.
**Why:** User preference; one-click/`git push` deploys; room to grow into a real platform.
**Rejected:** Static no-build site (simplest, but less room to grow); Vite + vanilla
(build step without the framework benefits).

### 2026-05-29 — Data model: timeline-always
**What:** Every dataset is city × timeline. A single snapshot is a timeline of length 1
and the slider hides itself.
**Why:** One code path for both cases; the first dataset (elections) is naturally a timeline.
**Rejected:** Separate "snapshot" vs "timeline" modes — more code for little gain.

### 2026-05-29 — Separate base map from datasets
**What:** A shared `geo.json` holds geometry; each dataset holds only values per city per
time-step; the frontend joins them by city key.
**Why:** Makes the platform generic — a new dataset is a JSON file, not new code. Geometry
is heavy and shared, so it shouldn't be duplicated per dataset.
**Rejected:** Bundling geometry into each dataset (simpler to load, but duplicated and
couples data to the map).

### 2026-05-29 — Join key: normalized Hebrew city name
**What:** Cities are keyed by their normalized Hebrew name (e.g. `"בני ברק"`), resolved
through `pipeline/common/geo_index.resolve`.
**Why:** Human-readable; datasets don't need to carry an extra code column; matches how
the source data already identifies cities.
**Rejected:** Numeric `סמל ישוב` (CBS code) — more robust against spelling variants, but
every dataset would have to carry it and it's opaque. Revisit if name collisions bite.

### 2026-05-29 — Generic `colorScale` metadata per dataset
**What:** Each dataset declares `{type: sequential|diverging, scheme, domain, power?, midpoint?}`.
**Why:** Lets future datasets (counts, percentages, diverging measures) render correctly
without changing frontend code.
**Rejected:** Hard-coding the color logic in the frontend (would need edits per dataset).

### 2026-05-29 — `weight` for dot size lives in `geo.json`
**What:** Each city carries a dataset-independent `weight` (≈ electorate size) used for dot radius.
**Why:** Dot size should be consistent across datasets; it's a property of the place, not the data.
**Rejected:** Per-dataset sizing (inconsistent dot sizes when switching datasets).

### 2026-05-29 — Haredi defined as Shas (שס) + UTJ (ג)
**What:** The first dataset counts the two Haredi party ballot letters, `{שס, ג}`, as a
fraction of valid votes; configurable in the builder.
**Why:** Standard proxy for the Haredi vote. Both letters are stable across elections 19–25.
**Note:** Shas voters include some traditional (non-Haredi) Mizrahi voters, so this
slightly over-counts — accepted as the conventional measure.

### 2026-05-29 — Planar projection (geoIdentity), not Mercator
**What:** Render with `d3.geoIdentity` (planar) plus a longitude×cos(latitude) aspect
correction, rather than a spherical projection like Mercator.
**Why:** The source municipality polygons have inconsistent ring winding. Under a
spherical projection D3 interprets a wrongly-wound ring as "the whole globe except this
area," rendering the map inside-out and collapsing the fit. Planar projection is immune.
**Rejected:** Mercator with ring-rewinding — attempted, but winding was inconsistent across
features and fragile; planar sidesteps the problem entirely.

### 2026-05-29 — Filter foreign mis-geocodes by Israel bounding box
**What:** Coordinates outside an Israel bounding box are dropped during the geo build.
**Why:** The coordinate source mis-geocodes some names that collide with foreign places
(e.g. Hebron → Illinois, Uman → Ukraine), which otherwise break the map's auto-fit.

### 2026-05-29 — Geo universe = cities in the election files; weight = eligible voters
**What:** `geo.json` contains exactly the localities that appear in the election CSVs
(resolved to geometry), and each city's `weight` is its max eligible voters (בזב) across
elections.
**Why:** The election files are the most complete per-city list of Israel with a size
measure. A dataset-independent size proxy has to come from somewhere; eligible voters is
the best signal available.
**Rejected:** Including every polygon/coordinate city (bloats the base map with places no
dataset covers). **Future option:** expand the universe if a dataset needs a city absent
from the election files.

### 2026-05-29 — D3 owns the SVG inside React via refs
**What:** `MapView` keeps the D3 selection/projection/zoom in refs. One effect (keyed on
geo) draws geometry + wires zoom once; a second effect (keyed on dataset/timestep) only
recolors. React owns the picker/slider/legend.
**Why:** Zoom/pan state must survive re-renders, and redrawing 1,200 shapes on every
slider tick is wasteful. Separating "draw once" from "recolor" keeps interaction smooth.
**Rejected:** Rendering every SVG element as React nodes (clean, but fights D3's zoom and
re-renders the whole map on each timestep).

### 2026-05-29 — Generic color schemes via an interpolator registry
**What:** `lib/colorScale.ts` maps a dataset's `scheme` string to a d3 interpolator from a
small registry, supporting sequential (with optional `power`) and diverging (with
`midpoint`).
**Why:** New datasets pick a color treatment by name in their JSON; no frontend changes.
**Rejected:** Importing all of d3-scale-chromatic dynamically (unnecessary; a curated
registry is clearer and smaller).
