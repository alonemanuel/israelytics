# Design system — Israelytics

## Typefaces

Two custom Hebrew typefaces, self-hosted via `next/font/local` (no Google Fonts, no layout shift).
Font files live in `app/fonts/`.

| Variable | Family | Role | Weights loaded |
|----------|--------|------|----------------|
| `--font-sans` | **NarkissTam** | UI, labels, body | 300 · 400 · 500 · 600 · 700 · 800 · 900 |
| `--font-serif` | **HadassahFriedlaender** | Display / named entities | 100 · 300 · 400 · 500 · 700 · 900 |
| `--font-mono` | system monospace stack | Numbers / technical readouts | (system) |

### Where each font is used

**Hadassah (serif)** — display and named-entity slots (the editorial voice):
- Brand wordmark "ישראליטיקס" (`.wordmark`)
- The **dataset title** set large in the sidebar (`.ds-title`)
- Info-panel heading, time-axis current label (`.tb-label`), tooltip city name

**NarkissTam (sans)** — UI and prose:
- Picker, kickers, descriptions, map city labels, "no data" labels

**Monospace** (`--font-mono`, `.mono`) — every number, for a tabular, technical feel:
- Legend scale ends, time-axis tick numbers + date sub, tooltip values + percentages

The rule: **serif for named things, sans for prose, mono for numbers.**

### Brand mark

The mark is a **vector SVG**, not a glyph: `components/BrandMark.tsx` draws a rising
analytics trend line whose peak is a Star of David — "Israel + analytics" in one shape,
stroked in `currentColor` (so it inherits the ink and stays monochrome). It sits at 24 px in
the masthead beside the wordmark.

## Type scale

Defined as CSS custom properties in `:root` inside `app/globals.css`:

```css
--text-xs:   11px   /* kickers, tags, tick numbers */
--text-sm:   13px   /* picker, descriptions, tooltip body */
--text-base: 15px   /* body / info-panel body */
--text-lg:   18px   /* time-axis current label */
--text-xl:   22px   /* wordmark (mobile) */
--text-2xl:  26px   /* wordmark, info-panel h2 */
```

The sidebar **dataset title** is the one fluid exception — `clamp(30px, 3vw, 42px)` — because
it is the page's typographic hero and must scale with the viewport. Otherwise use a `--text-*`
token rather than a raw `px` value; if a new fixed size is needed, add a token.

## Colour palette

All colours are CSS custom properties that swap between light and dark themes.
See the `:root` block in `app/globals.css` for the full list; key tokens:

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg-1` | `#f1ede2` | `#121110` | paper (page + map canvas) |
| `--panel` | `#f6f3ea` | `#1a1813` | sidebar + info panel |
| `--ink` | `#16140e` | `#ece7da` | primary text, ink rules |
| `--muted` | `#6e695b` | `#8e8779` | secondary text, numbers |
| `--rule` | `rgba(ink,.14)` | `rgba(ink,.13)` | hairline rules |
| `--rule-mid` | `rgba(ink,.30)` | `rgba(ink,.26)` | control borders, ticks |
| `--rule-strong` | `--ink` | `--ink` | bold band rules (masthead/time-axis/divider) |
| `--accent` | `= --ink` | `= --ink` | active states (ink, not a hue) |
| `--land` | `#e7e2d4` | `#232019` | the landmass fill |
| `--coast` | `rgba(ink,.55)` | `rgba(ink,.42)` | the hairline coastline |
| `--water` | `#cdd1ca` | `#262b2c` | inland lakes (Kinneret, Dead Sea) — neutral gray |

### Monochrome shell — color only from the data

The entire UI is **achromatic** (black/white/grays). `--accent`/`--accent-strong` are ink, not
a hue, so the brand mark, focus rings, active/selected states and the timeline fill all read as
ink; inland water is a neutral gray. The **only** color on screen comes from the data layer.
Never introduce a chromatic UI color — if you reach for one, it belongs to the data, not the
chrome.

