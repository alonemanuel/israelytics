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
- Brand mark "י" (`font-weight: 900`, accent color, 32 px)
- Info-panel heading `h2`
- Tooltip city name (`b` tag, weight 500)

**NarkissTam (sans)** — everything else:
- Body text, dataset picker, legend, timeline labels, map city labels, tooltip values

The rule: serif for *named things you read*, sans for *data you scan*.

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
| `--surface` | `rgba(252,251,248,.82)` | `rgba(34,34,40,.66)` | glass panels |
| `--accent` | `#c2410c` | `#f97316` | brand mark, active states |
| `--accent-strong` | `#9a3412` | `#fb923c` | tooltip values, selected borders |
| `--water` | `#8fc3d0` | `#1d4f5e` | inland lakes (Kinneret, Dead Sea) |

### Neutral-first philosophy

The palette is intentionally low-chroma so the **data colours on the map carry the visual weight**. Don't introduce saturated UI colours; the accent (orange) is the only chromatic element outside the map.

## Component surface — glass panels

Floating panels (topbar, legend, timeline, info panel, tooltip) use the `.glass` utility class:

```css
.glass {
  background: var(--surface);
  backdrop-filter: blur(var(--blur)) saturate(140%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}
```

`--blur` is `16px`. Don't add `backdrop-filter` outside `.glass` — it creates new stacking contexts and is expensive.

## Spacing & radius

```
--radius-sm: 10px   pill sub-elements (timeline thumb, legend bar)
--radius-md: 14px   legend, info panel, tooltip, zoom controls
--radius-lg: 20px   topbar, timeline container
```

No magic numbers: use the radius tokens and the `env(safe-area-inset-*)` wrappers already on bottom-anchored elements.

## Map layer

- Projection: planar `d3.geoIdentity` with longitude×cos(lat) correction (not Mercator — see `docs/DECISIONS.md`).
- Land fill: `--land`; sea fill: `--sea`; city regions: `--map-empty` when no data.
- Inland water (Kinneret, Dead Sea) is its own layer drawn over the land + city fills in `--water` (a teal, kept distinct from the political-blue data colours) with a `--water-stroke` shoreline. Source: `public/data/water.json`. The coastline is clipped flush to the coastal cities and the Kinneret is cut out of the landmass — see `docs/DECISIONS.md`.
- City labels: HTML overlay (not SVG text), positioned in screen-px by `MapView` so they stay crisp at any zoom.
- Dot radius is driven by `weight` from `geo.json` (≈ electorate size), not the dataset value.

## Adding UI

- New floating elements should use `.glass` and anchor to the `position: absolute` stage or topbar.
- New text: pick the right font role (serif = editorial/named, sans = data/UI) and a `--text-*` size.
- New colours: add a CSS custom property with both light and dark values; don't hardcode hex.
