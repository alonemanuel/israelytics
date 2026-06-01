"""Build the national outline -> public/data/border.json.

Goal: a single clean landmass that (a) reads as the recognisable country and
(b) contains every city we render, so no locality ever sits outside the border.

We get there by unioning three lon/lat sources and filling interior holes:
  * sources/border-src/israel.json     — Israel (recognised extent; no Golan/WB)
  * sources/border-src/palestine.json  — West Bank (fills the central WB gap that
                                          Israel's outline excludes)
  * the dissolved city polygons from geo.json — pulls the outline out to wherever
                                          we actually have data (notably the Golan,
                                          which the two political outlines omit)

This is deliberately "the extent of what's shown", not a statement on borders.
The georgique/world-geojson sources are committed under sources/border-src/ for
provenance. Output is one GeoJSON geometry in lon/lat; the frontend projects it
with the same planar transform as the cities, so it lines up exactly.
"""

import json
import os

from shapely.geometry import shape, mapping, Polygon, MultiPolygon, MultiPoint
from shapely.ops import unary_union

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
SRC = os.path.join(HERE, "sources", "border-src")
GEO = os.path.join(ROOT, "public", "data", "geo.json")
OUT = os.path.join(ROOT, "public", "data", "border.json")

WELD = 0.012        # deg: bridge gaps between the political outlines and data blobs
SIMPLIFY = 0.0015   # deg: thin the outline so the file stays small
MIN_ISLAND = 0.04   # drop stray parts smaller than this fraction of the largest


def _load_geom(path):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    feat = g["features"][0] if g.get("type") == "FeatureCollection" else g
    return shape(feat.get("geometry", feat))


def _drop_holes(geom):
    if geom.geom_type == "Polygon":
        return Polygon(geom.exterior)
    return MultiPolygon([Polygon(p.exterior) for p in geom.geoms])


def build():
    parts = [_load_geom(os.path.join(SRC, "israel.json")),
             _load_geom(os.path.join(SRC, "palestine.json"))]

    with open(GEO, encoding="utf-8") as f:
        geo = json.load(f)

    east_pts = []   # city anchors east of the Jordan rift, to span the Golan
    for c in geo["cities"].values():
        if c.get("kind") == "polygon":
            g = shape(c["geometry"])
            g = g if g.is_valid else g.buffer(0)
            parts.append(g)
            pt = (g.centroid.x, g.centroid.y)
        else:
            pt = (c["lon"], c["lat"])
        if pt[0] >= 35.5:
            east_pts.append(pt)

    # The political outlines stop at the pre-1967 line, but the data includes the
    # Golan. Hull the eastern anchors (Sea-of-Galilee region up into the Golan) and
    # add it so the Golan localities join the main body instead of floating off.
    if east_pts:
        parts.append(MultiPoint(east_pts).convex_hull.buffer(0.02))

    u = unary_union([p if p.is_valid else p.buffer(0) for p in parts])
    u = u.buffer(WELD).buffer(-WELD)       # weld near-touching pieces into one body
    u = _drop_holes(u)

    if u.geom_type == "MultiPolygon":
        ordered = sorted(u.geoms, key=lambda p: p.area, reverse=True)
        keep = [p for p in ordered if p.area >= ordered[0].area * MIN_ISLAND]
        u = keep[0] if len(keep) == 1 else MultiPolygon(keep)

    u = u.simplify(SIMPLIFY, preserve_topology=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(mapping(u), f, ensure_ascii=False, separators=(",", ":"))

    n_parts = 1 if u.geom_type == "Polygon" else len(u.geoms)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"border.json: {u.geom_type} ({n_parts} part(s)), {size_kb} KB")


if __name__ == "__main__":
    build()
