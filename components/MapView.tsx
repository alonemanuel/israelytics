"use client";

import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import type { Dataset, GeoData, PolygonCity, Part } from "@/lib/types";
import { cellValue, cellParts } from "@/lib/types";
import { makeColor } from "@/lib/colorScale";

const VB = 1000;
const LAT0 = 31.5;
const KX = Math.cos((LAT0 * Math.PI) / 180); // longitude aspect correction

interface Feature {
  type: "Feature";
  properties: { key: string; name: string };
  geometry: PolygonCity["geometry"];
}
interface Dot {
  key: string;
  name: string;
  lat: number;
  lon: number;
  weight: number;
}

export default function MapView({
  geo,
  dataset,
  step,
}: {
  geo: GeoData;
  dataset: Dataset | null;
  step: number;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const projRef = useRef<d3.GeoProjection | null>(null);
  const pinnedRef = useRef(false); // tooltip pinned by tap (touch)
  const selectedRef = useRef<{ name: string; key: string } | null>(null); // currently pinned city

  // Split the base map into polygon features and point dots (depends on geo only).
  const { features, dots } = useMemo(() => {
    const features: Feature[] = [];
    const dots: Dot[] = [];
    for (const [key, c] of Object.entries(geo.cities)) {
      if (c.kind === "polygon") {
        features.push({ type: "Feature", properties: { key, name: c.nameHe }, geometry: c.geometry });
      } else {
        dots.push({ key, name: c.nameHe, lat: c.lat, lon: c.lon, weight: c.weight });
      }
    }
    return { features, dots };
  }, [geo]);

  const dotR = useMemo(
    () => d3.scaleSqrt().domain([0, d3.max(dots, (d) => d.weight) || 1]).range([1.3, 9]),
    [dots]
  );

  // Draw geometry once per geo: projection fit, polygons, dots, zoom/pan.
  useEffect(() => {
    const node = svgRef.current;
    if (!node) return;
    const svg = d3.select(node);
    svg.selectAll("*").remove();
    const gZoom = svg.append("g");
    const gRegions = gZoom.append("g");
    const gDots = gZoom.append("g");

    const aspect = d3.geoTransform({
      point(this: any, lon: number, lat: number) {
        this.stream.point(lon * KX, lat);
      },
    });
    const projection = d3.geoIdentity().reflectY(true) as d3.GeoProjection;
    const path = d3.geoPath({ stream: (s) => aspect.stream(projection.stream(s)) });
    projRef.current = projection;

    const scaleGeom = (g: PolygonCity["geometry"]) => {
      const rec = (c: any): any => (typeof c[0] === "number" ? [c[0] * KX, c[1]] : c.map(rec));
      return { type: g.type, coordinates: rec(g.coordinates) } as PolygonCity["geometry"];
    };
    const fitFeats: any[] = features.map((f) => ({ type: "Feature", geometry: scaleGeom(f.geometry) }));
    dots.forEach((d) => fitFeats.push({ type: "Feature", geometry: { type: "Point", coordinates: [d.lon * KX, d.lat] } }));
    projection.fitExtent([[20, 20], [VB - 20, VB - 20]], { type: "FeatureCollection", features: fitFeats });
    const projPoint = (lon: number, lat: number) => projection([lon * KX, lat])!;

    gRegions.selectAll("path").data(features).join("path")
      .attr("class", "region").attr("d", (d) => path(d as any))
      .attr("data-key", (d) => d.properties.key);

    gDots.selectAll("circle").data(dots).join("circle")
      .attr("class", "dot").attr("data-key", (d) => d.key)
      .attr("cx", (d) => projPoint(d.lon, d.lat)[0])
      .attr("cy", (d) => projPoint(d.lon, d.lat)[1])
      .attr("r", (d) => dotR(d.weight));

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 60]).translateExtent([[0, 0], [VB, VB]])
      .on("zoom", (e) => {
        gZoom.attr("transform", e.transform.toString());
        gDots.selectAll<SVGCircleElement, Dot>("circle").attr("r", (d) => dotR(d.weight) / e.transform.k);
      });
    svg.call(zoom).on("dblclick.zoom", null);
    (node as any).__zoom_reset = () => svg.transition().duration(350).call(zoom.transform, d3.zoomIdentity);
    (node as any).__zoom_by = (f: number) => svg.transition().duration(250).call(zoom.scaleBy, f);
  }, [features, dots, dotR]);

  // Recolor + (re)bind interactions whenever dataset or timestep changes.
  useEffect(() => {
    const node = svgRef.current;
    if (!node) return;
    const svg = d3.select(node);
    const color = dataset ? makeColor(dataset.colorScale) : () => "#94a0b3";
    const tsId = dataset?.timesteps[step]?.id;
    const cellOf = (key: string) =>
      tsId != null ? (dataset?.cities[key]?.[tsId] ?? null) : null;
    const valueOf = (key: string): number | null => cellValue(cellOf(key));
    const fmt = (v: number | null) => {
      if (v == null) return "אין נתונים";
      if (dataset?.unit === "percent") return Math.round(v * 100) + "%";
      if (dataset?.unit === "margin") {
        const p = Math.round(Math.abs(v) * 100);
        if (p === 0) return "תיקו";
        return (v > 0 ? "נטייה ימינה " : "נטייה שמאלה ") + p;
      }
      return String(v);
    };
    // Render a value breakdown (e.g. parties) as labeled bars. `tag` colors the
    // bar (R/L for right-left); untagged parts get a neutral bar.
    const partsHtml = (parts: Part[] | null): string => {
      if (!parts || !parts.length) return "";
      const rows = parts
        .map((p) => {
          const pct = Math.round(p.value * 100);
          const cls = p.tag === "R" ? "r" : p.tag === "L" ? "l" : "n";
          return `<div class="part"><span class="plabel">${p.labelHe}</span>`
            + `<span class="pbar"><i class="${cls}" style="width:${Math.min(100, pct)}%"></i></span>`
            + `<span class="ppct">${pct}%</span></div>`;
        })
        .join("");
      return `<div class="parts">${rows}</div>`;
    };

    svg.selectAll<SVGPathElement, Feature>("path.region")
      .attr("fill", (d) => color(valueOf(d.properties.key)));
    svg.selectAll<SVGCircleElement, Dot>("circle.dot")
      .attr("fill", (d) => color(valueOf(d.key)))
      .attr("opacity", (d) => (valueOf(d.key) == null ? 0.4 : 0.95));

    const tip = d3.select(tipRef.current);
    const host = () => node.parentElement!.getBoundingClientRect();
    const place = (ev: any) => {
      const r = host();
      const x = ev.clientX - r.left;
      const y = ev.clientY - r.top;
      // flip away from edges so the tip stays on-screen
      const flipX = x > r.width - 180;
      tip.style("left", (flipX ? x - 14 : x + 14) + "px")
        .style("top", y + 14 + "px")
        .style("transform", flipX ? "translateX(-100%)" : "");
    };
    const render = (name: string, key: string) =>
      tip
        .html(`<b>${name}</b><br><span class="val">${fmt(valueOf(key))}</span>`
          + partsHtml(cellParts(cellOf(key))))
        .classed("show", true);
    const showFor = (name: string, key: string, ev: any) => {
      render(name, key);
      place(ev);
    };

    // keep a pinned tooltip's value current when the timestep/dataset changes
    if (pinnedRef.current && selectedRef.current) {
      render(selectedRef.current.name, selectedRef.current.key);
    }

    const bind = (sel: any, nameOf: (d: any) => string, keyOf: (d: any) => string) =>
      sel
        .on("mousemove", (ev: any, d: any) => {
          if (!pinnedRef.current) showFor(nameOf(d), keyOf(d), ev);
        })
        .on("mouseleave", () => {
          if (!pinnedRef.current) tip.classed("show", false);
        })
        .on("click", (ev: any, d: any) => {
          ev.stopPropagation();
          svg.selectAll(".sel").classed("sel", false);
          d3.select(ev.currentTarget).classed("sel", true);
          pinnedRef.current = true;
          selectedRef.current = { name: nameOf(d), key: keyOf(d) };
          showFor(nameOf(d), keyOf(d), ev);
        });

    bind(svg.selectAll("path.region"), (d: Feature) => d.properties.name, (d: Feature) => d.properties.key);
    bind(svg.selectAll("circle.dot"), (d: Dot) => d.name, (d: Dot) => d.key);

    // tap/click empty map clears the pinned selection
    svg.on("click.clear", () => {
      pinnedRef.current = false;
      selectedRef.current = null;
      tip.classed("show", false);
      svg.selectAll(".sel").classed("sel", false);
    });
  }, [dataset, step]);

  return (
    <div className="stage">
      <svg ref={svgRef} viewBox={`0 0 ${VB} ${VB}`} preserveAspectRatio="xMidYMid meet" />
      <div className="zoomctl glass">
        <button onClick={() => (svgRef.current as any)?.__zoom_by?.(1.8)} title="התקרבות" aria-label="התקרבות">+</button>
        <button onClick={() => (svgRef.current as any)?.__zoom_by?.(1 / 1.8)} title="התרחקות" aria-label="התרחקות">−</button>
        <div className="sep" />
        <button onClick={() => (svgRef.current as any)?.__zoom_reset?.()} title="איפוס תצוגה" aria-label="איפוס תצוגה">⤢</button>
      </div>
      <div ref={tipRef} className="tooltip" />
    </div>
  );
}
