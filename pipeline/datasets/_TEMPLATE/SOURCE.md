# <Dataset name> — source & method

**Dataset id:** `<id>`  (kebab-case; matches the folder name and the output filename)
**Output:** `public/data/datasets/<id>.json`
**Builder:** `./build.py` (reads `./sources`)

## What this is

<One or two sentences: what each number means, and the unit (%, count, ₪, …).>

## Sources

Put every raw file you downloaded into `./sources/` (committed as-is, never edited).

| File | What | Source (site + direct URL) | Downloaded |
|------|------|----------------------------|------------|
| `sources/<file>` | <description> | <name> — <https://…> | <YYYY-MM-DD> |

## Method (raw → numbers)

<Step by step: how the raw files become the output JSON. Encoding quirks, the
formula, what's cleaned or dropped and why. Enough that someone could redo it.>

## Caveats

<Known gaps, approximations, proxies, anything a reader should distrust.>
