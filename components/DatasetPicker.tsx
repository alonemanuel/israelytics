"use client";

import type { DatasetSummary } from "@/lib/types";

export default function DatasetPicker({
  index,
  selectedId,
  onSelect,
}: {
  index: DatasetSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <label className="picker">
      <span>נתון:</span>
      <select value={selectedId ?? ""} onChange={(e) => onSelect(e.target.value)}>
        {index.map((d) => (
          <option key={d.id} value={d.id}>
            {d.titleHe}
          </option>
        ))}
      </select>
    </label>
  );
}
