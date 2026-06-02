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

### 2026-05-29 — Join key: CBS locality code (סמל יישוב), not Hebrew name
**What:** Switch the city join key from normalized Hebrew names to CBS locality codes —
stable numeric identifiers from the Israeli Central Bureau of Statistics.
**Why:** Hebrew names are fragile: encoding issues, normalization edge cases (dashes,
geresh, parentheticals), renaming (נצרת עילית → נוף הגליל). CBS codes are
language-independent, unambiguous, and stable across data sources.
**Rejected (previously):** Normalized Hebrew name — was the original choice for
human-readability, but fragility outweighed that benefit. Hebrew names are kept as
display labels (`nameHe` in geo.json).
**Migration:** `geo_index.py` still resolves names internally; builders call
`register_cbs_codes()` then `cbs_code_for()` to get the CBS code for output.

### 2026-05-29 — Object-keyed timesteps, not positional arrays
**What:** City values in datasets changed from positional arrays aligned to the timesteps
list (`[0.85, 0.83, null]`) to objects keyed by timestep ID (`{"k19": 0.85, "k20": 0.83}`).
**Why:** Positional arrays are fragile — one off-by-one and every value shifts silently.
Objects are self-documenting, sparse-safe (missing key = no data, no nulls needed), and
support datasets with irregular timelines (elections happen at uneven intervals).
**Rejected:** Positional arrays — more compact, but the ~250 cities × <30 timesteps
means the size difference is negligible. Safety and debuggability win.

### 2026-05-29 — Each dataset defines its own timeline
**What:** Timestep IDs are dataset-specific strings, not a global time axis. Election
datasets use `"k19"`, `"k20"`, etc. Year-based datasets use `"2020"`, `"2021"`, etc.
**Why:** Different data sources have fundamentally different time axes — elections are
irregular (sometimes 1 year apart, sometimes 4), while population data is annual. A
single shared timeline would force awkward alignment. The slider just steps through
whatever timesteps the dataset declares, so the frontend doesn't care.
**Rejected:** A single global year axis — would require interpolation or many nulls for
irregular data like elections.

## D-009 — UI redesign: full-bleed map, vertical timeline, auto light/dark

The map is now the canvas: it fills the viewport and the controls (top bar, dataset
picker, timeline, legend, zoom) float over it as translucent "glass" cards. This is a
mobile-first, map-app layout rather than a stacked dashboard.

Decisions:
- **Vertical timeline** docked to the (RTL) right edge, custom-built (not a native
  `<input type=range>`): newest timestep on top, large touch thumb, per-timestep ticks,
  a floating label, plus drag / tap-tick / arrow-key control. A native vertical range is
  inconsistent across browsers and has a tiny touch target.
- **Auto light/dark** via `prefers-color-scheme` and CSS custom properties (design
  tokens), so the app respects the device setting. `viewport.themeColor` follows suit.
- **Accent = Israeli blue**, kept distinct from the per-dataset map color schemes so UI
  chrome never competes with the data.
- **Heebo** webfont via `next/font` (self-hosted, no layout shift) for a branded Hebrew +
  Latin face instead of system fonts.
- **Tap-to-inspect**: tapping a city pins its tooltip and highlights it, since hover does
  not exist on touch. Tapping empty map clears it.

`NO_DATA_COLOR` moved from `#555` to a mid-slate (`#94a0b3`) that reads on both themes.

Rejected: a CSS framework (Tailwind). The surface area is small; plain CSS with tokens
keeps the dependency footprint minimal and the pure-view boundary intact.

### 2026-05-29 — CBS statistical areas as polygon source (replacing municipalities.geojson)
**What:** Replaced the ~250-feature `municipalities.geojson` (municipalities + local
councils + regional councils) with the CBS "Statistical Areas with Demographic Data"
geodatabase, dissolved by `SEMEL_YISHUV` to produce `localities.geojson` (1,387
per-locality polygons). Coverage went from 190 polygons to 1,190 out of 1,212 cities.
**Why:** The old source only had jurisdictional boundaries — municipalities and
regional councils. Small settlements (kibbutzim, moshavim, community settlements,
Bedouin towns) within regional councils had no polygon and were shown as dots. The CBS
source has a polygon for every recognized locality because each is at least one
statistical area.
**Rejected:** Voronoi tessellation from point coordinates (synthetic, not real
boundaries), buffer circles (still not real boundaries), keeping dots (poor UX).
**Caveats:** The CBS source uses 2011 statistical area boundaries. ~30 unrecognized
Bedouin settlements have no CBS polygon and fall back to point coordinates from
coords.csv. Geometry is simplified (tolerance 0.0005°, ~50m) to keep file size
manageable (~2.3 MB source, ~1 MB output).

