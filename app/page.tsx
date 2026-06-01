"use client";

import { useEffect, useState } from "react";
import { useData } from "@/lib/useData";
import DatasetPicker from "@/components/DatasetPicker";
import Timeline from "@/components/Timeline";
import Legend from "@/components/Legend";
import MapView from "@/components/MapView";
import InfoButton from "@/components/InfoButton";
import ThemeToggle from "@/components/ThemeToggle";

export default function Home() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { geo, border, index, dataset, error } = useData(selectedId);
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
        <MapView geo={geo} border={border} dataset={dataset} step={step} />
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

      <header className="masthead glass">
        <div className="brand-lockup">
          <span className="mark">י</span>
          <h1 className="eyebrow brand-name">Israelytics</h1>
        </div>
        <div className="dataset-line">
          {index.length > 0 && (
            <DatasetPicker index={index} selectedId={selectedId} onSelect={setSelectedId} />
          )}
          {dataset && <InfoButton dataset={dataset} />}
        </div>
        {dataset?.descriptionHe && <p className="teaser">{dataset.descriptionHe}</p>}
      </header>

      <div className="corner-tl">
        <ThemeToggle />
      </div>

      {dataset && (
        <Timeline timesteps={dataset.timesteps} step={step} onStep={setStep} />
      )}

      {geo && dataset && <Legend dataset={dataset} />}
    </main>
  );
}
