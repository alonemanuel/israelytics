"""Build the Haredi-vote dataset -> public/data/datasets/haredi-vote.json,
and register it in public/data/datasets/index.json.

Per city per election: (Shas + UTJ) / valid votes. Spelling variants that
resolve to the same canonical key are merged. Keys come from the shared
GeoIndex, so they line up with geo.json.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "common"))
from elections import (ELECTIONS, read_localities, haredi_share,                # noqa: E402
                      merge_shares, register_cbs_codes)
from geo_index import GeoIndex                                                 # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOURCES = os.path.join(os.path.dirname(__file__), "sources")
DATASETS = os.path.join(ROOT, "public", "data", "datasets")

DATASET_ID = "haredi-vote"
META = {
    "id": DATASET_ID,
    "title": "Haredi vote share",
    "titleHe": "שיעור ההצבעה החרדית",
    "description": "Combined Shas + United Torah Judaism vote as a share of valid votes.",
    "descriptionHe": 'אחוז הקולות למפלגות החרדיות (ש"ס + יהדות התורה) מתוך כלל הקולות הכשרים.',
    "unit": "percent",
    "colorScale": {"type": "sequential", "scheme": "Purples", "domain": [0, 1],
                   "power": 0.55},
    "timesteps": [{"id": f"k{n}", "label": f"הכנסת ה-{n}", "sub": d} for n, d in ELECTIONS],
}


def build():
    geo = GeoIndex(SOURCES)
    register_cbs_codes(geo, SOURCES)
    n_steps = len(ELECTIONS)

    # canonical_key -> list of per-election share-lists (one per spelling variant)
    by_key = {}
    national_haredi = [0] * n_steps
    national_valid = [0] * n_steps
    unmatched = {}

    for i, (n, _) in enumerate(ELECTIONS):
        for loc in read_localities(SOURCES, n):
            key, _kind = geo.resolve(loc["raw"])
            share = haredi_share(loc["votes"], loc["valid"])
            national_haredi[i] += sum(loc["votes"].get(l, 0) for l in ("שס", "ג"))
            national_valid[i] += loc["valid"]
            if not key:
                unmatched[loc["raw"]] = max(unmatched.get(loc["raw"], 0), loc["valid"])
                continue
            entry = by_key.setdefault(key, [])
            shares = [None] * n_steps
            shares[i] = share
            entry.append(shares)

    merged = {key: merge_shares(lists) for key, lists in by_key.items()}

    timestep_ids = [f"k{n}" for n, _ in ELECTIONS]
    cities = {}
    for key, values in merged.items():
        cbs = geo.cbs_code_for(key)
        if not cbs:
            continue
        obj = {}
        for j, val in enumerate(values):
            if val is not None:
                obj[timestep_ids[j]] = val
        if obj:
            cities[cbs] = obj

    os.makedirs(DATASETS, exist_ok=True)
    dataset = dict(META, cities=cities)
    with open(os.path.join(DATASETS, f"{DATASET_ID}.json"), "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))

    _register()

    print(f"{DATASET_ID}.json: {len(cities)} cities, {n_steps} timesteps")
    print("national Haredi share per election:")
    for (n, d), h, v in zip(ELECTIONS, national_haredi, national_valid):
        print(f"  E{n} ({d}): {100*h/v:4.1f}%  ({h:,}/{v:,})")
    print(f"unmatched localities: {len(unmatched)}")


def _register():
    """Add/update this dataset in datasets/index.json (the picker registry)."""
    path = os.path.join(DATASETS, "index.json")
    registry = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            registry = json.load(f)
    registry = [d for d in registry if d.get("id") != DATASET_ID]
    registry.append({"id": DATASET_ID, "titleHe": META["titleHe"],
                     "title": META["title"], "descriptionHe": META["descriptionHe"]})
    registry.sort(key=lambda d: d["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    build()
