"use client";

import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import type { Dataset, GeoData, PolygonCity } from "@/lib/types";
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

    const tip = d3.select(tipRef.current);
    const showTip = (html: string, ev: any) => {
      const host = svgRef.current!.parentElement!.getBoundingClientRect();
      tip.html(html).style("opacity", "1")
        .style("left", ev.clientX - host.left + 14 + "px")
        .style("top", ev.clientY - host.top + 14 + "px");
    };
    const hideTip = () => tip.style("opacity", "0");

    gRegions.selectAll("path").data(features).join("path")
      .attr("class", "region").attr("d", (d) => path(d as any))
      .attr("data-key", (d) => d.properties.key)
      .on("mousemove", (ev, d) => showTip(`<b>${d.properties.name}</b><br><span class="v"></span>`, ev))
      .on("mouseleave", hideTip);

    gDots.selectAll("circle").data(dots).join("circle")
      .attr("class", "dot").attr("data-key", (d) => d.key)
      .attr("cx", (d) => projPoint(d.lon, d.lat)[0])
      .attr("cy", (d) => projPoint(d.lon, d.lat)[1])
      .attr("r", (d) => dotR(d.weight))
      .on("mousemove", (ev, d) => showTip(`<b>${d.name}</b><br><span class="v"></span>`, ev))
      .on("mouseleave", hideTip);

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

  // Recolor + retooltip whenever dataset or timestep changes.
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const color = dataset ? makeColor(dataset.colorScale) : () => "#555";
    const valueOf = (key: string): number | null =>
      dataset?.cities[key]?.[step] ?? null;
    const fmt = (v: number | null) =>
      v == null ? "אין נתונים" : Math.round(v * 100) + "%";

    svg.selectAll<SVGPathElement, Feature>("path.region")
      .attr("fill", (d) => color(valueOf(d.properties.key)));
    svg.selectAll<SVGCircleElement, Dot>("circle.dot")
      .attr("fill", (d) => color(valueOf(d.key)))
      .attr("opacity", (d) => (valueOf(d.key) == null ? 0.35 : 0.95));

    // tooltip value injection (re-bind handlers so they read current step)
    const tip = d3.select(tipRef.current);
    const host = () => svgRef.current!.parentElement!.getBoundingClientRect();
    const bind = (sel: any, nameOf: (d: any) => string, keyOf: (d: any) => string) =>
      sel.on("mousemove", (ev: any, d: any) => {
        const r = host();
        tip.html(`<b>${nameOf(d)}</b><br>${fmt(valueOf(keyOf(d)))}`).style("opacity", "1")
          .style("left", ev.clientX - r.left + 14 + "px")
          .style("top", ev.clientY - r.top + 14 + "px");
      });
    bind(svg.selectAll("path.region"), (d: Feature) => d.properties.name, (d: Feature) => d.properties.key);
    bind(svg.selectAll("circle.dot"), (d: Dot) => d.name, (d: Dot) => d.key);
  }, [dataset, step]);

  return (
    <div className="stage">
      <svg ref={svgRef} viewBox={`0 0 ${VB} ${VB}`} preserveAspectRatio="xMidYMid meet" />
      <div className="zoomctl">
        <button onClick={() => (svgRef.current as any)?.__zoom_by?.(1.8)} title="התקרבות">+</button>
        <button onClick={() => (svgRef.current as any)?.__zoom_by?.(1 / 1.8)} title="התרחקות">−</button>
        <button onClick={() => (svgRef.current as any)?.__zoom_reset?.()} title="איפוס">⤢</button>
      </div>
      <div ref={tipRef} className="tooltip" />
    </div>
  );
}
