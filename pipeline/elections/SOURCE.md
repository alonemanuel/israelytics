# Knesset election results — shared source

**Package:** `pipeline/elections/` (raw + this provenance note)
**Raw:** `./sources/` (committed as-is, never edited)
**Reader:** `pipeline/common/elections.py` (exposes `SOURCES_DIR`, `read_localities`)

## What this is

The official per-locality Knesset election results for the **17th (2006) through
25th (2022)** elections. This is a **shared source**: it is consumed by more than
one part of the pipeline, so it does not belong to any single dataset.

Consumers today:

- **`basemap/build_geo.py`** — uses the city *universe* and per-city `בזב`
  (eligible voters) as the dataset-independent size `weight` in `geo.json`.
- **`datasets/haredi-vote/`** — derives (Shas + UTJ) / valid votes.
- **`datasets/right-left-vote/`** — derives the right-vs-left bloc margin.

A new election-based dataset is a new *reduction* of these same files (see the
`votes` dict returned by `read_localities`), not a new copy of the raw.

## Sources

The raw files are official result tables from the Israeli **Central Elections
Committee**. Two granularities are mixed:

- **19th–25th**: per-locality ("לפי יישובים") CSVs, one per election, with a CBS
  code column.
- **17th & 18th**: per-**ballot-box** files (no per-locality export was available),
  aggregated up to the locality by the reader. The 18th carries a CBS code; the
  17th has only city names, so its codes are backfilled (see Reading).

| File | Election | Date | Granularity | Source |
|------|----------|------|-------------|--------|
| `sources/17-kalpiot.xls` | 17th Knesset | 2006 | ballot-box (.xls) | Central Elections Committee |
| `sources/18-kalpiot.csv` | 18th Knesset | 2009 | ballot-box (CSV) | " |
| `sources/19.csv` | 19th Knesset | Jan 2013 | per-locality | " |
| `sources/20.csv` | 20th Knesset | Mar 2015 | per-locality | " |
| `sources/21.csv` | 21st Knesset | Apr 2019 | per-locality | " |
| `sources/22.csv` | 22nd Knesset | Sep 2019 | per-locality | " |
| `sources/23.csv` | 23rd Knesset | Mar 2020 | per-locality | " |
| `sources/24.csv` | 24th Knesset | Mar 2021 | per-locality | " |
| `sources/25.csv` | 25th Knesset | Nov 2022 | per-locality | " |

> **Fill in the exact download URLs and the date you downloaded them.** The
> committee publishes each election under its own site (e.g. `votes25.bechirot.gov.il`).
> Replace the "Source" cells above with the precise links so this is fully traceable.

## Reading (what `read_localities` does for every consumer)

1. **Decode** each file. They mix UTF-8 and Windows-1255 encodings and vary their
   headers slightly; the reader handles both and finds columns by Hebrew header
   text, not position. Each party is a ballot-letter column (e.g. `מחל`, `שס`); the
   non-party columns (`שם ישוב`, `סמל ישוב`, `כשרים`, `מצביעים`, `בזב`, …) are fixed.
2. **Aggregate ballot-box sources (17th, 18th)** up to the locality: sum each party
   and the counts over all ballot boxes of a locality. The 18th groups by its CBS
   code column directly; the 17th groups by normalized city name, then resolves that
   name to a CBS code via the name↔code pairs learned from the 19th–25th files
   (`elections.build_name_to_cbs`). 2006 localities whose name doesn't resolve to a
   code are dropped by downstream builders and reported (~96 of ~1,210, mostly
   tiny/renamed places).
3. **Skip aggregates** like `מעטפות חיצוניות` / `מעטפות כפולות` ("external/double
   envelopes" — absentee / military votes, not a place).

Each yielded record is `{raw, cbs_code, votes, valid, voters, eligible}`. What a
dataset *does* with `votes` (which letters it sums, how it normalizes) is that
dataset's own method, documented in its own `SOURCE.md`.

## Caveats

- Party **ballot letters are reused across elections** by different parties (e.g.
  `כן` = Kadima in 2006 but National Unity in 2021–22). Any per-party logic must be
  keyed by election, not by a single global letter map.
- The denominator any dataset uses is *votes within the locality*, so shares reflect
  the local electorate, not national turnout.
