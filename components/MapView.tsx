"use client";

import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import type { BorderGeometry, Dataset, GeoData, PolygonCity, Part, WaterData } from "@/lib/types";
import { cellValue, cellParts } from "@/lib/types";
import { makeColor } from "@/lib/colorScale";

const VB = 1000;
const LAT0 = 31.5;
const KX = Math.cos((LAT0 * Math.PI) / 180); // longitude aspect correction

/** Project a point that lives in the zoomed <g>'s local coords to stage pixels. */
function toStagePx(gNode: SVGGElement, host: DOMRect, x: number, y: number): [number, number] {
  const m = gNode.getScreenCTM()!;
  return [m.a * x + m.c * y + m.e - host.left, m.b * x + m.d * y + m.f - host.top];
}

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
  border,
  water,
  dataset,
  step,
}: {
  geo: GeoData;
  border: BorderGeometry | null;
  water: WaterData;
  dataset: Dataset | null;
  step: number;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const labelLayerRef = useRef<HTMLDivElement | null>(null); // screen-space city labels
  const projRef = useRef<d3.GeoProjection | null>(null);
  const gZoomRef = useRef<SVGGElement | null>(null); // the zoom/pan <g>, for screen projection
  const anchorsRef = useRef<Map<string, [number, number]>>(new Map()); // city key -> centroid in g-coords
  const pinnedRef = useRef(false); // tooltip pinned by tap (touch)
  const selectedRef = useRef<{ name: string; key: string } | null>(null); // currently pinned city
  const followTipRef = useRef<(() => void) | null>(null); // repositions pinned tip at its city

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
    gZoomRef.current = gZoom.node();
    const gLand = gZoom.append("g").attr("class", "land");
    const gRegions = gZoom.append("g");
    const gWater = gZoom.append("g").attr("class", "water");
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
    // fit to the border too (it contains every city, so it's the true extent)
    if (border) fitFeats.push({ type: "Feature", geometry: scaleGeom(border as PolygonCity["geometry"]) });
    // and to the water (the Dead Sea reaches a touch past the eastern border)
    water.forEach((w) => fitFeats.push({ type: "Feature", geometry: scaleGeom(w.geometry as PolygonCity["geometry"]) }));
    projection.fitExtent([[20, 20], [VB - 20, VB - 20]], { type: "FeatureCollection", features: fitFeats });
    const projPoint = (lon: number, lat: number) => projection([lon * KX, lat])!;

    // National silhouette: a single dissolved landmass (built by build_border.py),
    // drawn beneath the city fills. Gives a clean filled country with one crisp
    // coastline + drop-shadow over the "sea". Falls back to the union of city
    // polygons if the border file didn't load.
    gLand.append("path")
      .attr("class", "landmass")
      .attr("d", path((border ?? { type: "FeatureCollection", features }) as any));

    gRegions.selectAll("path").data(features).join("path")
      .attr("class", "region").attr("d", (d) => path(d as any))
      .attr("data-key", (d) => d.properties.key);

    // Inland water (Kinneret + Dead Sea), drawn over the land + city fills so the
    // lakes always read as water with a clean shoreline. Non-interactive.
    gWater.selectAll("path").data(water).join("path")
      .attr("class", "lake")
      .attr("d", (d) => path({ type: "Feature", geometry: d.geometry } as any));

    gDots.selectAll("circle").data(dots).join("circle")
      .attr("class", "dot").attr("data-key", (d) => d.key)
      .attr("cx", (d) => projPoint(d.lon, d.lat)[0])
      .attr("cy", (d) => projPoint(d.lon, d.lat)[1])
      .attr("r", (d) => dotR(d.weight));

    // City-name labels. Computed once in base coords, then positioned in real
    // pixels on each zoom/resize by projecting through the live transform. This
    // keeps them crisp and legibly sized on every device, with weight-priority
    // collision so they never overlap. (Rendering them inside the zoomed <g> made
    // text tiny on mobile and broke kerning at high zoom.)
    interface LabelPt { key: string; cx: number; cy: number; name: string; weight: number; }
    const labelPts: LabelPt[] = [];
    features.forEach((f) => {
      const [cx, cy] = path.centroid(f as any);
      if (Number.isFinite(cx) && Number.isFinite(cy))
        labelPts.push({ key: f.properties.key, cx, cy, name: f.properties.name, weight: geo.cities[f.properties.key]?.weight ?? 0 });
    });
    dots.forEach((d) => {
      const [cx, cy] = projPoint(d.lon, d.lat);
      labelPts.push({ key: d.key, cx, cy, name: d.name, weight: d.weight });
    });
    labelPts.sort((a, b) => b.weight - a.weight); // biggest cities claim space first
    // anchor each city's centroid so a pinned tooltip can follow it on zoom/pan
    anchorsRef.current = new Map(labelPts.map((p) => [p.key, [p.cx, p.cy] as [number, number]]));

    const layer = d3.select(labelLayerRef.current!);
    const FONT = 13, CHAR_W = 7.4, PAD_X = 7, PAD_Y = 6; // px box estimate for collision
    const LABEL_W0 = 150000; // weight gate at k=1 (~top 8 cities); eases as you zoom in
    const placeLabels = (t: d3.ZoomTransform) => {
      const ctm = gZoom.node()!.getScreenCTM();
      if (!ctm || !node.parentElement) return;
      const host = node.parentElement.getBoundingClientRect();
      const minW = LABEL_W0 / t.k;
      const placed: { l: number; t: number; r: number; b: number }[] = [];
      const shown: (LabelPt & { x: number; y: number })[] = [];
      for (const p of labelPts) {
        if (p.weight < minW) break; // sorted desc — nothing lighter qualifies either
        const x = ctm.a * p.cx + ctm.c * p.cy + ctm.e - host.left;
        const y = ctm.b * p.cx + ctm.d * p.cy + ctm.f - host.top;
        if (x < -60 || y < -20 || x > host.width + 60 || y > host.height + 20) continue;
        const hw = (p.name.length * CHAR_W) / 2 + PAD_X;
        const hh = FONT / 2 + PAD_Y;
        const box = { l: x - hw, t: y - hh, r: x + hw, b: y + hh };
        if (placed.some((q) => box.l < q.r && box.r > q.l && box.t < q.b && box.b > q.t)) continue;
        placed.push(box);
        shown.push({ ...p, x, y });
      }
      layer.selectAll<HTMLDivElement, LabelPt & { x: number; y: number }>("div.city-label")
        .data(shown, (d: any) => d.key)
        .join((en) => en.append("div").attr("class", "city-label").text((d) => d.name))
        .style("transform", (d) => `translate(${d.x}px,${d.y}px) translate(-50%,-50%)`);
    };

    // Keep a pinned tooltip glued to its city as the map moves: project the city's
    // anchor to stage pixels and reposition the tip there (hide it if it scrolls
    // off-stage). Positioning only — the tip's text is owned by the recolor effect.
    const followPinnedTip = () => {
      const sel = selectedRef.current;
      const g = gZoomRef.current;
      if (!pinnedRef.current || !sel || !g || !node.parentElement) return;
      const a = anchorsRef.current.get(sel.key);
      const tipEl = tipRef.current;
      if (!a || !tipEl) return;
      const host = node.parentElement.getBoundingClientRect();
      const [x, y] = toStagePx(g, host, a[0], a[1]);
      const off = x < 0 || y < 0 || x > host.width || y > host.height;
      tipEl.classList.toggle("show", !off);
      if (off) return;
      const flipX = x > host.width - 180;
      tipEl.style.left = (flipX ? x - 14 : x + 14) + "px";
      tipEl.style.top = y + 14 + "px";
      tipEl.style.transform = flipX ? "translateX(-100%)" : "";
    };
    followTipRef.current = followPinnedTip;

    const render = (t: d3.ZoomTransform) => {
      gZoom.attr("transform", t.toString());
      gDots.selectAll<SVGCircleElement, Dot>("circle").attr("r", (d) => dotR(d.weight) / t.k);
      placeLabels(t);
      followPinnedTip();
    };

    // Momentum / fling + rubber-band: d3.zoom has no inertia and, with a hard
    // translateExtent, no over-pan either — so at k=1 (whole country fills the
    // frame) the map is locked and a fling has nowhere to go. We instead let the
    // map be pulled/flung past its bounds (padded translateExtent) and then ease
    // it back to the in-bounds fit when the gesture settles, like a native map.
    //
    // Flow: through a pan we track velocity with a time-aware exponential filter
    // (below) so it remembers the throw even when the final pointer samples are
    // slow/sparse; on release we damp it by any pause before lifting, coast with
    // decaying velocity, then spring back to the constrained transform. Velocity is
    // in viewBox units/ms; programmatic moves (sourceEvent == null) don't feed it.
    const TIGHT: [[number, number], [number, number]] = [[0, 0], [VB, VB]];
    const PAD = VB * 0.55; // how far past the edge the map can be pulled/flung
    let momentumRAF = 0;
    let vx = 0, vy = 0;                              // smoothed pan velocity, units/ms
    let prevS: { t: number; x: number; y: number; k: number } | null = null;
    let lastMoveT = 0;
    const VEL_TAU = 50;       // ms; velocity smoothing constant (remembers the throw)
    const FRICTION = 0.95, FLING_MIN = 0.04, STOP_MIN = 0.015; // tuned by feel
    const stopMomentum = () => { if (momentumRAF) { cancelAnimationFrame(momentumRAF); momentumRAF = 0; } };

    // Clamp `t` so the viewport (the svg's viewBox extent) stays within `bounds`
    // — d3's own constrain math, which (unlike interactive drags) it does NOT
    // apply to programmatic zoom.transform calls, so the momentum loop must do it
    // itself. Used with PADDED to wall the fling, and with TIGHT to snap home.
    const PADDED: [[number, number], [number, number]] = [[-PAD, -PAD], [VB + PAD, VB + PAD]];
    const constrainTo = (t: d3.ZoomTransform, b: [[number, number], [number, number]]): d3.ZoomTransform => {
      const dx0 = t.invertX(TIGHT[0][0]) - b[0][0];
      const dx1 = t.invertX(TIGHT[1][0]) - b[1][0];
      const dy0 = t.invertY(TIGHT[0][1]) - b[0][1];
      const dy1 = t.invertY(TIGHT[1][1]) - b[1][1];
      return t.translate(
        dx1 > dx0 ? (dx0 + dx1) / 2 : Math.min(0, dx0) || Math.max(0, dx1),
        dy1 > dy0 ? (dy0 + dy1) / 2 : Math.min(0, dy0) || Math.max(0, dy1)
      );
    };
    const springBack = () => {
      const t = d3.zoomTransform(node), target = constrainTo(t, TIGHT);
      if (Math.abs(target.x - t.x) < 0.5 && Math.abs(target.y - t.y) < 0.5) return; // already fit
      svg.transition().duration(420).ease(d3.easeCubicOut).call(zoom.transform, target);
    };

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 60])
      .translateExtent(PADDED) // allow over-pan; spring-back fixes it on release
      .on("start", (e) => { if (e.sourceEvent) { stopMomentum(); svg.interrupt(); vx = vy = 0; prevS = null; } })
      .on("zoom", (e) => {
        render(e.transform);
        if (!e.sourceEvent) return;
        // Track velocity with a time-aware exponential filter so it remembers the
        // throw: the fast part of a flick survives even when the final samples are
        // slow/sparse (which a fixed trailing window would average away to ~0).
        const now = performance.now(), t = e.transform;
        if (prevS && t.k === prevS.k) {
          const dt = now - prevS.t;
          if (dt > 100) { vx = vy = 0; }            // a pause mid-drag = a fresh start
          else if (dt > 0) {
            const a = 1 - Math.exp(-dt / VEL_TAU);
            vx += a * ((t.x - prevS.x) / dt - vx);
            vy += a * ((t.y - prevS.y) / dt - vy);
          }
        } else {
          vx = vy = 0;                              // first sample, or a scale change
        }
        prevS = { t: now, x: t.x, y: t.y, k: t.k };
        lastMoveT = now;
      })
      .on("end", (e) => {
        if (!e.sourceEvent) return;
        const now = performance.now();
        // Bleed the fling off by how long the pointer sat still before lifting,
        // rather than a hard cutoff: people routinely decelerate/hold a beat before
        // releasing. Normal release latency (≤ GRACE) keeps full speed; a deliberate
        // hold decays to ~0 and so won't fling.
        const GRACE = 40, TAU = 75;
        const damp = Math.exp(-Math.max(0, now - lastMoveT - GRACE) / TAU);
        vx *= damp; vy *= damp;
        if (Math.hypot(vx, vy) < FLING_MIN) { springBack(); return; }
        let prev = now;
        const tick = (now: number) => {
          const dt = Math.min(now - prev, 40); prev = now;
          const decay = Math.pow(FRICTION, dt / 16.67);
          vx *= decay; vy *= decay;
          if (Math.hypot(vx, vy) < STOP_MIN) { momentumRAF = 0; springBack(); return; }
          const t0 = d3.zoomTransform(node);
          // zoom.transform doesn't enforce translateExtent, so clamp to PADDED here.
          const nt = constrainTo(d3.zoomIdentity.translate(t0.x + vx * dt, t0.y + vy * dt).scale(t0.k), PADDED);
          svg.call(zoom.transform, nt);
          if (Math.abs(nt.x - t0.x) < 0.01) vx = 0; // hit the overscroll wall — stop axis
          if (Math.abs(nt.y - t0.y) < 0.01) vy = 0;
          momentumRAF = requestAnimationFrame(tick);
        };
        momentumRAF = requestAnimationFrame(tick);
      });
    svg.call(zoom).on("dblclick.zoom", null);
    (node as any).__zoom_reset = () => { stopMomentum(); svg.interrupt(); svg.transition().duration(350).call(zoom.transform, d3.zoomIdentity); };
    (node as any).__zoom_by = (f: number) => { stopMomentum(); svg.interrupt(); svg.transition().duration(250).call(zoom.scaleBy, f); };

    placeLabels(d3.zoomIdentity); // initial pass
    // labels live in screen px, so reflow them whenever the stage resizes
    const ro = new ResizeObserver(() => {
      placeLabels(d3.zoomTransform(node));
      followPinnedTip();
    });
    if (node.parentElement) ro.observe(node.parentElement);
    return () => { ro.disconnect(); stopMomentum(); };
  }, [features, dots, dotR, border, water]);

  // Recolor + (re)bind interactions whenever dataset or timestep changes.
  useEffect(() => {
    const node = svgRef.current;
    if (!node) return;
    const svg = d3.select(node);
    const color = dataset ? makeColor(dataset.colorScale) : () => "var(--map-empty)";
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
      followTipRef.current?.();
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
          // anchor the pinned tip at the city centroid so it tracks the city on
          // zoom/pan; fall back to the click point if the anchor isn't known yet.
          render(nameOf(d), keyOf(d));
          if (anchorsRef.current.has(keyOf(d))) followTipRef.current?.();
          else place(ev);
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
      <div ref={labelLayerRef} className="labels-layer" />
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
