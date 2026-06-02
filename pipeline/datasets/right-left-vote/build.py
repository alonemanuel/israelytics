"""Build the Right-vs-Left dataset -> public/data/datasets/right-left-vote.json,
and register it in public/data/datasets/index.json.

Per city per election: the signed margin (R - L) / (R + L) between the right-wing
and left-wing blocs, in [-1, +1] (+1 = entirely right, -1 = entirely left), plus
a "how they voted" breakdown of the top parties. This reuses the *same* raw
election results as haredi-vote — a different reduction of one shared source. The
party table (letter -> name + bloc, per election) lives in common/elections.py
(PARTIES); the rationale and the full per-election table are documented in
./SOURCE.md.

Keys are CBS locality codes, so they line up with geo.json. Spelling variants
that resolve to the same CBS code in one election are combined by summing their
votes (the locality split across name spellings is one place).
"""

import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
from elections import (ELECTIONS, SOURCES_DIR, BLOC, read_localities,         # noqa: E402
                       right_left_margin, top_parties)
from geo_index import GeoIndex                                                 # noqa: E402

ROOT = os.path.join(HERE, "..", "..", "..")
ELECTION_SOURCES = SOURCES_DIR
GEO_SOURCES = os.path.join(HERE, "..", "..", "basemap", "sources")
DATASETS = os.path.join(ROOT, "public", "data", "datasets")

DATASET_ID = "right-left-vote"
META = {
    "id": DATASET_ID,
    "title": "Right vs Left vote",
    "titleHe": "ימין מול שמאל",
    "description": ("Signed margin between the right-wing and left-wing blocs as a "
                    "share of their combined vote: +1 all-right (orange), -1 all-left (purple)."),
    "descriptionHe": ("המרווח בין גוש הימין לגוש השמאל מתוך סך קולות שני הגושים: "
                      "‎1+‎ כולו ימין (כתום), ‎1-‎ כולו שמאל (סגול)."),
    # Reader-facing methodology, shown behind the ⓘ button. Markdown-lite
    # (**bold**, blank-line paragraphs, "- " bullets).
    "infoHe": (
        "**מה רואים כאן?**\n"
        "לכל יישוב מוצג המרווח בין **גוש הימין** ל**גוש השמאל** בכל בחירות לכנסת, "
        "מתוך סך הקולות לשני הגושים: ‎1+‎ (כתום) = כל הקולות לימין, ‎1-‎ (סגול) = כל "
        "הקולות לשמאל, ‎0‎ = תיקו.\n\n"
        "**איך מסווגים את המפלגות?**\n"
        "הסיווג אידאולוגי, לפי בחירות (אותה אות מייצגת מפלגות שונות בשנים שונות):\n"
        "- **ימין:** הליכוד, ש\"ס, יהדות התורה, הבית היהודי/ימינה/הציונות הדתית, "
        "ישראל ביתנו, תקווה חדשה.\n"
        "- **שמאל ומרכז:** העבודה/המחנה הציוני, מרצ, יש עתיד/כחול לבן/המחנה הממלכתי, "
        "קדימה, כולנו, והמפלגות הערביות.\n\n"
        "לפי בחירה זו מפלגות המרכז והמפלגות הערביות נספרות בגוש השמאל. "
        "ריחוף על יישוב מציג את פירוט ההצבעה בפועל."
    ),
    "unit": "margin",
    # Diverging: earth-purple (left) at -1, warm neutral at 0, earth-orange
    # (right) at +1. EarthDiv is defined in lib/colorScale.ts.
    "colorScale": {"type": "diverging", "scheme": "EarthDiv", "domain": [-1, 1],
                   "midpoint": 0},
    "timesteps": [{"id": f"k{n}", "label": f"הכנסת ה-{n}", "sub": d} for n, d in ELECTIONS],
}


def build():
    geo = GeoIndex(GEO_SOURCES)
    timestep_ids = [f"k{n}" for n, _ in ELECTIONS]

    # CBS code -> {timestep index -> combined {"votes": {...}, "valid": int}},
    # summing across spelling variants of the same locality in one election.
    acc = {}
    national_r = [0] * len(ELECTIONS)
    national_l = [0] * len(ELECTIONS)
    national_valid = [0] * len(ELECTIONS)
    unmatched = {}

    for i, (n, _) in enumerate(ELECTIONS):
        blocs = BLOC[n]
        for loc in read_localities(ELECTION_SOURCES, n):
            v = loc["votes"]
            national_r[i] += sum(c for ltr, c in v.items() if blocs.get(ltr) == "R")
            national_l[i] += sum(c for ltr, c in v.items() if blocs.get(ltr) == "L")
            national_valid[i] += loc["valid"]
            cbs = loc["cbs_code"]
            if not cbs:
                continue
            kind, _, _ = geo.lookup(cbs, loc["raw"])
            if not kind:
                unmatched[cbs] = max(unmatched.get(cbs, 0), loc["valid"])
                continue
            slot = acc.setdefault(cbs, {}).setdefault(i, {"votes": {}, "valid": 0})
            slot["valid"] += loc["valid"]
            for ltr, c in v.items():
                slot["votes"][ltr] = slot["votes"].get(ltr, 0) + c

    cities = {}
    for cbs, by_step in acc.items():
        obj = {}
        for i, rec in by_step.items():
            election = ELECTIONS[i][0]
            margin = right_left_margin(rec["votes"], election)
            if margin is None:
                continue
            obj[timestep_ids[i]] = {
                "v": round(margin, 4),
                "parts": top_parties(rec["votes"], rec["valid"], election),
            }
        if obj:
            cities[cbs] = obj

    os.makedirs(DATASETS, exist_ok=True)
    dataset = dict(META, cities=cities)
    with open(os.path.join(DATASETS, f"{DATASET_ID}.json"), "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))

    _register()

    print(f"{DATASET_ID}.json: {len(cities)} cities, {len(ELECTIONS)} timesteps")
    print("national right/left bloc share + margin per election "
          "(coverage = classified / valid):")
    for (n, d), r, l, vv in zip(ELECTIONS, national_r, national_l, national_valid):
        margin = (r - l) / (r + l) if (r + l) else 0
        cov = (r + l) / vv if vv else 0
        print(f"  E{n} ({d}): R={100*r/vv:4.1f}%  L={100*l/vv:4.1f}%  "
              f"margin={margin:+.3f}  coverage={100*cov:4.1f}%")
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
