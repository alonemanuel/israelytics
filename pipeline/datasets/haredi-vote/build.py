"""Build the Haredi-vote dataset -> public/data/datasets/haredi-vote.json,
and register it in public/data/datasets/index.json.

Per city per election: (Shas + UTJ) / valid votes. Spelling variants that
resolve to the same CBS code are merged. Keys are CBS locality codes, so they
line up with geo.json. Raw inputs and provenance live alongside this file:
see ./sources and ./SOURCE.md.
"""

import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
from elections import ELECTIONS, read_localities, haredi_share, merge_shares  # noqa: E402
from geo_index import GeoIndex                                                # noqa: E402

ROOT = os.path.join(HERE, "..", "..", "..")
OWN_SOURCES = os.path.join(HERE, "sources")
GEO_SOURCES = os.path.join(HERE, "..", "..", "basemap", "sources")
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
    geo = GeoIndex(GEO_SOURCES)
    n_steps = len(ELECTIONS)

    # CBS code -> list of per-election share-lists (one per spelling variant)
    by_cbs = {}
    national_haredi = [0] * n_steps
    national_valid = [0] * n_steps
    unmatched = {}

    for i, (n, _) in enumerate(ELECTIONS):
        for loc in read_localities(OWN_SOURCES, n):
            cbs = loc["cbs_code"]
            share = haredi_share(loc["votes"], loc["valid"])
            national_haredi[i] += sum(loc["votes"].get(l, 0) for l in ("שס", "ג"))
            national_valid[i] += loc["valid"]
            if not cbs:
                continue
            kind, _, _ = geo.lookup(cbs, loc["raw"])
            if not kind:
                unmatched[cbs] = max(unmatched.get(cbs, 0), loc["valid"])
                continue
            entry = by_cbs.setdefault(cbs, [])
            shares = [None] * n_steps
            shares[i] = share
            entry.append(shares)

    merged = {cbs: merge_shares(lists) for cbs, lists in by_cbs.items()}

    timestep_ids = [f"k{n}" for n, _ in ELECTIONS]
    cities = {}
    for cbs, values in merged.items():
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
