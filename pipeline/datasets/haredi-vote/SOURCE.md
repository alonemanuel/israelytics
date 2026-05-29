# Haredi vote share — source & method

**Dataset id:** `haredi-vote`
**Output:** `public/data/datasets/haredi-vote.json`
**Builder:** `./build.py` (reads `./sources`)

## What this is

For each Israeli locality, the share of valid votes that went to the two Haredi
(ultra-orthodox) parties — **Shas (ש"ס)** and **United Torah Judaism / Yahadut
HaTorah (ג)** — in each Knesset election from the 19th (2013) to the 25th (2022).

## Sources

The raw files in `./sources/` are the official per-locality ("לפי יישובים")
result tables published by the Israeli **Central Elections Committee**, one CSV
per election, named by Knesset number.

| File | Election | Date | Source |
|------|----------|------|--------|
| `sources/19.csv` | 19th Knesset | Jan 2013 | Central Elections Committee — per-locality results |
| `sources/20.csv` | 20th Knesset | Mar 2015 | " |
| `sources/21.csv` | 21st Knesset | Apr 2019 | " |
| `sources/22.csv` | 22nd Knesset | Sep 2019 | " |
| `sources/23.csv` | 23rd Knesset | Mar 2020 | " |
| `sources/24.csv` | 24th Knesset | Mar 2021 | " |
| `sources/25.csv` | 25th Knesset | Nov 2022 | " |

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
4. **Key by CBS locality code** (`סמל יישוב`) so the values join to `geo.json`.
   Spelling variants of the same code across elections are merged
   (`elections.merge_shares`).
5. **Skip aggregates** like `מעטפות חיצוניות` ("external envelopes" — absentee /
   military votes, not a place).

## Caveats

- **Shas is a proxy.** Shas draws some traditional (non-Haredi) Mizrahi voters, so
  this slightly over-counts the strictly-Haredi vote. It is the conventional measure.
- ~12 small Bedouin localities don't resolve to geometry and are absent from the map
  (reported by the builder); their Haredi share is ~0 regardless.
- The denominator is *valid votes in that locality*, so the share reflects the local
  electorate, not turnout.
