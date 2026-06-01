# Right vs Left vote — source & method

**Dataset id:** `right-left-vote`
**Output:** `public/data/datasets/right-left-vote.json`
**Builder:** `./build.py`

## What this is

For each Israeli locality, the **signed margin between the right-wing and
left-wing blocs** in each Knesset election from the **17th (2006) to the 25th
(2022)**:

```
value = (R - L) / (R + L)
```

where `R`/`L` are the locality's total votes for right-/left-bloc parties.
The value runs **−1 (entirely left, red)** to **+1 (entirely right, blue)**, with
**0 = even**. Each city also carries a **breakdown of its top parties** (vote
share + bloc tag), shown on hover.

## Source

This dataset does **not** own raw files. It is a second *reduction* of the
shared election results in **`pipeline/elections/`** (see that package's
`SOURCE.md` for the file list, granularities, encodings, and how ballot-box
sources are aggregated). The Haredi-vote dataset reduces the same source a
different way. The builder reads it via `elections.SOURCES_DIR`.

## Method (raw → numbers)

1. **Read** each election's per-locality votes via `elections.read_localities`
   (shared reader; handles encodings, column-finding, ballot-box aggregation).
2. **Combine spelling variants**: rows that resolve to the same CBS code within
   one election are summed (votes + valid), since they are one place.
3. **Classify each party into a bloc** using the per-election table
   `elections.PARTIES` (letter → name + bloc). See the table below.
4. **Compute the margin** `(R − L) / (R + L)` over the classified votes only.
   Localities with no classified votes yield no value ("no data"), never a
   misleading 0.
5. **Build the breakdown** (`elections.top_parties`): the top 6 parties by votes,
   each as `{labelHe, value = share of valid votes, tag = R/L}`, plus an
   aggregated `אחר` (other) row.
6. **Key by CBS locality code** so values join to `geo.json`.

The builder also prints national bloc shares + margin + coverage per election as
a sanity check.

## Classification: the two-bloc scheme

This dataset uses a **two-bloc** split: **every classified party is Right or
Left** — there is no "center" bucket. Per the design choice for this map:

- **Center parties → Left.** Yesh Atid, Kahol Lavan / National Unity, Kadima,
  Kulanu, Pensioners are counted as Left.
- **Arab parties → Left.** Hadash, Ta'al, Ra'am, Balad (and their joint lists).

These are genuinely contested calls; a different analyst would draw the line
elsewhere. They are made explicit here so the map is honest about its method.
Religious-right, settler/national, and secular-nationalist (Yisrael Beiteinu)
parties are **Right**; New Hope (a right-wing breakaway) is **Right**.

### Why the table is keyed per election

Ballot **letters are reused across elections by different parties**, so a single
global letter→bloc map would be silently wrong. Examples:

- `כן` = **Kadima** (2006) → Left, but **National Unity** (2021–22) → Left
- `ב` = **Jewish Home** (2009) → Right, but **Yamina** (2021) → Right
- `ט` = **National Union** (2009) → Right, but **Religious Zionism** (2022) → Right
- `ל` = **Yisrael Beiteinu** from 2009 on → Right

The authoritative table lives in code: `pipeline/common/elections.py` →
`PARTIES`. To change a classification, edit it there (one place feeds both the
margin and the breakdown) and rebuild. The blocs as currently classified:

| Election | Right (R) | Left (L) |
|----------|-----------|----------|
| 17 (2006) | Likud, Yisrael Beiteinu, Shas, UTJ, NU-NRP | Kadima, Labor, Pensioners, Meretz, UAL-Ta'al, Hadash, Balad |
| 18 (2009) | Likud, Yisrael Beiteinu, Shas, UTJ, National Union, Jewish Home | Kadima, Labor, Meretz, UAL-Ta'al, Hadash, Balad |
| 19 (2013) | Likud-Beiteinu, Shas, Jewish Home, UTJ, Otzma | Yesh Atid, Labor, Hatnuah, Meretz, Kadima, UAL-Ta'al, Hadash, Balad |
| 20 (2015) | Likud, Jewish Home, Shas, Yisrael Beiteinu, UTJ, Yachad | Zionist Union, Yesh Atid, Kulanu, Meretz, Joint List |
| 21 (Apr 2019) | Likud, Shas, UTJ, Yisrael Beiteinu, URWP, New Right, Zehut | Kahol Lavan, Labor, Meretz, Kulanu, Gesher, Hadash-Ta'al, Ra'am-Balad |
| 22 (Sep 2019) | Likud, Shas, Yisrael Beiteinu, UTJ, Yamina, Otzma | Kahol Lavan, Labor-Gesher, Democratic Union, Joint List |
| 23 (2020) | Likud, Shas, UTJ, Yisrael Beiteinu, Yamina | Kahol Lavan, Labor-Gesher-Meretz, Joint List |
| 24 (2021) | Likud, Shas, UTJ, Yamina, Yisrael Beiteinu, Religious Zionism, New Hope | Yesh Atid, Kahol Lavan, Labor, Meretz, Joint List, Ra'am |
| 25 (2022) | Likud, Religious Zionism, Shas, UTJ, Yisrael Beiteinu, Jewish Home | Yesh Atid, National Unity, Labor, Meretz, Ra'am, Hadash-Ta'al, Balad |

## Caveats

- **The bloc line is editorial.** The center→left and Arab→left choices are
  defensible but not neutral; treat the margin as "right vs everyone-else"
  shaded by those calls, not an objective constant.
- **Coverage isn't 100%.** Tiny/unidentified lists not in the table are excluded
  from both blocs (~1–5% of valid votes per election; the builder prints
  coverage). They still appear in the per-city breakdown under their ballot letter.
- **Joint lists blur sub-parties.** When parties run on a combined slate (e.g.
  the Joint List, Likud-Beiteinu) the breakdown shows the slate, not its members.
- ~12 small Bedouin localities don't resolve to geometry and are absent from the
  map (reported by the builder), same as Haredi-vote.
- The denominator for the margin is *classified bloc votes*; for the breakdown
  shares it is *valid votes* in that locality (so breakdown shares sum to ~1
  including "אחר", while R+L may be <100%).
