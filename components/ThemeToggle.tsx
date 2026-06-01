"use client";

import { useEffect, useState } from "react";

/**
 * Light/dark toggle. The choice persists in localStorage and overrides the OS
 * preference; an inline script in layout.tsx applies it pre-paint to avoid a
 * flash. Before mount we render an empty (but sized) button so server and client
 * markup match — the icon fills in once we know the resolved theme.
 */
const KEY = "israelytics-theme";
type Mode = "light" | "dark";

export default function ThemeToggle() {
  const [mode, setMode] = useState<Mode | null>(null);

  useEffect(() => {
    const stored = (localStorage.getItem(KEY) as Mode | null) ?? null;
    const system = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    setMode(stored ?? system);
  }, []);

  const toggle = () => {
    const next: Mode = mode === "dark" ? "light" : "dark";
    setMode(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* private mode / storage disabled — theme still applies for this session */
    }
  };

  const isDark = mode === "dark";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={isDark ? "מעבר למצב בהיר" : "מעבר למצב כהה"}
      title={isDark ? "מצב בהיר" : "מצב כהה"}
    >
      {mode === null ? null : isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}
