# Base map — source & method

**Outputs:** `public/data/geo.json` (city geometry) and `public/data/border.json`
(national outline)
**Builders:** `./build_geo.py` (reads `./sources` + the election results, see below)
and `./build_border.py` (reads the two outlines below + `geo.json`)

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

## National outline (`border.json`)

`build_border.py` produces a single dissolved landmass used as the map's country
silhouette. It **unions** three lon/lat sources and fills interior holes:

1. `israel.json` — the recognised national outline.
2. `palestine.json` — the West Bank, which fills the central gap that Israel's
   outline excludes (so the country reads as one body, not a shape with a bite out).
3. The **dissolved city polygons** from `geo.json`, plus a convex hull of the
   easternmost city anchors — this pulls the outline out to the **Golan**, which the
   two political outlines omit but the data covers.

The result is verified to **contain every city** in `geo.json` (0 outside). This is
deliberately "the extent of what we render," not a statement on borders — picking
any single political boundary would leave Golan/eastern localities outside the line.
See `docs/DECISIONS.md`.

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
