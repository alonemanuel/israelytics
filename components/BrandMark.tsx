/**
 * Israelytics brand mark — a vectoric "Israel + analytics" glyph.
 *
 * A rising data trend (analytics) that culminates in a Star of David (Israel):
 * the line climbs from the lower-right to the upper-left (the RTL reading
 * direction), with circular data points at each vertex and the peak rendered as
 * the star. Monochrome — drawn entirely in `currentColor`, so it inherits the
 * UI ink and the only colors on screen stay the data's.
 */
export default function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label="ישראליטיקס"
    >
      {/* rising trend line (analytics), climbing toward the upper-left */}
      <path d="M20.5 17.5 L15 13 L10.5 14.5 L6.5 7" />
      {/* data points along the trend */}
      <circle cx="20.5" cy="17.5" r="1.15" fill="currentColor" stroke="none" />
      <circle cx="15" cy="13" r="1.15" fill="currentColor" stroke="none" />
      <circle cx="10.5" cy="14.5" r="1.15" fill="currentColor" stroke="none" />
      {/* the peak data point is a Star of David (Israel) — two overlaid triangles */}
      <path d="M6.5 3.6 L3.42 8.95 L9.58 8.95 Z" />
      <path d="M6.5 10.3 L3.42 4.95 L9.58 4.95 Z" />
    </svg>
  );
}
