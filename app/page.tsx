"use client";

import { useEffect, useState } from "react";
import { useData } from "@/lib/useData";
import DatasetPicker from "@/components/DatasetPicker";
import Timeline from "@/components/Timeline";
import Legend from "@/components/Legend";
import MapView from "@/components/MapView";

export default function Home() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { geo, index, dataset, error } = useData(selectedId);
  const [step, setStep] = useState(0);

  // default to the first dataset once the registry loads
  useEffect(() => {
    if (!selectedId && index.length) setSelectedId(index[0].id);
  }, [index, selectedId]);

  // when a dataset loads, jump the slider to its most recent timestep
  useEffect(() => {
    if (dataset) setStep(dataset.timesteps.length - 1);
  }, [dataset]);

  return (
    <main dir="rtl">
      <header>
        <div className="titles">
          <h1>Israelytics</h1>
          {dataset?.descriptionHe && <p>{dataset.descriptionHe}</p>}
        </div>
        {index.length > 0 && (
          <DatasetPicker index={index} selectedId={selectedId} onSelect={setSelectedId} />
        )}
      </header>

      {dataset && (
        <div className="controls">
          <Timeline timesteps={dataset.timesteps} step={step} onStep={setStep} />
        </div>
      )}

      {error && <div className="error">שגיאה בטעינת הנתונים: {error}</div>}

      {geo ? (
        <>
          <MapView geo={geo} dataset={dataset} step={step} />
          {dataset && <Legend dataset={dataset} />}
        </>
      ) : (
        !error && <div className="loading">טוען מפה…</div>
      )}
    </main>
  );
}