### Data palette — `EarthDiv`

The signature data divergence is `EarthDiv` (defined in `lib/colorScale.ts`): **earth-purple**
at the low pole, a warm neutral midpoint, **earth-orange** at the high pole. Diverging datasets
(e.g. right-vs-left: purple = left/−1, orange = right/+1) use it; the tooltip breakdown bars
mirror the poles (`i.l` purple, `i.r` orange). Sequential datasets pick a single d3 ramp
(e.g. `haredi-vote` → `Purples`).

## Layout — the broadsheet grid

The app is a flat, ruled **data broadsheet**, not a map with floating panels. `main` is a CSS
grid of three stacked zones separated by **bold ink rules** (`--rule-strong`):

```
┌───────────────────────────────────────────────┐
│  MASTHEAD   wordmark · tag        picker · ☾   │  height 58px, bold bottom rule
├──────────────────────┬────────────────────────┤
│                      │  SIDEBAR (right, RTL)   │
│   MAP CANVAS (left)  │  kicker / big title /   │  hairline-ruled divider between
│   line-drawn country │  description / legend   │
├──────────────────────┴────────────────────────┤
│  TIME AXIS   17 ─●───────── 25   הכנסת ה-25     │  bold top rule, horizontal scrubber
└───────────────────────────────────────────────┘
```

The sidebar is the **typographic hero**: a small tracked `.kicker` (with a leading rule), the
dataset title set large in serif, the description, then the legend. On mobile the workspace
collapses to one column (map full-bleed), the sidebar becomes a compact legend card pinned
top-start, and the picker carries the dataset name. Keep new chrome inside this banded,
ruled grid — not as floating glass.

## Component surface — flat, ruled, no glass

There is **no glass, blur, or soft shadow.** Surfaces are flat fills (`--bg-1` / `--panel`)
separated by rules and hairline borders:

- **Bands** (masthead, time axis, sidebar divider) use a 1.5px `--rule-strong` ink rule.
- **Controls / cards** (picker, theme toggle, zoom, legend bar, info panel) use a 1px
  `--rule-mid` or `--rule-strong` border, no shadow.
- The tooltip is the one exception — a solid ink chip with a soft drop-shadow, since it floats
  over the map.

## Spacing & radius

```
--radius-sm: 4px   controls, zoom, tooltip, info chips
--radius-md: 6px   (reserved)
```

Corners are nearly square — this is print, not a glass app. Use the radius tokens; don't
invent rounder values.

## Map layer

- Projection: planar `d3.geoIdentity` with longitude×cos(lat) correction (not Mercator — see `docs/DECISIONS.md`).
- **Flat, line-drawn country:** land fill `--land`, a crisp 1.25px `--coast` hairline, **no
  drop-shadow**, on the paper canvas (`--bg-1`). City regions are `--map-empty` when no data —
  a tone close to the land, so the data clusters are what read.
- Inland water (Kinneret, Dead Sea) is its own layer drawn over the land + city fills in `--water` (a neutral gray — achromatic, so the only color on the map is the data) with a `--water-stroke` shoreline. Source: `public/data/water.json`. The coastline is clipped flush to the coastal cities and the Kinneret is cut out of the landmass — see `docs/DECISIONS.md`.
- City labels: HTML overlay (not SVG text), positioned in screen-px by `MapView` so they stay crisp at any zoom.
- Dot radius is driven by `weight` from `geo.json` (≈ electorate size), not the dataset value.

## Adding UI

- New chrome belongs in the banded grid (masthead / sidebar / time axis) as a flat, ruled
  surface — not a floating panel. Separate zones with `--rule-strong`, details with `--rule`.
- New text: pick the right font role (serif = named/display, sans = prose, mono = numbers) and
  a `--text-*` size.
- New colours: add a CSS custom property with both light and dark values; don't hardcode hex.
