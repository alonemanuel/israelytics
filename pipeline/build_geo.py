"""Build the shared base map -> public/data/geo.json.

The universe of cities is whatever appears in the election files (the most
complete per-city list we have, and the only source with a size measure). Each
city is resolved to polygon or point geometry via the shared GeoIndex, and given
a dataset-independent `weight` (max eligible voters across elections) for dot
sizing. Cities that resolve to no geometry are reported, never silently dropped.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "common"))
from elections import ELECTIONS, read_localities, register_cbs_codes  # noqa: E402
from geo_index import GeoIndex                                         # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOURCES = os.path.join(os.path.dirname(__file__), "sources")
OUT = os.path.join(ROOT, "public", "data", "geo.json")


def build():
    geo = GeoIndex(SOURCES)
    register_cbs_codes(geo, SOURCES)

    cities = {}            # CBS code -> city record
    unmatched = {}         # raw name -> max eligible (for the report)
    for n, _ in ELECTIONS:
        for loc in read_localities(SOURCES, n):
            key, kind = geo.resolve(loc["raw"])
            if not key:
                unmatched[loc["raw"]] = max(unmatched.get(loc["raw"], 0),
                                            loc["eligible"])
                continue
            cbs = geo.cbs_code_for(key)
            if not cbs:
                continue
            rec = cities.get(cbs)
            if rec is None:
                rec = {"nameHe": geo.name_for(key, kind), "kind": kind,
                       "weight": 0}
                geom = geo.geometry_for(key, kind)
                if kind == "polygon":
                    rec["geometry"] = geom
                else:
                    rec["lat"], rec["lon"] = geom["lat"], geom["lon"]
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
    print(f"unmatched localities: {len(unmatched)} "
          f"(top: {sorted(unmatched.items(), key=lambda x: -x[1])[:5]})")


if __name__ == "__main__":
    build()
