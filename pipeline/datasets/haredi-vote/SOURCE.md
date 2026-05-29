# Haredi vote share — source & method

**Dataset id:** `haredi-vote`
**Output:** `public/data/datasets/haredi-vote.json`
**Builder:** `./build.py` (reads `./sources`)

## What this is

For each Israeli locality, the share of valid votes that went to the two Haredi
(ultra-orthodox) parties — **Shas (ש"ס)** and **United Torah Judaism / Yahadut
HaTorah (ג)** — in each Knesset election from the **17th (2006) to the 25th (2022)**.

## Sources

The raw files in `./sources/` are official result tables from the Israeli
**Central Elections Committee**. Two granularities are mixed:

- **19th–25th**: per-locality ("לפי יישובים") CSVs, one per election, with a CBS
  code column.
- **17th & 18th**: per-**ballot-box** files (no per-locality export was available),
  aggregated up to the locality by the builder. The 18th carries a CBS code; the
  17th has only city names, so its codes are backfilled (see Method).

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

## Method (raw → numbers)

1. **Read** each CSV. Files mix UTF-8 and Windows-1255 encodings and vary their
   headers slightly; `pipeline/common/elections.py` handles both and finds columns
   by Hebrew header text, not position.
2. **Identify Haredi votes** per locality as the sum of the two ballot-letter
   columns `ש"ס` (`שס`) and `ג`. These letters are stable across elections 19–25.
   The set is defined in `elections.HAREDI_LETTERS` — edit there to change it.
3. **Compute the share** = Haredi votes ÷ `כשרים` (valid votes) for that locality.
   Localities with zero valid votes yield no value (rendered as "no data").
4. **Aggregate ballot-box sources (17th, 18th)** up to the locality before the
   share is computed: sum each party and the valid count over all ballot boxes of
   a locality. The 18th groups by its CBS code column directly; the 17th groups by
   normalized city name, then resolves that name to a CBS code via the name↔code
   pairs learned from the 19th–25th files (`elections.build_name_to_cbs`). 2006
   localities whose name doesn't resolve to a code are reported and omitted
   (~96 of ~1,210, mostly tiny/renamed places).
5. **Key by CBS locality code** (`סמל יישוב`) so the values join to `geo.json`.
   Spelling variants of the same code across elections are merged
   (`elections.merge_shares`).
6. **Skip aggregates** like `מעטפות חיצוניות` / `מעטפות כפולות` ("external/double
   envelopes" — absentee / military votes, not a place).

## Caveats

- **Shas is a proxy.** Shas draws some traditional (non-Haredi) Mizrahi voters, so
  this slightly over-counts the strictly-Haredi vote. It is the conventional measure.
- ~12 small Bedouin localities don't resolve to geometry and are absent from the map
  (reported by the builder); their Haredi share is ~0 regardless.
- The denominator is *valid votes in that locality*, so the share reflects the local
  electorate, not turnout.
