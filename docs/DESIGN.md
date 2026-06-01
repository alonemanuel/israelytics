# Design system — Israelytics

The look is **editorial and type-led**, in the spirit of Hebrew type foundries
(Hagilda, Fontef): flat paper surfaces, hairline rules, a confident serif display,
and generous whitespace — so the **data colours on the map carry the visual weight**.
Chrome is quiet; type is the interface.

## Typefaces

Two custom Hebrew typefaces, self-hosted via `next/font/local` (no Google Fonts, no layout shift).
Font files live in `app/fonts/`.

| Variable | Family | Role | Weights loaded |
|----------|--------|------|----------------|
| `--font-sans` | **NarkissTam** | UI, data, labels | 300 · 400 · 500 · 600 · 700 · 800 · 900 |
| `--font-serif` | **HadassahFriedlaender** | Editorial, display | 100 · 300 · 400 · 500 · 700 · 900 |

### Where each font is used

**Hadassah (serif)** — editorial display and named-entity slots:
- Brand mark "י" (`font-weight: 900`, accent colour) in the masthead lockup
- **Masthead headline** — the dataset title, set large (`--text-2xl`, weight 500). This is
  the typographic hero of the page *and* the dataset picker (see below).
- Info-panel heading `h2`
- Tooltip city name (`b` tag, weight 500, `--text-lg`)

**NarkissTam (sans)** — everything else:
- Body text, teaser line, legend, timeline labels, map city labels, tooltip values,
  and the tracked-out Latin **eyebrow** (`Israelytics`).

The rule: **serif for named things you read** (the dataset, a city), **sans for data you scan**.

### The masthead is the picker

There is no separate "title" and "dropdown". The dataset `<select>` is styled *as* the
serif headline (transparent, borderless, big, with a slim chevron) — choosing a dataset
and reading its name are the same element. Above it sits a small tracked-out Latin
eyebrow (`Israelytics`, `--track-wide`, uppercase, muted) with the serif "י" mark; below
it, the dataset's `descriptionHe` as a muted teaser. The masthead **hugs its content** in
the top-start corner — it is a card, not a full-width bar.

## Type scale

Defined as CSS custom properties in `:root` inside `app/globals.css`:

```css
--text-xs:   11px   /* tracked eyebrows, legend ticks/ends */
--text-sm:   13px   /* primary UI labels, teaser, tooltip body */
--text-base: 15px   /* body / info-panel body */
--text-lg:   19px   /* tooltip city name */
--text-xl:   24px   /* info-panel h2 */
--text-2xl:  30px   /* masthead headline (the dataset title) */
--text-3xl:  42px   /* display reserve */
```

Letter-spacing is also tokenised — use these, not raw values:

```css
--track-tight: -0.018em   /* large serif display (headline, h2, city name) */
--track-wide:   0.22em    /* small uppercase Latin eyebrows */
```

Always use a `--text-*` / `--track-*` token rather than a raw value. If a new size is
needed, add a token. Numeric data uses `font-variant-numeric: tabular-nums` (legend
ends, tooltip values, timeline label).

## Colour palette

All colours are CSS custom properties that swap between light and dark themes.
See the `:root` block in `app/globals.css` for the full list; key tokens:

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg-1` | `#f5f3ec` | `#16161a` | page background |
| `--bg-2` | `#eae7dd` | `#0f0f13` | gradient second stop |
| `--ink` | `#1a1813` | `#ecebe6` | primary text |
| `--muted` | `#76736a` | `#9b9890` | secondary text, teaser, eyebrows |
| `--faint` | `#a7a397` | `#6c6a63` | chevron, lowest-emphasis marks |
| `--surface` | `rgba(250,248,243,.86)` | `rgba(30,30,35,.78)` | paper panels |
| `--hairline` | `rgba(26,24,19,.12)` | `rgba(255,255,255,.13)` | thin dividers / rails |
| `--accent` | `#bb3f12` | `#f97316` | brand mark, active states |
| `--accent-strong` | `#983311` | `#fb923c` | tooltip values, selected borders |

### Neutral-first philosophy

The palette is intentionally low-chroma so the **data colours on the map carry the visual
weight**. Don't introduce saturated UI colours; the terracotta accent is the only chromatic
element outside the map, and it is used sparingly (the mark, hover/active, the timeline fill).

## Component surface — flat paper, not frosted glass

Floating panels (masthead, legend, timeline, info panel, zoom controls, theme toggle) use
the `.glass` utility — but the look is **flat paper with a hairline edge**, only a whisper
of blur, not a heavy frosted slab:

```css
.glass {
  background: var(--surface);                 /* ~0.8 opacity paper */
  backdrop-filter: blur(var(--blur)) saturate(125%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);               /* soft, low — see tokens */
}
```

`--blur` is `11px` (down from a heavy frost). Shadows are deliberately light. Don't add
`backdrop-filter` outside `.glass` / the standalone theme toggle — it creates new stacking
contexts (and is the containing block that forces the info panel to be portaled to `<body>`).

Hairline rules (`--hairline`) separate regions *inside* a panel (legend's no-data row, the
timeline rail) instead of nested boxes or heavy borders.

## Spacing & radius

```
--radius-sm: 7px    tooltip, zoom buttons
--radius-md: 11px   legend, info panel, zoom-control housing
--radius-lg: 16px   masthead, timeline container
```

Radii are restrained (more "printed", less pill). No magic numbers: use the radius tokens
and the `env(safe-area-inset-*)` wrappers already on corner-anchored elements.

## Map layer

- Projection: planar `d3.geoIdentity` with longitude×cos(lat) correction (not Mercator — see `docs/DECISIONS.md`).
- Land fill: `--land`; sea fill: `--sea`; city regions: `--map-empty` when no data.
- City labels: HTML overlay (not SVG text), positioned in screen-px by `MapView` so they stay crisp at any zoom.
- Dot radius is driven by `weight` from `geo.json` (≈ electorate size), not the dataset value.

## Adding UI

- New floating elements should use `.glass` and anchor to the `position: absolute` stage.
  Prefer hugging content over full-width bars.
- New text: pick the right font role (**serif = editorial/named, sans = data/UI**), a
  `--text-*` size, and a `--track-*` if it's display or an eyebrow. Numbers get tabular figures.
- New colours: add a CSS custom property with both light and dark values; don't hardcode hex.
