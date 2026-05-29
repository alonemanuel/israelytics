"use client";

import type { Timestep } from "@/lib/types";

export default function Timeline({
  timesteps,
  step,
  onStep,
}: {
  timesteps: Timestep[];
  step: number;
  onStep: (i: number) => void;
}) {
  if (timesteps.length <= 1) return null; // snapshot dataset: no slider
  const ts = timesteps[step];
  return (
    <div className="timeline">
      <span className="tlabel">
        {ts.label} {ts.sub && <small>· {ts.sub}</small>}
      </span>
      <input
        type="range"
        min={0}
        max={timesteps.length - 1}
        step={1}
        value={step}
        onChange={(e) => onStep(+e.target.value)}
      />
    </div>
  );
}
