# Base map — source & method

**Outputs:** `public/data/geo.json` (city geometry), `public/data/border.json`
(national outline) and `public/data/water.json` (inland water bodies)
**Builders:** `./build_geo.py` (reads `./sources` + the election results, see below)
and `./build_border.py` (reads the outlines + water below + `geo.json`)

## What this is

The shared geometry of Israeli localities — one entry per CBS locality code,
either a polygon boundary or a fallback point — that every dataset is drawn on.
Built once; datasets join onto it by CBS code.

## Sources

| File | What | Source |
|------|------|--------|
| `sources/localities.geojson` | Per-locality polygon boundaries keyed by CBS code (`cbs_code`, `name_he`) | Israeli CBS "Statistical Areas with Demographic Data" geodatabase, dissolved by `SEMEL_YISHUV` and reprojected to WGS84 |
| `sources/coords.csv` | Lat/lon points by city name; fallback for localities missing from the CBS polygons | github.com/yuvadm/geolocations-il |
| `sources/aliases.csv` | Manual name-spelling aliases (legacy from name-based matching; mostly unused since the switch to CBS codes) | hand-written |
| `sources/border-src/israel.json` | Israel national outline (recognised extent) in lon/lat | github.com/georgique/world-geojson (`countries/israel.json`) |
| `sources/border-src/palestine.json` | West Bank outline in lon/lat; fills the central gap Israel's outline excludes | github.com/georgique/world-geojson (`countries/palestine.json`) |
| `sources/border-src/golan.json` | Golan Heights boundary in lon/lat; the data covers the Golan but the two outlines above omit it | Natural Earth 10m `admin_0_disputed_areas` (feature "Golan Heights") |
| `sources/border-src/water.json` | Kinneret + Dead Sea (two basins) water polygons in lon/lat | Natural Earth 10m `lakes` (features "Sea of Galilee", "Dead Sea") |

> **Fill in the exact source URL / download date for `localities.geojson`** (the
> CBS geodatabase export) so the basemap is fully reproducible.

## Method

1. `geo_index.GeoIndex` loads `localities.geojson` into a CBS-code → {geometry,
   name} map, and `coords.csv` into a name → lat/lon map (filtered to an Israel
   bounding box, which drops foreign mis-geocodes like Hebron→USA).
2. `build_geo.py` walks the **election results** (see the cross-dependency note) to
   get the universe of real localities and each one's `weight` (max eligible voters
   `בזב` across elections — a dataset-independent size proxy for dot radius).
3. For each locality's CBS code, `geo_index.lookup` returns a polygon if the code is
   in the CBS source, else a point from `coords.csv`, else nothing (reported).

## National outline (`border.json`) + water (`water.json`)

`build_border.py` produces a single dissolved landmass (the map's country
silhouette) and the inland water layer:

1. **Union** `israel.json` + `palestine.json` + `golan.json` + the dissolved city
   polygons from `geo.json` into one coherent body; close small gaps and fill
   interior data-holes. `palestine.json` fills the central West Bank gap; `golan.json`
   gives the Golan a real boundary (replacing an earlier convex-hull approximation);
   the city polygons pull the outline out to wherever we actually have data.
2. **Clip the western coast flush to the coastal cities.** The `israel.json` outline
   sits ~10 km offshore, which left an ugly "beach" between the cities and the sea.
   We subtract that offshore strip (everything between the cities and the open
   Mediterranean, bounded north of Gaza) so the coastline becomes the **seaward edge
   of the coastal-city union itself** — the same full-resolution geometry the city
   regions are drawn from, so the land edge and the city borders are bit-for-bit
   flush. Gaps between coastal towns are bridged (`COAST_BRIDGE`) so the line runs
   smoothly along the beach, and the coast is **not** re-simplified (that would move
   it off the city edges). Only the inland/eastern/southern borders are simplified.
3. **Subtract the inland water** (`water.json`): the Kinneret becomes a hole in the
   landmass; the Dead Sea, straddling the eastern edge, becomes a shoreline
   indentation. `water.json` is emitted separately so the frontend draws the lakes as
   their own layer (clear water with a real shoreline).

The result still **contains every city** in `geo.json` (0 outside). This is
deliberately "the extent of what we render," not a statement on borders. See
`docs/DECISIONS.md`.

## Cross-dependency (intentional)

The basemap reads the **election result CSVs** from the shared election-results
package (`../elections/sources/`, via `elections.SOURCES_DIR`) to derive the
locality universe and the `weight`. This couples the basemap to the election
source. It's deliberate for now — the election files are the most complete
locality list with a size measure. If the basemap ever needs to stand alone,
replace this with a dedicated CBS locality + population source and drop the
dependency.

## Caveats

- Rendered with a **planar** projection (`d3.geoIdentity` + cos-lat correction), not
  Mercator — see `docs/DECISIONS.md` (inconsistent polygon winding breaks spherical
  projections).
- A leftover `municipalities.geojson` (older name-keyed polygon source, ~6.9 MB) is
  superseded by `localities.geojson` and intentionally not committed.