### 2026-05-29 — Simplified GeoIndex: CBS code as primary key
**What:** Rewrote `geo_index.py` to look up geometry by CBS code directly via
`lookup(cbs_code)`, instead of the old name-normalization + alias resolution path.
**Why:** With CBS codes as the join key and CBS polygons as the geometry source, name
matching is no longer needed for the core join. The old approach (normalize Hebrew name
→ tight_key → alias → polygon lookup) was the most fragile part of the pipeline.
CBS code lookup is O(1) with zero ambiguity.
**Kept:** `normalize.py` and `coords.csv` for the point fallback (the ~30 unrecognized
settlements that need name-based coordinate lookup).
**Removed:** `aliases.csv` dependency for polygon matching, `register_cbs_codes()`,
`cbs_code_for()`, `resolve()`.

### 2026-05-29 — Datasets are self-contained provenance packages
**What:** Reorganized `pipeline/` so each dataset (and the basemap) is a folder
holding its raw downloaded files (`sources/`, committed as-is), a `SOURCE.md`
(where the raw came from + how it became numbers + caveats), and its `build.py`.
A `_TEMPLATE/` is the copy-to-start skeleton.
**Why:** A folder of final numbers is hard to reverse-engineer. Keeping the raw,
the source links, and the method beside the output makes every dataset reproducible
and auditable a year later — the whole motivation.
**Rejected:** A machine-readable `manifest.json` + sha256 `verify.py` — deferred as
YAGNI. The raw files are committed to git, so git already provides versioning and
tamper-detection; a `SOURCE.md` sources-table covers the human need. Add the manifest
later if automated re-fetching or cross-dataset tooling actually appears.
**Decided:** commit raw into the repo (self-contained, survives dead links);
provenance is repo-only for now (no UI changes).

### 2026-05-29 — Extend Haredi dataset back to 2006/2009 from ballot-box sources
**What:** Added the 17th (2006) and 18th (2009) Knessets to `haredi-vote`, so the
timeline is now 17–25 (nine elections). Their only available sources are
**per-ballot-box** (17th = a legacy `.xls`; 18th = a CSV), so the builder
aggregates ballot boxes up to the locality before computing the share.
**Why:** More history makes the "how the Haredi vote changed" story far stronger,
and the data exists.
**How:** The 18th carries a CBS code, so it groups by code directly. The 17th has
only city names, so codes are backfilled via `build_name_to_cbs` (the name↔code
pairs in the 19–25 per-locality files). ~96 of ~1,210 2006 localities don't resolve
(tiny/renamed places) and are omitted; reported, not silent.
**Validation:** National Haredi share computes to 14.5% (2006) and 13.0% (2009),
matching published Shas+UTJ results; per-city spot checks (Bnei Brak 0.80→0.90,
Modiin Illit ~0.97, Tel Aviv 0.09→0.05) are correct.
**Note:** Adds an `xlrd` dependency (only path that reads legacy `.xls`); recorded
in `pipeline/requirements.txt`.

### 2026-06-01 — Map redesign: national outline, neutral theme, screen-space labels
**What:** A visual overhaul of the map view. Four notable decisions below.

**National outline (`border.json`).** Added a filled country silhouette so land
reads as clearly separated from sea. Built by `build_border.py` as the **union** of
(a) an Israel outline + (b) a West Bank outline (both from
github.com/georgique/world-geojson, committed under `basemap/sources/border-src/`)
+ (c) the dissolved city polygons and a convex hull of the easternmost cities.
**Why this and not a single downloaded border:** the data includes Golan and eastern
localities that any one political outline omits, so a recognised-Israel border alone
left ~28 cities outside the line. Unioning with the data guarantees the outline
contains **every** city (verified 0 outside) and sidesteps picking a contested
boundary — it is "the extent of what we render."
**Rejected:** (1) dissolving only the city polygons — they are non-contiguous
(scattered municipal areas), so the union was a 25-piece archipelago, not a country.
(2) Adopting a tile/vector map provider (MapLibre) for the border + labels — would
require fixing CBS polygon winding for Mercator, a tile-provider API key, and a
`MapView` rewrite, for a basemap mostly hidden under the choropleth. Deferred.

