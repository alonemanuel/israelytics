"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import type { Dataset } from "@/lib/types";

// Render markdown-lite (the subset datasets use in `infoHe`): blank-line
// paragraphs, "- " bullet lists, and **bold** inline. Kept tiny on purpose —
// the info text is curated by the pipeline, not arbitrary user input.
function renderBold(text: string, keyBase: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((seg, i) =>
    seg.startsWith("**") && seg.endsWith("**") ? (
      <strong key={`${keyBase}-${i}`}>{seg.slice(2, -2)}</strong>
    ) : (
      <span key={`${keyBase}-${i}`}>{seg}</span>
    )
  );
}

function MarkdownLite({ text }: { text: string }) {
  const blocks = text.split(/\n\n+/);
  return (
    <>
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        if (lines.every((l) => l.startsWith("- "))) {
          return (
            <ul key={bi}>
              {lines.map((l, li) => (
                <li key={li}>{renderBold(l.slice(2), `${bi}-${li}`)}</li>
              ))}
            </ul>
          );
        }
        return <p key={bi}>{renderBold(block, String(bi))}</p>;
      })}
    </>
  );
}

/** ⓘ button that opens a panel with the dataset's reader-facing methodology
 * (`infoHe`). Renders nothing when the dataset has no info text. */
export default function InfoButton({ dataset }: { dataset: Dataset }) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const info = dataset.infoHe ?? dataset.info;

  useEffect(() => setMounted(true), []);

  // close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!info) return null;

  // The overlay is portaled to <body> so it escapes the header's
  // backdrop-filter, which would otherwise be the containing block for our
  // position:fixed panel and pin it to the header instead of the viewport.
  const overlay = open && (
    <div dir="rtl">
      <div className="info-scrim" onClick={() => setOpen(false)} />
      <div className="info-panel" role="dialog" aria-modal="true">
        <div className="info-head">
          <h2>{dataset.titleHe}</h2>
          <button className="info-close" onClick={() => setOpen(false)} aria-label="סגירה">
            ✕
          </button>
        </div>
        <div className="info-body">
          <MarkdownLite text={info} />
        </div>
      </div>
    </div>
  );

  return (
    <>
      <button
        className="info-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="הסבר על הנתון"
        aria-expanded={open}
        title="הסבר על הנתון"
      >
        ⓘ
      </button>
      {mounted && overlay ? createPortal(overlay, document.body) : null}
    </>
  );
}
