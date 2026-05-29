"""Build the <id> dataset -> public/data/datasets/<id>.json, and register it in
public/data/datasets/index.json.

Copy this folder to pipeline/datasets/<id>/, drop your raw files in ./sources/,
fill in ./SOURCE.md, and implement build() below. Key every city by its CBS
locality code (סמל יישוב) so values join onto geo.json. Use geo.lookup(cbs) to
confirm a code has geometry; report (don't silently drop) codes that don't.
"""

import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
from geo_index import GeoIndex                                     # noqa: E402

ROOT = os.path.join(HERE, "..", "..", "..")
OWN_SOURCES = os.path.join(HERE, "sources")
GEO_SOURCES = os.path.join(HERE, "..", "..", "basemap", "sources")
DATASETS = os.path.join(ROOT, "public", "data", "datasets")

DATASET_ID = "REPLACE-ME"
META = {
    "id": DATASET_ID,
    "title": "REPLACE-ME",
    "titleHe": "REPLACE-ME",
    "descriptionHe": "REPLACE-ME",
    "unit": "percent",                 # percent | count | ...
    # sequential (with optional "power") or diverging (with "midpoint").
    # scheme is a d3 name registered in lib/colorScale.ts.
    "colorScale": {"type": "sequential", "scheme": "Blues", "domain": [0, 1]},
    # Each dataset defines its own timeline; ids are dataset-specific strings.
    "timesteps": [{"id": "2020", "label": "2020"}],
}


def build():
    geo = GeoIndex(GEO_SOURCES)

    # cities: CBS code -> { timestep_id: value }.  Missing key = no data.
    cities = {}
    # ... read OWN_SOURCES, compute values, key by CBS code, use geo.lookup(cbs) ...

    os.makedirs(DATASETS, exist_ok=True)
    with open(os.path.join(DATASETS, f"{DATASET_ID}.json"), "w", encoding="utf-8") as f:
        json.dump(dict(META, cities=cities), f, ensure_ascii=False, separators=(",", ":"))
    _register()
    print(f"{DATASET_ID}.json: {len(cities)} cities")


def _register():
    path = os.path.join(DATASETS, "index.json")
    registry = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    registry = [d for d in registry if d.get("id") != DATASET_ID]
    registry.append({"id": DATASET_ID, "titleHe": META["titleHe"],
                     "title": META["title"], "descriptionHe": META["descriptionHe"]})
    registry.sort(key=lambda d: d["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    build()