**Theme.** Replaced the blue-tinted palette + auto-only dark mode with a neutral
(warm-paper / graphite) palette and an explicit light/dark **toggle** persisted in
localStorage, applied pre-paint by an inline script in `layout.tsx` to avoid a flash.
The no-data color became a CSS var (`--map-empty`) so it follows the theme.
**Why:** the blue cast fought the data colors; users want to choose, and the choice
must survive reloads.

**City labels in screen space.** Labels are an HTML overlay positioned in real px by
projecting centroids through the live zoom transform, with weight-priority collision.
**Why:** the first attempt rendered SVG text inside the zoomed `<g>` sized at
`12/k` units — tiny on mobile (canvas-relative, not screen) and kerning broke at high
zoom (sub-pixel font scaled up). Screen-space text is crisp at every zoom, on every
device, with no new dependency.

**Pinned tooltip follows its city.** A pinned (clicked) tooltip is re-anchored to its
city centroid on every zoom/pan (and hidden when the city scrolls off-stage), instead
of staying frozen at the original click pixel.

### 2026-06-01 — Promote the election results to a shared source package
**What:** Moved the raw Knesset CSVs out of `datasets/haredi-vote/sources/` into a
new top-level `pipeline/elections/` provenance package (its own `SOURCE.md`). All
consumers — `basemap/build_geo.py` and every election-derived dataset — now read
them via `elections.SOURCES_DIR`. Introduced the idea that **one source feeds many
datasets**; a dataset is a *reduction* of a source, not necessarily the owner of raw.
**Why:** The results were never really "the haredi dataset's data" — the basemap
already reached into that folder (a documented cross-dependency), and adding a
right-vs-left map gave a third consumer of the identical raw. Filing shared raw
under one arbitrary dataset is a smell that gets worse with each new consumer.
**Rejected:** (a) *Piggyback* — point the new builder at `../haredi-vote/sources`.
Zero migration but doubles down on the mis-filing; two outsiders reaching into one
dataset. (b) Put the raw in `pipeline/sources/` — that path is gitignored, and
shared raw must be committed for provenance, so it would have been invisible.
**Note:** `git mv` preserved history; the basemap's cross-dependency note and
CLAUDE.md were updated to point at the shared package.

### 2026-06-01 — Right-vs-Left dataset: signed margin, two-bloc, per-election table
**What:** Added `right-left-vote` — value = `(R − L)/(R + L)` in [−1,+1], rendered
with a diverging RdBu scale (red=left, blue=right, white=even). Parties are split
into exactly two blocs (no center bucket) via a **per-election** letter→party→bloc
table (`elections.PARTIES`), with center and Arab parties counted as **Left**.
**Why:** A signed margin reads naturally as a red↔blue political map and reuses the
already-generic diverging colorScale (no frontend change). The table *must* be
per-election because ballot letters are reused by different parties across years
(`כן`=Kadima→National Unity; `ב`=Jewish Home→Yamina; `ט`=National Union→Religious
Zionism) — a global letter map would be silently wrong. Two-bloc + center/Arab→Left
were explicit user choices, documented as editorial in the dataset's SOURCE.md.
**Validation:** National margins match the historical record — 2006 = −0.167 (the
real 50R/70L seat split), flipping right from 2009 on; coverage 95–99% of valid votes.
**Rejected:** Right-share-of-(R+L) as a 0..1 value (less intuitive than a signed
axis); a three-bloc scheme with a neutral center (user chose two-bloc); a single
global party table (wrong, per above).

