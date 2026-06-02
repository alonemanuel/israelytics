# Design system — Israelytics

## Typefaces

Two custom Hebrew typefaces, self-hosted via `next/font/local` (no Google Fonts, no layout shift).
Font files live in `app/fonts/`.

| Variable | Family | Role | Weights loaded |
|----------|--------|------|----------------|
| `--font-sans` | **NarkissTam** | UI, data, labels | 300 · 400 · 500 · 600 · 700 · 800 · 900 |
| `--font-serif` | **HadassahFriedlaender** | Editorial, display | 100 · 300 · 400 · 500 · 700 · 900 |

### Where each font is used

**Hadassah (serif)** — editorial and named-entity slots:
- Brand wordmark "ישראליטיקס" (`.wordmark`, weight 700, `--text-xl`)
- Info-panel heading `h2`
- Tooltip city name (`b` tag, weight 500)

**NarkissTam (sans)** — everything else:
- Body text, dataset picker, legend, timeline labels, map city labels, tooltip values

The rule: serif for *named things you read*, sans for *data you scan*.

### Brand mark

The mark is a **vector SVG**, not a glyph: `components/BrandMark.tsx` draws a rising
analytics trend line whose peak is a Star of David — "Israel + analytics" in one shape,
stroked in `currentColor` (so it inherits the ink accent and stays monochrome). It sizes via
`.brand .mark` (32 px desktop, 27 px mobile). On mobile the wordmark hides and the icon alone
carries the brand, freeing the bar for the dataset name and reclaiming screen for the map.

## Type scale

Defined as CSS custom properties in `:root` inside `app/globals.css`:

```css
--text-xs:   11px   /* secondary labels, legend ticks */
--text-sm:   13px   /* primary UI labels, picker, tooltip body */
--text-base: 15px   /* body / info-panel body */
--text-lg:   18px   /* — */
--text-xl:   22px   /* brand h1, info-panel h2 */
--text-2xl:  28px   /* — */
--text-3xl:  36px   /* — */
```

Always use a `--text-*` token rather than a raw `px` value. If a new size is needed, add a token.

## Colour palette

All colours are CSS custom properties that swap between light and dark themes.
See the `:root` block in `app/globals.css` for the full list; key tokens:

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg-1` | `#f4f3ef` | `#16161a` | page background |
| `--bg-2` | `#e7e6e0` | `#101015` | gradient second stop |
| `--ink` | `#1b1a17` | `#ecebe6` | primary text |
| `--muted` | `#6c6a63` | `#9b9a93` | secondary text, legend ends |
| `--surface` | `rgba(253,252,249,.74)` | `rgba(30,30,35,.6)` | glass panels |
| `--accent` | `#1c1b16` | `#edece7` | brand mark, active states (ink, not a hue) |
| `--accent-strong` | `#000000` | `#ffffff` | selected borders |
| `--land` | `#f7f5ef` | `#202026` | the landmass fill |
| `--sea` | `#e6e2d8` | `#111114` | the calm field the country floats on |
| `--water` | `#ccd1cf` | `#262c2e` | inland lakes (Kinneret, Dead Sea) — neutral gray |

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

## Layout — floating clusters, no chrome slab

The map is full-bleed; everything else floats over it as small, self-contained glass
clusters anchored to the corners — there is no full-width bar. The top row holds two
clusters: the **brand masthead card** (icon + serif wordmark + dataset caption) at the inline
start, and the **controls** (picker + theme toggle) at the inline end. The header element
itself is `pointer-events: none` so the empty middle passes clicks through to the map; each
cluster re-enables pointer events. Legend sits bottom-end, the timeline mid-end, zoom
bottom-start. Keep new UI in this corner-anchored, hugs-its-content idiom.

## Component surface — glass panels

Floating elements (brand, picker, theme, legend, timeline, info panel, tooltip, zoom) use the
`.glass` utility class (or, for the picker/theme, the same translucent surface + blur inline):

```css
.glass {
  background: var(--surface);
  backdrop-filter: blur(var(--blur)) saturate(125%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}
```

`--blur` is `22px`. Shadows are soft and diffuse (large blur, low alpha) for a quiet, lifted
feel — see the `--shadow-*` tokens; don't use hard, tight shadows.

## Spacing & radius

```
--radius-sm: 12px   tooltip, zoom buttons, small chips
--radius-md: 16px   legend, info-head
--radius-lg: 22px   brand masthead, timeline, info panel
```

No magic numbers: use the radius tokens and the `env(safe-area-inset-*)` wrappers already on
bottom-anchored elements.

## Map layer

- Projection: planar `d3.geoIdentity` with longitude×cos(lat) correction (not Mercator — see `docs/DECISIONS.md`).
- Land fill: `--land`; sea/field: `--sea`; city regions: `--map-empty` when no data. The
  landmass is *lifted off the field* with a soft, diffuse drop-shadow and a 1px hairline coast
  (`--outline`), so the country reads as a crafted object; no-data cities sit close to the land
  tone so the data clusters are what catch the eye.
- Inland water (Kinneret, Dead Sea) is its own layer drawn over the land + city fills in `--water` (a neutral cool gray — achromatic, so the only color on the map is the data) with a `--water-stroke` shoreline. Source: `public/data/water.json`. The coastline is clipped flush to the coastal cities and the Kinneret is cut out of the landmass — see `docs/DECISIONS.md`.
- City labels: HTML overlay (not SVG text), positioned in screen-px by `MapView` so they stay crisp at any zoom.
- Dot radius is driven by `weight` from `geo.json` (≈ electorate size), not the dataset value.

## Adding UI

- New floating elements should use `.glass` and anchor to the `position: absolute` stage or topbar.
- New text: pick the right font role (serif = editorial/named, sans = data/UI) and a `--text-*` size.
- New colours: add a CSS custom property with both light and dark values; don't hardcode hex.
