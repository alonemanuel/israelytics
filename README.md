# Israelytics

Visualize data about Israeli cities on a map of Israel, with a timeline.

Pick a dataset, and the map colors every city by that dataset's value — then drag a
slider to watch it change across time. It's built to be **generic**: the map of Israel
is shared, and each dataset is just a data file. Adding a new dataset means dropping in
a JSON file — no code changes.

**Status:** working POC. Two datasets so far, both across Knesset elections 17–25
(2006–2022): **Haredi (ultra-orthodox) vote share** per city, and **Right vs Left**
(the signed bloc margin, with a per-city party breakdown on hover). They are two
*reductions of the same election results* — a good illustration that one data source
can drive many maps. More datasets (population, turnout, income, …) can be added later.

## How it works (the short version)

- A **base map** (`public/data/geo.json`) holds the geometry of every Israeli city —
  built once, shared by all datasets.
- Each **dataset** (`public/data/datasets/<id>.json`) holds values per city per
  time-step, plus how to color them.
- The website joins the two by CBS locality code and draws the map.

See [`CLAUDE.md`](./CLAUDE.md) for the architecture and the data-format contract, and
[`docs/DECISIONS.md`](./docs/DECISIONS.md) for why things are built the way they are.

## Running locally

Requires Node 18.17+ (Node 22 recommended) and Python 3.

```bash
npm install
npm run dev          # http://localhost:3000

# rebuild the data files (Python pipeline; outputs into public/data/):
python pipeline/basemap/build_geo.py               # -> public/data/geo.json
python pipeline/basemap/build_border.py            # -> public/data/border.json + water.json (run after geo)
python pipeline/datasets/haredi-vote/build.py      # -> datasets/haredi-vote.json + registers it
python pipeline/datasets/right-left-vote/build.py  # -> datasets/right-left-vote.json + registers it

# tests:
python -m pytest pipeline/tests/    # pipeline logic
npx vitest run                      # colorScale
```

## Adding a new dataset

Each dataset is a **provenance package** — its `SOURCE.md` (where the numbers came
from + the method) and its `build.py` live together so it stays reproducible.

1. `cp -r pipeline/datasets/_TEMPLATE pipeline/datasets/<id>`
2. **Raw inputs:** put newly-downloaded files in `<id>/sources/` (committed as-is) —
   *or*, if you're reusing an existing source (e.g. the Knesset results in
   `pipeline/elections/`), read it via that shared package instead of copying.
3. Fill in `<id>/SOURCE.md` — the source links, dates, and how raw → numbers.
4. Implement `<id>/build.py` to emit `public/data/datasets/<id>.json` keyed by CBS
   locality code. It registers itself and shows up in the picker automatically.
   Optionally add an `infoHe` methodology blurb (ⓘ panel) and `{v, parts}` cells
   for a per-city tooltip breakdown — both are generic, no frontend changes needed.

Worked examples: `pipeline/datasets/haredi-vote/` (own simple reduction) and
`pipeline/datasets/right-left-vote/` (reuses the shared election source + adds a
breakdown and info panel).

## Tech

Next.js (App Router, TypeScript) + D3 for the map, deployed on Vercel. Data is prepared
by a small Python pipeline. See `docs/DECISIONS.md` for why.
