"use client";

import { useCallback, useRef, useState } from "react";
import type { Timestep } from "@/lib/types";

/**
 * Vertical timeline scrubber. Newest timestep at the top, oldest at the bottom.
 * Drag the thumb, tap a tick, or use arrow keys. Built custom (not a native
 * range input) for a reliable, large touch target in RTL.
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
  // `active` keeps the label visible during a touch drag (where :hover doesn't fire);
  // it lingers briefly after release so the final value stays readable.
  const [active, setActive] = useState(false);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  if (timesteps.length <= 1) return null; // snapshot dataset: no slider

  const last = timesteps.length - 1;
  const ts = timesteps[step];
  const topFrac = (last - step) / last; // 0 = top (newest), 1 = bottom (oldest)

  const setFromClientY = useCallback(
    (clientY: number) => {
      const el = trackRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const f = Math.min(1, Math.max(0, (clientY - r.top) / r.height));
      onStep(Math.round((1 - f) * last)); // top -> newest
    },
    [last, onStep]
  );

  const onPointerDown = (e: React.PointerEvent) => {
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    if (idleTimer.current) clearTimeout(idleTimer.current);
    setActive(true);
    setFromClientY(e.clientY);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (e.buttons !== 0) setFromClientY(e.clientY);
  };
  const onPointerUp = () => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => setActive(false), 900);
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowUp" || e.key === "ArrowRight") {
      e.preventDefault();
      onStep(Math.min(last, step + 1));
    } else if (e.key === "ArrowDown" || e.key === "ArrowLeft") {
      e.preventDefault();
      onStep(Math.max(0, step - 1));
    }
  };

  return (
    <div className={`timeline glass${active ? " active" : ""}`}>
      <div
        ref={trackRef}
        className="track"
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
        <div className="ticks">
          <div className="rail" style={{ top: 0, bottom: 0 }} />
          <div className="fill" style={{ top: `${topFrac * 100}%`, bottom: 0 }} />
          {timesteps.map((t, i) => (
            <div
              key={t.id}
              className={`tick${i <= step ? " past" : ""}`}
              style={{ position: "absolute", left: "50%", top: `${((last - i) / last) * 100}%`, transform: "translate(-50%, -50%)" }}
            />
          ))}
          <div className="thumb" style={{ top: `${topFrac * 100}%` }} />
          <div className="tlabel" style={{ top: `${topFrac * 100}%` }}>
            <b>{ts.label}</b>
            {ts.sub && <small>{ts.sub}</small>}
          </div>
        </div>
      </div>
    </div>
  );
}
