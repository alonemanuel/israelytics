"use client";

import { useEffect, useState } from "react";
import { useData } from "@/lib/useData";
import DatasetPicker from "@/components/DatasetPicker";
import Timeline from "@/components/Timeline";
import Legend from "@/components/Legend";
import MapView from "@/components/MapView";
import InfoButton from "@/components/InfoButton";
import ThemeToggle from "@/components/ThemeToggle";
import BrandMark from "@/components/BrandMark";

export default function Home() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { geo, border, water, index, dataset, error } = useData(selectedId);
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
      {geo ? (
        <MapView geo={geo} border={border} water={water} dataset={dataset} step={step} />
      ) : (
        !error && (
          <div className="center-msg">
            <div className="card glass">
              <div className="spinner" />
              טוען מפה…
            </div>
          </div>
        )
      )}

      {error && (
        <div className="center-msg error">
          <div className="card glass">שגיאה בטעינת הנתונים: {error}</div>
        </div>
      )}

      <header className="topbar glass">
        <div className="brand">
          <BrandMark className="mark" />
          <div className="titles">
            <h1>
              <span className="wordmark">ישראליטיקס</span>
              {dataset && <InfoButton dataset={dataset} />}
            </h1>
            {dataset?.descriptionHe && <p>{dataset.descriptionHe}</p>}
          </div>
        </div>
        <div className="topbar-actions">
          {index.length > 0 && (
            <DatasetPicker index={index} selectedId={selectedId} onSelect={setSelectedId} />
          )}
          <ThemeToggle />
        </div>
      </header>

      {dataset && (
        <Timeline timesteps={dataset.timesteps} step={step} onStep={setStep} />
      )}

      {geo && dataset && <Legend dataset={dataset} />}
    </main>
  );
}
