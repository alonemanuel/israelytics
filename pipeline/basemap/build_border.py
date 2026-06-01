"""Build the national outline + inland water -> public/data/border.json + water.json.

Two outputs, both lon/lat, projected by the frontend with the same planar
transform as the cities so they line up exactly:

  * border.json — a single clean landmass that (a) reads as the recognisable
    country and (b) contains every city we render, with the **Kinneret cut out**
    as a hole.
  * water.json  — the inland water bodies (Kinneret + Dead Sea) drawn as their
    own layer so they read clearly as water, with a real shoreline.

How the landmass is built:
  1. Union four lon/lat sources into one coherent body:
       - sources/border-src/israel.json     (Israel, recognised extent)
       - sources/border-src/palestine.json  (West Bank — fills the central gap)
       - sources/border-src/golan.json       (Golan Heights — a real boundary,
                                               replacing the old convex-hull hack)
       - the dissolved city polygons from geo.json (pulls the outline out to
                                               wherever we actually have data)
     then close small gaps and fill interior data-holes so it's one solid shape.
  2. Clip the western **coast flush to the coastal cities**: the israel.json
     outline sits ~10 km offshore, leaving an ugly "beach" between the cities and
     the sea. We subtract that offshore strip (everything between the cities and
     the open Mediterranean) so the land edge meets the city borders exactly.
  3. Subtract the inland water bodies (Kinneret + Dead Sea) so the lakes show.

This is deliberately "the extent of what's shown", not a statement on borders.
The political/water sources are committed under sources/border-src/ for provenance.
"""

import json
import os

from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
SRC = os.path.join(HERE, "sources", "border-src")
GEO = os.path.join(ROOT, "public", "data", "geo.json")
OUT_BORDER = os.path.join(ROOT, "public", "data", "border.json")
OUT_WATER = os.path.join(ROOT, "public", "data", "water.json")

WELD = 0.012         # deg: bridge gaps between the political outlines and data blobs
SIMPLIFY = 0.0015    # deg (~150 m): thin the *inland* border + the water bodies
COAST_BRIDGE = 0.016 # deg (~1.6 km): bridge the gaps between coastal cities so the
                     # coastline runs smoothly across beaches/reserves between towns

# The Mediterranean, as a polygon west of the country whose eastern edge tracks
# the real coastline (a touch inland of it). Intersected with the body it is the
# fat offshore strip the crude israel.json outline adds; subtracting the coastal
# cities from it makes the clip stop exactly at the city edges. Bounded north of
# Gaza so it never touches the Gaza envelope / western Negev localities.
MED_COAST = Polygon([
    (33.00, 31.55), (34.58, 31.62), (34.67, 31.80), (34.79, 32.08),
    (34.88, 32.33), (34.98, 32.83), (35.13, 33.10), (33.00, 33.15),
])

# Hebrew names for the water layer (keyed by the source feature name).
WATER_NAMES = {"Kinneret": "הכנרת", "Dead Sea": "ים המלח"}


def _load_geom(path):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    feat = g["features"][0] if g.get("type") == "FeatureCollection" else g
    return shape(feat.get("geometry", feat))


def _clean(g):
    return g if g.is_valid else g.buffer(0)


def _largest(g):
    return max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g


def _fill_holes(g):
    return Polygon(g.exterior)


def _read_water():
    """Return [(name_he, geometry), ...]; Dead Sea's two basins merged into one."""
    fc = json.load(open(os.path.join(SRC, "water.json"), encoding="utf-8"))
    by_name = {}
    for feat in fc["features"]:
        name_he = WATER_NAMES.get(feat["properties"].get("name"), feat["properties"].get("name"))
        geom = _clean(shape(feat["geometry"]))
        by_name[name_he] = unary_union([by_name[name_he], geom]) if name_he in by_name else geom
    return list(by_name.items())


def build():
    israel = _clean(_load_geom(os.path.join(SRC, "israel.json")))
    pal = _clean(_load_geom(os.path.join(SRC, "palestine.json")))
    golan = _clean(_load_geom(os.path.join(SRC, "golan.json")))
    # Simplify the water once and reuse it for both the cut-out and the layer, so
    # the Kinneret hole in the land matches the water drawn over it exactly.
    water = [(name, _clean(g.simplify(SIMPLIFY, preserve_topology=True)))
             for name, g in _read_water()]
    water_u = unary_union([g for _, g in water])

    with open(GEO, encoding="utf-8") as f:
        geo = json.load(f)
    cities_u = unary_union([
        _clean(shape(c["geometry"]))
        for c in geo["cities"].values() if c.get("kind") == "polygon"
    ])

    # 1) one coherent body, gaps closed, interior data-holes filled. Simplify it
    #    now: this smooths the inland / eastern / southern borders, while the
    #    western coast is replaced below by the full-resolution city edges (which
    #    must stay bit-for-bit identical to the city regions, so they're flush).
    body = _clean(unary_union([israel, pal, golan, cities_u]))
    body = _clean(body.buffer(WELD).buffer(-WELD))
    body = _fill_holes(_largest(body))
    body = _clean(body.simplify(SIMPLIFY, preserve_topology=True))

    # 2) clip the western coast flush to the coastal cities. The coastline becomes
    #    the seaward edge of the coastal-city union itself (full resolution, the
    #    same geometry the city regions are drawn from), with the gaps between
    #    towns bridged so it runs smoothly along the beach. The result is NOT
    #    simplified again — that would move the coast off the city edges.
    coast = _clean(cities_u.buffer(COAST_BRIDGE).buffer(-COAST_BRIDGE))
    beach = MED_COAST.intersection(body).difference(coast)
    land = _clean(body.difference(beach))
    land = _clean(unary_union([land, cities_u]))   # coast == exact city edges
    land = _fill_holes(_largest(land))

    # 3) cut the inland water out of the land (Kinneret becomes a hole; the Dead
    #    Sea, straddling the eastern edge, becomes a shoreline indentation)
    land = orient(_largest(_clean(land.difference(water_u))), sign=1.0)  # ext CCW, holes CW

    with open(OUT_BORDER, "w", encoding="utf-8") as f:
        json.dump(mapping(land), f, ensure_ascii=False, separators=(",", ":"))

    water_out = [{"nameHe": name, "geometry": mapping(geom)} for name, geom in water]
    with open(OUT_WATER, "w", encoding="utf-8") as f:
        json.dump(water_out, f, ensure_ascii=False, separators=(",", ":"))

    n_holes = len(land.interiors)
    kb = os.path.getsize(OUT_BORDER) // 1024
    print(f"border.json: {land.geom_type}, {n_holes} lake hole(s), {kb} KB")
    print(f"water.json: {len(water_out)} bodies ({', '.join(n for n, _ in water)})")


if __name__ == "__main__":
    build()
