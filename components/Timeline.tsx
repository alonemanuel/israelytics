"use client";

import { useCallback, useRef, useState } from "react";
import type { Timestep } from "@/lib/types";

/**
 * Horizontal time axis (footer band). RTL: oldest at the inline-start (right),
 * newest at the inline-end (left); the filled bar runs from the start to the
 * thumb. Drag the thumb, tap a tick, or use arrow keys. Built custom (not a
 * native range input) for a reliable, large touch target in RTL.
 */
export default function Timeline({
  timesteps,
  step,
  onStep,
}: {
  timesteps: Timestep[];
  step: number;
  onStep: (i: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(false);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  if (timesteps.length <= 1) return null; // snapshot dataset: no axis

  const last = timesteps.length - 1;
  const ts = timesteps[step];
  // leftFrac: 0 = left edge (newest), 1 = right edge (oldest). RTL reads right
  // (start/oldest) to left (end/newest).
  const leftFrac = (i: number) => (last - i) / last;

  const setFromClientX = useCallback(
    (clientX: number) => {
      const el = trackRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const f = Math.min(1, Math.max(0, (clientX - r.left) / r.width)); // 0 at left
      onStep(Math.round((1 - f) * last)); // left -> newest
    },
    [last, onStep]
  );

  const onPointerDown = (e: React.PointerEvent) => {
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    if (idleTimer.current) clearTimeout(idleTimer.current);
    setActive(true);
    setFromClientX(e.clientX);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (e.buttons !== 0) setFromClientX(e.clientX);
  };
  const onPointerUp = () => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => setActive(false), 700);
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    // RTL: ArrowLeft advances toward newer, ArrowRight toward older
    if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
      e.preventDefault();
      onStep(Math.min(last, step + 1));
    } else if (e.key === "ArrowDown" || e.key === "ArrowRight") {
      e.preventDefault();
      onStep(Math.max(0, step - 1));
    }
  };

  return (
    <div className={`timebar${active ? " active" : ""}`}>
      <div className="tb-now">
        <span className="tb-label">{ts.label}</span>
        {ts.sub && <span className="tb-sub">{ts.sub}</span>}
      </div>
      <div
        ref={trackRef}
        className="tb-track"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        role="slider"
        tabIndex={0}
        aria-label="ציר זמן"
        aria-valuemin={0}
        aria-valuemax={last}
        aria-valuenow={step}
        aria-valuetext={`${ts.label}${ts.sub ? " · " + ts.sub : ""}`}
        onKeyDown={onKeyDown}
      >
        <div className="tb-rail" />
        <div className="tb-fill" style={{ left: `${leftFrac(step) * 100}%`, right: 0 }} />
        {timesteps.map((t, i) => {
          const x = leftFrac(i) * 100;
          return (
            <div key={t.id} className="tb-stop" style={{ left: `${x}%` }}>
              <span className={`tb-tick${i <= step ? " past" : ""}${i === step ? " on" : ""}`} />
              <span className={`tb-num${i === step ? " on" : ""}`}>{t.id.replace(/^k/, "")}</span>
            </div>
          );
        })}
        <div className="tb-thumb" style={{ left: `${leftFrac(step) * 100}%` }} />
      </div>
    </div>
  );
}
