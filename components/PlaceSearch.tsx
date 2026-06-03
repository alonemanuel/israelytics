"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { GeoData } from "@/lib/types";

interface Item { key: string; name: string; weight: number; }

/** Strip quotes/gershayim and collapse whitespace so "תל אביב" ≈ "תל-אביב" etc. */
const norm = (s: string) => s.replace(/[״׳"'`\-]/g, "").replace(/\s+/g, " ").trim();

const MAX = 8; // results shown

/**
 * Autocomplete search over the basemap's cities. Picking a result asks the map
 * to zoom in on that city and select it (via the `onPick` callback, by CBS key).
 */
export default function PlaceSearch({
  geo,
  onPick,
}: {
  geo: GeoData;
  onPick: (key: string) => void;
}) {
  // all cities, heaviest first — so a prefix tie surfaces the bigger town
  const items = useMemo<Item[]>(() => {
    const list: Item[] = [];
    for (const [key, c] of Object.entries(geo.cities)) list.push({ key, name: c.nameHe, weight: c.weight });
    list.sort((a, b) => b.weight - a.weight);
    return list;
  }, [geo]);

  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const results = useMemo<Item[]>(() => {
    const nq = norm(q);
    if (!nq) return [];
    const starts: Item[] = [];
    const contains: Item[] = [];
    for (const it of items) {
      const n = norm(it.name);
      if (n.startsWith(nq)) starts.push(it);
      else if (n.includes(nq)) contains.push(it);
    }
    return [...starts, ...contains].slice(0, MAX);
  }, [q, items]);

  // keep the active row in range as results change
  useEffect(() => { setActive(0); }, [q]);

  const pick = (it: Item | undefined) => {
    if (!it) return;
    setQ(it.name);
    setOpen(false);
    inputRef.current?.blur();
    onPick(it.key);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); setActive((i) => Math.min(i + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); pick(results[active]); }
    else if (e.key === "Escape") { setOpen(false); inputRef.current?.blur(); }
  };

  const showList = open && results.length > 0;

  return (
    <div
      className="search"
      ref={boxRef}
      onBlur={(e) => { if (!boxRef.current?.contains(e.relatedTarget as Node)) setOpen(false); }}
    >
      <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
        <line x1="16.5" y1="16.5" x2="21" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        ref={inputRef}
        type="text"
        value={q}
        placeholder="חיפוש יישוב"
        aria-label="חיפוש יישוב"
        autoComplete="off"
        role="combobox"
        aria-expanded={showList}
        aria-controls="search-list"
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {q && (
        <button className="search-clear" aria-label="ניקוי" onClick={() => { setQ(""); setOpen(false); inputRef.current?.focus(); }}>
          ×
        </button>
      )}
      {showList && (
        <ul className="search-list glass" id="search-list" role="listbox">
          {results.map((it, i) => (
            <li
              key={it.key}
              role="option"
              aria-selected={i === active}
              className={i === active ? "active" : undefined}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => { e.preventDefault(); pick(it); }}
            >
              {it.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