### 2026-06-01 — Generic per-cell breakdown (`{v, parts}`) + per-dataset `infoHe`
**What:** Two extensions so a dataset can say more than one number. (1) A cell may be
`{v, parts:[{labelHe,value,tag?}]}` instead of a bare number — `v` still drives the
color; `parts` is an optional breakdown shown in the tooltip (right-left fills the
top-6 parties + "אחר", tagged R/L). (2) A dataset may carry `infoHe`, markdown-lite
methodology shown behind an ⓘ button. Both are optional and dataset-agnostic; the
frontend reads cells through `cellValue()`/`cellParts()` and changes nothing else.
**Why:** "Right vs Left = −0.38" is opaque on its own — users want to know *how* a
city voted and *what the blocs mean*. Keeping the channels generic (`parts`/`tag`
are not party-specific; `info` is just markdown) means future non-election datasets
reuse them for free, preserving the "new dataset = new JSON, not new code" property.
**Rejected:** A separate lazy-loaded `<id>.details.json` sidecar (kept inline —
right-left is ~400 KB gzipped, a non-issue at one-country scale, and avoids a second
fetch + loading state); rendering the dev-facing `SOURCE.md` as the info panel (too
long/English/technical for end users — `infoHe` is a curated reader-facing blurb);
hardcoding a party-breakdown type (would not generalize to other datasets).
**Note:** `infoHe` panel is portaled to `<body>` — the header's `backdrop-filter`
(`.glass`) is a containing block that otherwise traps `position:fixed` children.

### 2026-06-01 — Map geometry fixes: real Golan, coast flush to cities, visible lakes
**What:** Reworked `build_border.py` to fix three wrong things in the silhouette and to
add an inland-water layer (`public/data/water.json`, drawn by `MapView`).
- **Golan.** Replaced the *convex hull of the easternmost city anchors* (a crude straight
  blob) with a real **Golan Heights** boundary from Natural Earth 10m `admin_0_disputed_areas`
  (`sources/border-src/golan.json`). The hull both mis-shaped the NE and was redundant now
  that the body already unions the city polygons.
