"""Build the shared base map -> public/data/geo.json.

Geometry comes from this folder's sources/ (localities.geojson, coords.csv).
The city *universe* and per-city size `weight` are derived from the election
results in the shared election-source package (../elections/sources, exposed as
elections.SOURCES_DIR). That cross-dependency is intentional and documented in
basemap/SOURCE.md; if the basemap ever needs to stand alone, swap in a dedicated
CBS locality+population source.
"""

import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "common"))
from elections import ELECTIONS, SOURCES_DIR, read_localities       # noqa: E402
from geo_index import GeoIndex                                     # noqa: E402

ROOT = os.path.join(HERE, "..", "..")
GEO_SOURCES = os.path.join(HERE, "sources")
ELECTION_SOURCES = SOURCES_DIR
OUT = os.path.join(ROOT, "public", "data", "geo.json")


def build():
    geo = GeoIndex(GEO_SOURCES)

    cities = {}            # CBS code -> city record
    unmatched = {}         # CBS code -> (raw name, max eligible)
    for n, _ in ELECTIONS:
        for loc in read_localities(ELECTION_SOURCES, n):
            cbs = loc["cbs_code"]
            if not cbs:
                continue
            kind, name, geometry = geo.lookup(cbs, loc["raw"])
            if not kind:
                prev = unmatched.get(cbs, ("", 0))
                unmatched[cbs] = (loc["raw"], max(prev[1], loc["eligible"]))
                continue
            rec = cities.get(cbs)
            if rec is None:
                rec = {"nameHe": name, "kind": kind, "weight": 0}
                if kind == "polygon":
                    rec["geometry"] = geometry
                else:
                    rec["lat"], rec["lon"] = geometry["lat"], geometry["lon"]
                cities[cbs] = rec
            rec["weight"] = max(rec["weight"], loc["eligible"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"cities": cities}, f, ensure_ascii=False,
                  separators=(",", ":"))

    n_poly = sum(1 for c in cities.values() if c["kind"] == "polygon")
    n_dot = sum(1 for c in cities.values() if c["kind"] == "point")
    size_kb = os.path.getsize(OUT) // 1024
    print(f"geo.json: {len(cities)} cities ({n_poly} polygons, {n_dot} points), "
          f"{size_kb} KB")
    top = sorted(unmatched.items(), key=lambda x: -x[1][1])[:5]
    print(f"unmatched localities: {len(unmatched)} "
          f"(top: {[(name, elig) for _, (name, elig) in top]})")


if __name__ == "__main__":
    build()