- **Coast flush to cities.** The `israel.json` outline sits ~10 km offshore, so the
  silhouette showed a fat "beach" west of the coastal cities. We subtract that offshore
  strip — everything between the cities and the open Mediterranean — using a hand-drawn
  offshore polygon whose eastern edge tracks the coast, **bounded north of Gaza** so it never
  touches the Gaza-envelope / western-Negev localities. (First attempt auto-detected "the sea"
  as a connected exterior component; because the Mediterranean wraps around the south to the
  eastern/northern borders — and merges with the Gaza coast — buffering it clipped *all*
  borders and ate Ashkelon + the Gaza envelope. The bounded hand-drawn polygon is the fix.)
  *Crucially, the coastline must be the **same geometry as the city regions** or it reads as
  weird in/out slivers — the land edge weaving across the city edges.* So the coast becomes the
  seaward edge of the **coastal-city union itself**, full-resolution, with gaps between towns
  bridged (`COAST_BRIDGE` close) for a smooth beach line, and it is **not** re-simplified (only
  the inland/eastern/southern borders are). The body is simplified *before* the coast is built,
  so the file stays small (57 KB vs geo.json's ~1 MB) while the coast stays bit-for-bit on the
  city edges. Result: 0 cities outside the land.
- **Visible lakes.** The Kinneret and Dead Sea (Natural Earth 10m `lakes`,
  `sources/border-src/water.json`) are subtracted from the landmass (Kinneret → a hole;
  Dead Sea → an eastern shoreline indentation) and re-emitted as `water.json`, which the
  frontend draws as its own layer in a teal `--water` token (distinct from the RdBu
  political blue) with a real shoreline.
**Why:** all three were visibly wrong and the user asked for a beautiful, correct map. Cutting
the lakes from the land *and* drawing them as a layer means the silhouette's edge/shadow
respect the water while the lakes always read clearly as water regardless of overlap.
**Rejected:** (a) deriving the lakes as holes in the dissolved city polygons — the cities ring
the Kinneret but not the Israel/Jordan-straddling Dead Sea, so it wouldn't close; (b) swapping
in a higher-res downloaded coastline — wouldn't be *flush with our city polygons*, which is
what was asked; (c) eroding the whole body inward to the cities — would shrink the eastern/
southern borders (no cities sit right at those) and distort the silhouette.
**Note:** `border.json` carries the Kinneret as a hole; `.landmass` uses `fill-rule: evenodd`
so the hole cuts through regardless of ring winding. Verified with the real d3 projection
(geoIdentity + cos-lat) rasterized headless, since a browser couldn't be installed here.

### 2026-06-02 — Monochrome UI, color only from the data
**What:** The entire chrome (top bar, picker, timeline, legend, zoom, tooltip frame) is
achromatic — black/white/grays. The `--accent`/`--accent-strong` tokens, which used to be
orange, are now plain ink (near-black in light, near-white in dark), so brand mark, focus
rings, active states, selected outlines and the timeline fill all read as ink. Inland water
(Kinneret/Dead Sea) was retinted from teal to a neutral cool gray for the same reason. The
*only* color on screen now comes from the data layer.
**Why:** User direction — "black/white style; the color will come from the data." A neutral
shell makes the choropleth the unambiguous focus and lets any future dataset's palette stand
out without competing with a chromatic UI.
**Rejected:** Keeping the orange accent (the previous "neutral-first" compromise) — still a
second hue competing with the map; a colored-per-dataset accent — ties chrome to data and
muddies the "color = data" rule.

### 2026-06-02 — Data divergence palette: EarthDiv (earth-purple ↔ earth-orange)
**What:** Replaced the right-left dataset's `RdBu` (red↔blue) with a custom `EarthDiv`
interpolator in `lib/colorScale.ts`: earth-purple at the low pole (left, −1), a warm neutral
at the midpoint, earth-orange at the high pole (right, +1). Tooltip breakdown bars and the
Hebrew copy (`כתום`/`סגול`) were updated to match; sequential `haredi-vote` stays on `Purples`
(earth purple, one of the two poles).
**Why:** User direction — data should be vivid and specifically "earth orange and earth
purple." Orange-vs-purple also avoids the red/blue political-color baggage while orange keeps
a loose cultural tie to the Israeli right. Orientation (purple low / orange high) is fixed in
the interpolator so a dataset only names the scheme.
**Rejected:** d3's stock `interpolatePuOr` — its orientation is orange-low/purple-high and its
browns are muddier than the chosen earth tones.

### 2026-06-02 — Brand: vector mark + Hebrew logotype, Hebrew-only UI
**What:** The "י" glyph brand mark became a vectoric SVG (`components/BrandMark.tsx`): a rising
analytics trend line whose peak is a Star of David — "Israel + analytics" in one monochrome
`currentColor` glyph. The visible wordmark changed from English "Israelytics" to Hebrew
"ישראליטיקס" (serif/Hadassah), and the document title/description are Hebrew too. On mobile the
wordmark hides, leaving the icon + ⓘ, and the top bar tightens its insets/padding to hand the
map as much screen as possible.
**Why:** User direction — "nothing in English," a different/vectoric icon tied to Israel +
analytics, and maximum mobile screen space. A vector mark scales crisply at the small mobile
size where the wordmark is dropped.
**Rejected:** A literal Israel-silhouette icon (illegible at 26–32px and hard to read as
"analytics"); keeping the wordmark on mobile (eats the bar that the dataset name needs).

### 2026-06-02 — Visual redesign: editorial "atlas" composition
**What:** A ground-up restyle for a calmer, more designed feel. (1) Dropped the full-width
top-bar slab; the brand is now a hugs-its-content **masthead card** (vector mark + serif
wordmark + dataset caption) with the controls as separate floating glass pills — corner-anchored
clusters over a full-bleed map. (2) Map: replaced the hard drop-shadow + 1.5px coast with a
soft, diffuse lift + 1px hairline coast on a calm radial field; thinner region strokes; no-data
tone pulled close to the land so data clusters read first. (3) Timeline: thin rail + small
ticks + a refined thumb, with the active election shown as an always-on serif year readout that
rides the thumb (was hover-only). (4) Legend: serif title, hairline-separated "no data" row.
(5) Softer, larger-radius tokens (radii 12/16/22, blur 22px, diffuse shadows); deeper, calmer
light/dark palettes. (6) Hebraized the election date subs (e.g. "Nov 2022" → "נובמבר 2022") so
nothing in the UI is English.
**Why:** User feedback that the prior pass was "still very ugly" and a request to "make it
beautiful." The fixes target the specific ugliness: a heavy chrome slab, a hard-edged map, and
plain edge widgets — replaced with restrained editorial typography, soft depth, and an always-on
sense of where you are in time. Verified by iterating against headless screenshots (desktop +
mobile, light + dark, both datasets).
**Rejected:** A horizontal bottom timeline (cleaner in isolation but collides with the legend
and needs a logic rewrite of the vertical scrubber); on-canvas brand text with no card (worse
legibility where the map runs under the masthead).
