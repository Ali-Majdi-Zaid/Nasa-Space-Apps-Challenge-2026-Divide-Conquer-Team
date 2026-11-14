"""Interactive campaign map: campaign_map.html.

A real world map built on MapLibre GL JS (WebGL vector tiles from
OpenFreeMap, a satellite layer from Esri, and an optional 3D globe) that
shows every Earth cell, the stops of a campaign and the route between them
as great-circle arcs. The cursor's latitude and longitude are shown live;
clicking the map, dragging the start pin or typing coordinates sets the
starting point, and the cost-coverage curve is recomputed in the browser
from the pass/fail masks the campaign module exported. The page needs no
server. It is also embedded in the dashboard's Test-plan tab, and the two
keep each other's start point in sync with window messages.

Python's job here is to assemble the page from the pipeline payload; the
map itself is drawn by the browser.
"""
from __future__ import annotations

import json

from .schema import pretty_unit

MAPLIBRE_VERSION = "5.6.0"


def available() -> bool:
    return True


def map_data(payload: dict) -> dict:
    """The slice of the pipeline payload the map page needs."""
    e = payload["earth"]
    names = [k or r or c for k, r, c in zip(e["known"], e["region"], e["ids"])]
    targets, cols_needed, units = [], set(), {}
    for t in payload["targets"]:
        c = t["campaign"]
        by_label = {r["label"]: r for r in t.get("plan", {}).get("requirements", [])}
        detail = []   # the tolerance band behind each requirement, so the page can show a site's value against it
        for label in c.get("requirements", []):
            r = by_label.get(label)
            if r:
                detail.append(dict(label=label, earth_col=r["earth_col"], unit=r["unit"],
                                   target=round(r["target"], 4), lo=round(r["lo"], 4), hi=round(r["hi"], 4)))
                cols_needed.add(r["earth_col"])
                units[r["unit"]] = pretty_unit(r["unit"])
        targets.append(dict(id=t["id"], name=t["name"], body=t["body"], lat=t["lat"], lon=t["lon"],
                            requirements=c.get("requirements", []), masks=c.get("masks", []), scores=c.get("scores", []),
                            profiles=c.get("profiles", 0), detail=detail, start=c.get("start"), rows=c.get("rows", [])))
    cols = {k: v for k, v in e.get("cols", {}).items() if k in cols_needed}
    return dict(earth=dict(lat=e["lat"], lon=e["lon"], name=names, known=[bool(k) for k in e["known"]], cols=cols),
                targets=targets, units=units, sources=payload.get("data_sources", []),
                synthetic=bool(payload.get("synthetic")), generated=payload.get("generated", ""))


def build(payload: dict) -> str:
    """The campaign map page as HTML."""
    blob = json.dumps(map_data(payload), separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.replace("__VERSION__", MAPLIBRE_VERSION).replace("__DATA__", blob)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EarthMimic campaign map</title>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@__VERSION__/dist/maplibre-gl.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
:root {
  --bg: #0E131A; --glass: rgba(14, 19, 26, .84); --glass-2: rgba(255, 255, 255, .05); --line: rgba(255, 255, 255, .1);
  --ink: #E8ECF1; --muted: #9AA6B2; --moon: #7FA9D6; --mars: #E08A5C; --start: #FF5D5D; --ok: #6FBF98; --known: #F2B84B; --cell: #A9B4C0;
  --accent: var(--moon);
  --display: "Barlow Condensed", "Arial Narrow", system-ui, sans-serif; --text: Barlow, "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink); font: 400 14px/1.45 var(--text); }
#map { position: absolute; inset: 0; }
body.flat #map { right: var(--ui-w, 392px); }   /* flat map: the world ends where the panel column begins */
.glass { position: absolute; background: var(--glass); backdrop-filter: blur(14px) saturate(140%); -webkit-backdrop-filter: blur(14px) saturate(140%);
  border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 10px 30px rgba(0, 0, 0, .35); }
button, select, input { font: inherit; color: inherit; }
button { cursor: pointer; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
h1, h2 { font-family: var(--display); font-weight: 600; line-height: 1.05; margin: 0; }
.eyebrow { font-size: 11px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.k { font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 14px 0 6px; }
.mono { font-family: var(--mono); font-size: 12.5px; letter-spacing: .01em; }
.chip { display: inline-block; padding: 1px 8px; border-radius: 999px; font: 600 11px/1.6 var(--text); letter-spacing: .04em; text-transform: uppercase; vertical-align: middle;
  background: var(--glass-2); border: 1px solid var(--line); color: var(--muted); }
.chip.Moon { color: var(--moon); border-color: rgba(127, 169, 214, .4); }
.chip.Mars { color: var(--mars); border-color: rgba(224, 138, 92, .4); }
.chip.ok { color: var(--ok); border-color: rgba(111, 191, 152, .4); }
.chip.miss { text-decoration: line-through; opacity: .7; }

/* ---- left panel */
#panel { top: 16px; right: 16px; width: 360px; max-width: calc(100vw - 32px); max-height: calc(100% - 186px); overflow: auto; padding: 16px 18px 18px;
  scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, .22) transparent; }
#panel::-webkit-scrollbar { width: 8px; }
#panel::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, .22); border-radius: 4px; }
#panel .head { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: start; }
#panel h1 { font-size: 26px; margin: 2px 0 0; }
.tog { display: none; width: 32px; height: 32px; border-radius: 8px; border: 1px solid var(--line); background: var(--glass-2); color: var(--ink); font-size: 16px; line-height: 1; }
#panel.collapsed .more, #panel.collapsed select { display: none; }
#panel h1 .chip { margin-left: 8px; position: relative; top: -3px; }
#panel select { width: 100%; margin-top: 10px; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--line); background: rgba(255, 255, 255, .06); color: var(--ink); }
#panel select option { color: #111; }
.start { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px 12px; margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: var(--glass-2); border: 1px solid var(--line); }
.start .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.start .val { font-family: var(--mono); font-size: 15px; color: var(--ink); }
.start .val.none { font-family: var(--text); font-size: 13px; color: var(--muted); }
.start .lbl, .start .val { grid-column: 1; }
.start button { grid-column: 2; grid-row: 1 / span 2; justify-self: end; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--line); background: transparent; color: var(--muted); }
.start button:hover { color: var(--ink); border-color: var(--ink); }
.cards { display: grid; gap: 8px; }
.card { display: grid; grid-template-columns: 56px 1fr auto; gap: 12px; align-items: center; width: 100%; text-align: left; padding: 10px 12px; border-radius: 10px;
  background: var(--glass-2); border: 1px solid var(--line); color: var(--ink); transition: border-color .15s, background .15s; }
.card:hover { background: rgba(255, 255, 255, .09); }
.card.sel { border-color: var(--accent); background: rgba(255, 255, 255, .08); box-shadow: inset 3px 0 0 var(--accent); }
.card .n { font-family: var(--display); font-size: 28px; line-height: 1; }
.card .n span { display: block; font: 600 10px/1.2 var(--text); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: 3px; }
.card .bar { height: 6px; border-radius: 3px; background: rgba(255, 255, 255, .12); overflow: hidden; }
.card .bar i { display: block; height: 100%; background: var(--ok); border-radius: 3px; }
.card .sub { font-size: 12px; color: var(--muted); margin-top: 5px; }
.card .km { font-family: var(--mono); font-size: 15px; text-align: right; }
.card .km span { display: block; font: 600 10px/1.2 var(--text); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: 3px; }
.hint { font-size: 12px; color: var(--muted); margin: 6px 0 0; }
.stops { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.stops li { display: grid; grid-template-columns: 26px 1fr; gap: 10px; align-items: center; }
.stops .num { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font: 600 12px/1 var(--text); color: #fff; background: var(--accent); border: 2px solid rgba(255, 255, 255, .85); }
.stops .where { font-family: var(--mono); font-size: 11.5px; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 4px; }
.chips .chip { text-transform: none; letter-spacing: 0; font-weight: 500; }
.foot { margin-top: 14px; font-size: 11px; color: var(--muted); }

.card { position: relative; }
.card.rec { border-color: rgba(111, 191, 152, .55); }
.badge { position: absolute; top: -8px; right: 10px; font: 600 10px/1.5 var(--text); letter-spacing: .06em; text-transform: uppercase; background: var(--ok); color: #0E131A; border-radius: 999px; padding: 0 7px; }
.bal { padding: 8px 10px; border-radius: 10px; background: var(--glass-2); border: 1px solid var(--line); }
.bal input { width: 100%; accent-color: var(--ok); margin: 2px 0 6px; }
.bal .sub { font-size: 12px; color: var(--muted); }
.stops li { cursor: pointer; border-radius: 8px; padding: 4px 6px; margin: 0 -6px; }
.stops li:hover, .stops li.sel { background: var(--glass-2); }
.stops li .nm { font-weight: 500; }
.stops li .chip { margin-left: 6px; }
.ev { grid-column: 1 / -1; width: 100%; border-collapse: collapse; margin: 6px 0 2px; font-size: 12px; cursor: default; }
.ev th, .ev td { text-align: left; padding: 4px 6px; border-top: 1px solid var(--line); vertical-align: top; }
.ev th { font-size: 10px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); border-top: 0; }
.ev tr.fail td { color: var(--muted); }
.pass { color: var(--ok); font-weight: 600; }
.nope { color: var(--start); font-weight: 600; }

/* ---- bottom-left: cursor and coordinate entry */
#coords { right: 16px; bottom: 16px; width: 360px; max-width: calc(100vw - 32px); padding: 12px 14px; }
#coords .row { display: grid; grid-template-columns: 64px 1fr; align-items: center; gap: 10px; }
#coords .row + .row { margin-top: 8px; }
#coords .lbl { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
#cursor { font-family: var(--mono); font-size: 14px; min-height: 1.4em; }
#cursor.idle { color: var(--muted); font-family: var(--text); font-size: 12.5px; }
.entry { display: grid; grid-template-columns: 1fr 1fr auto; gap: 6px; }
.entry input { width: 100%; padding: 6px 8px; border-radius: 8px; border: 1px solid var(--line); background: rgba(255, 255, 255, .06); color: var(--ink); font-family: var(--mono); font-size: 12.5px; }
.entry input::placeholder { color: var(--muted); font-family: var(--text); }
.entry button, .seg button { padding: 6px 10px; border-radius: 8px; border: 1px solid var(--line); background: rgba(255, 255, 255, .06); color: var(--ink); }
.entry button:hover, .seg button:hover { background: rgba(255, 255, 255, .12); }
#coords .hint { margin-top: 8px; }

/* ---- top-right: basemaps and projection */
#basemaps { top: 16px; left: 16px; padding: 8px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-start; }
.seg { display: inline-flex; border-radius: 9px; overflow: hidden; border: 1px solid var(--line); }
.seg button { border: 0; border-radius: 0; background: transparent; color: var(--muted); padding: 6px 11px; font-weight: 500; }
.seg button + button { border-left: 1px solid var(--line); }
.seg button[aria-pressed="true"] { background: rgba(255, 255, 255, .14); color: var(--ink); }

/* ---- bottom-right: legend */
#legend { left: 16px; top: calc(var(--bars-h, 52px) + 28px); padding: 10px 12px; display: grid; gap: 6px; font-size: 12px; color: var(--muted); }
#legend div { display: flex; align-items: center; gap: 8px; }
#legend i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: var(--cell); opacity: .9; }
#legend i.known { background: var(--known); }
#legend i.stop { background: var(--accent); border: 2px solid #fff; }
#legend i.startp { background: var(--start); border: 2px solid #fff; }
#legend i.line { width: 18px; height: 3px; border-radius: 2px; background: var(--accent); }

/* ---- map markers */
.stop-pin { width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font: 600 13px/1 var(--text); color: #fff; background: var(--accent);
  border: 2px solid #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, .45); cursor: default; }
.start-pin { width: 20px; height: 20px; border-radius: 50%; background: var(--start); border: 3px solid #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, .5); position: relative; cursor: grab; }
.start-pin::after { content: ""; position: absolute; inset: -14px; border-radius: 50%; border: 2px solid var(--start); opacity: 0; animation: pulse 1.8s ease-out infinite; }
@keyframes pulse { 0% { transform: scale(.4); opacity: .9; } 100% { transform: scale(1.1); opacity: 0; } }
.maplibregl-popup-content { background: var(--glass); color: var(--ink); border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; font: 500 12.5px/1.4 var(--text); box-shadow: 0 6px 20px rgba(0, 0, 0, .4); }
.maplibregl-popup-content .mono { color: var(--muted); display: block; }
.maplibregl-popup-anchor-bottom .maplibregl-popup-tip { border-top-color: var(--glass); }
.maplibregl-popup-anchor-top .maplibregl-popup-tip { border-bottom-color: var(--glass); }
.maplibregl-ctrl-group { background: var(--glass) !important; border: 1px solid var(--line); box-shadow: 0 6px 20px rgba(0, 0, 0, .35) !important; }
.maplibregl-ctrl-group button + button { border-top: 1px solid var(--line) !important; }
.maplibregl-ctrl button .maplibregl-ctrl-icon { filter: invert(1) brightness(1.4); }
.maplibregl-ctrl-attrib { background: rgba(14, 19, 26, .7) !important; color: var(--muted); font-size: 11px; }
.maplibregl-ctrl-attrib a { color: var(--ink); }
/* ---- narrow screens: toggles become a top bar, the panel sits under it, controls move above the coordinates box */
@media (max-width: 860px) {
  body.flat #map { right: 0; }
  #basemaps { top: 10px; left: 10px; right: 10px; padding: 6px; justify-content: space-between; gap: 6px; }
  .seg button { padding: 5px 8px; font-size: 12px; }
  #panel { top: calc(var(--bars-h, 46px) + 18px); left: 10px; right: 10px; width: auto; max-width: none; padding: 12px 14px 14px;
    max-height: min(42%, calc(100% - var(--bars-h, 46px) - var(--coords-h, 120px) - 48px)); }
  #panel.collapsed { max-height: none; }
  #panel h1 { font-size: 22px; }
  .tog { display: grid; place-items: center; }
  .card { grid-template-columns: 48px 1fr auto; padding: 8px 10px; }
  .card .n { font-size: 24px; }
  #coords { left: 10px; right: 10px; bottom: 10px; width: auto; max-width: none; padding: 10px 12px; }
  #coords .hint { display: none; }
  #legend { display: none; }
  .maplibregl-ctrl-bottom-left { bottom: calc(var(--coords-h, 120px) + 12px); }
}
@media (max-height: 560px) {
  #panel { max-height: min(48%, calc(100% - var(--bars-h, 0px) - var(--coords-h, 120px) - 48px)); }
  #coords .hint { display: none; }
}
</style>
</head>
<body>
<div id="map" role="application" aria-label="World map of campaign routes"></div>
<aside id="panel" class="glass" aria-live="polite"></aside>
<div id="basemaps" class="glass">
  <div class="seg" role="group" aria-label="Base map">
    <button type="button" data-style="liberty" aria-pressed="false">Streets</button>
    <button type="button" data-style="positron" aria-pressed="false">Light</button>
    <button type="button" data-style="dark" aria-pressed="true">Dark</button>
    <button type="button" data-style="satellite" aria-pressed="false">Satellite</button>
  </div>
  <div class="seg" role="group" aria-label="Projection">
    <button type="button" data-proj="globe" aria-pressed="true">Globe</button>
    <button type="button" data-proj="mercator" aria-pressed="false">Flat</button>
  </div>
</div>
<div id="coords" class="glass">
  <div class="row"><span class="lbl">Cursor</span><span id="cursor" class="idle">Move over the map to read coordinates</span></div>
  <div class="row"><span class="lbl">Start</span>
    <form class="entry" id="entry">
      <input id="in-lat" type="number" step="any" min="-90" max="90" placeholder="latitude" aria-label="Start latitude">
      <input id="in-lon" type="number" step="any" min="-180" max="180" placeholder="longitude" aria-label="Start longitude">
      <button type="submit">Place</button>
    </form></div>
  <p class="hint">Click the map, drag the red pin, or type coordinates. Click an Earth cell to start exactly there.</p>
</div>
<div id="legend" class="glass" aria-label="Legend">
  <div><i></i>Earth cell</div><div><i class="known"></i>Known analog site</div><div><i class="stop"></i>Campaign stop, in order</div><div><i class="startp"></i>Start point</div><div><i class="line"></i>Great-circle route</div>
</div>
<script src="https://unpkg.com/maplibre-gl@__VERSION__/dist/maplibre-gl.js"></script>
<script>
(function () {
  var D = __DATA__;
  var N = D.earth.lat.length, RAD = Math.PI / 180;
  var embedded = window.parent && window.parent !== window;
  var params = new URLSearchParams(location.search);
  var state = { target: params.get("target"), start: undefined, k: null, style: "dark", proj: "globe", collapsed: false,
                worth: 51, stop: null };   // worth: slider position for "km one extra requirement is worth"; stop: expanded stop
  var hs = location.hash.match(/start=(-?[0-9.]+),(-?[0-9.]+)/);
  if (hs) state.start = [parseFloat(hs[1]), parseFloat(hs[2])];
  else if (location.hash.indexOf("free") >= 0) state.start = null;

  var STYLES = {
    liberty: "https://tiles.openfreemap.org/styles/liberty",
    positron: "https://tiles.openfreemap.org/styles/positron",
    dark: "https://tiles.openfreemap.org/styles/dark",
    satellite: { version: 8, glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
      sources: { esri: { type: "raster", tileSize: 256, attribution: "Imagery &copy; Esri, Maxar, Earthstar Geographics",
        tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"] } },
      layers: [{ id: "esri", type: "raster", source: "esri" }] }
  };

  // ------------------------------------------------------------- helpers
  function target() { for (var i = 0; i < D.targets.length; i++) if (D.targets[i].id === state.target) return D.targets[i]; return D.targets[0]; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function deg(v, pos, neg, digits) { return Math.abs(v).toFixed(digits == null ? 2 : digits) + "°" + (v >= 0 ? pos : neg); }
  function ll(la, lo, digits) { return deg(la, "N", "S", digits) + ", " + deg(lo, "E", "W", digits); }
  function wrapLon(lo) { return ((lo + 180) % 360 + 360) % 360 - 180; }
  function round2(x) { return Math.round(x * 100) / 100; }
  function cellLL(i) { return ll(D.earth.lat[i], D.earth.lon[i], 1); }
  function haverKm(la1, lo1, la2, lo2) {
    var a = Math.sin((la2 - la1) * RAD / 2), b = Math.sin((lo2 - lo1) * RAD / 2);
    return 2 * 6371 * Math.asin(Math.sqrt(a * a + Math.cos(la1 * RAD) * Math.cos(la2 * RAD) * b * b));
  }
  function pop(x) { var c = 0; while (x) { c += x & 1; x >>>= 1; } return c; }
  function accent(t) { return t.body === "Mars" ? "#E08A5C" : "#7FA9D6"; }

  // ---------------------------------------- the cost-coverage curve, in the browser
  function curve(t, start) {
    var masks = t.masks, nReq = t.requirements.length, rows = [];
    if (!nReq || !masks.length) return rows;
    var rep = {}, i, m;
    for (i = 0; i < N; i++) {
      m = masks[i];
      if (!m) continue;
      if (!(m in rep)) rep[m] = i;
      else if (start && haverKm(start[0], start[1], D.earth.lat[i], D.earth.lon[i]) <
                        haverKm(start[0], start[1], D.earth.lat[rep[m]], D.earth.lon[rep[m]])) rep[m] = i;
    }
    var keys = Object.keys(rep).map(Number), goal = 0;
    keys.forEach(function (x) { goal |= x; });
    var routeKm = function (order) {
      var km = 0, prev = start;
      order.forEach(function (ix) { if (prev) km += haverKm(prev[0], prev[1], D.earth.lat[ix], D.earth.lon[ix]); prev = [D.earth.lat[ix], D.earth.lon[ix]]; });
      return km;
    };
    var bestOrder = function (idx) {
      var best = idx.slice(), bk = Infinity;
      var perm = function (cur, rest) {
        if (!rest.length) { var km = routeKm(cur); if (km < bk) { bk = km; best = cur.slice(); } return; }
        for (var q = 0; q < rest.length; q++) perm(cur.concat([rest[q]]), rest.slice(0, q).concat(rest.slice(q + 1)));
      };
      perm([], idx);
      return { order: best, km: bk };
    };
    var maxCover = pop(goal);
    for (var k = 1; k <= Math.min(5, keys.length); k++) {
      var combos = [], pick = function (startAt, cur) {
        if (cur.length === k) { combos.push(cur.slice()); return; }
        for (var q = startAt; q < keys.length; q++) { cur.push(q); pick(q + 1, cur); cur.pop(); if (combos.length > 200000) return; }
      };
      pick(0, []);
      var bestCov = 0;
      combos.forEach(function (c) { var u = 0; c.forEach(function (q) { u |= keys[q]; }); if (pop(u) > bestCov) bestCov = pop(u); });
      var best = null, tried = 0, ties = 0, kms = [];
      combos.forEach(function (c) {
        var u = 0;
        c.forEach(function (q) { u |= keys[q]; });
        if (pop(u) !== bestCov) return;
        ties++;
        if (tried > 3000) return;
        tried++;
        var r = bestOrder(c.map(function (q) { return rep[keys[q]]; }));
        kms.push(r.km);
        if (!best || r.km < best.km) best = { covered: bestCov, km: r.km, order: r.order, union: u };
      });
      if (!best) break;
      kms.sort(function (a, b) { return a - b; });
      rows.push({ k: best.order.length, covered: best.covered, km: best.km, union: best.union,
                  stops: best.order.map(function (ix) { return { index: ix }; }),
                  candidates: combos.length, ties: ties, runner_up_km: kms.length > 1 ? kms[1] : null,
                  exact: combos.length <= 200000, profiles: keys.length });
      if (best.covered >= maxCover) break;
    }
    return rows;
  }
  function rows(t) {
    var s = state.start, pre = t.start;
    var same = (!s && !pre) || (!!s && !!pre && s[0] === pre[0] && s[1] === pre[1]);
    return same ? t.rows : curve(t, s);
  }
  function coveredLabels(t, row) {
    if (row.labels) return row.labels;
    return t.requirements.filter(function (_, j) { return (row.union >>> j) & 1; });
  }

  // ---------------------------------------- great-circle arcs ([lat, lon] in, [lon, lat] out, longitudes unwrapped)
  function arc(a, b) {
    var la1 = a[0] * RAD, lo1 = a[1] * RAD, la2 = b[0] * RAD, lo2 = b[1] * RAD;
    var d = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((la2 - la1) / 2), 2) + Math.cos(la1) * Math.cos(la2) * Math.pow(Math.sin((lo2 - lo1) / 2), 2)));
    var pts = [[a[1], a[0]]], n = 64;
    if (d < 1e-9) return [[a[1], a[0]], [b[1], b[0]]];
    for (var i = 1; i <= n; i++) {
      var f = i / n, A = Math.sin((1 - f) * d) / Math.sin(d), B = Math.sin(f * d) / Math.sin(d);
      var x = A * Math.cos(la1) * Math.cos(lo1) + B * Math.cos(la2) * Math.cos(lo2);
      var y = A * Math.cos(la1) * Math.sin(lo1) + B * Math.cos(la2) * Math.sin(lo2);
      var z = A * Math.sin(la1) + B * Math.sin(la2);
      pts.push([Math.atan2(y, x) / RAD, Math.atan2(z, Math.sqrt(x * x + y * y)) / RAD]);
    }
    for (i = 1; i < pts.length; i++) {
      while (pts[i][0] - pts[i - 1][0] > 180) pts[i][0] -= 360;
      while (pts[i][0] - pts[i - 1][0] < -180) pts[i][0] += 360;
    }
    return pts;
  }

  // ---------------------------------------------------------------- the map
  var cellsGeo = { type: "FeatureCollection", features: [] };
  for (var i = 0; i < N; i++) {
    cellsGeo.features.push({ type: "Feature", id: i, geometry: { type: "Point", coordinates: [D.earth.lon[i], D.earth.lat[i]] },
      properties: { i: i, name: D.earth.name[i], known: D.earth.known[i] ? 1 : 0 } });
  }
  var routeGeo = { type: "FeatureCollection", features: [] };
  var map = new maplibregl.Map({ container: "map", style: STYLES[state.style], center: [20, 15], zoom: 1.6, minZoom: 0.5, maxZoom: 14,
    attributionControl: false, canvasContextAttributes: { antialias: true } });
  window.EMmap = map;   // handy for debugging in the console
  map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-left");
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-left");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 120 }), "bottom-left");

  var popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
  function addLayers() {   // runs after every style load: layers and projection belong to the style
    var t = target();
    map.setProjection({ type: state.proj });
    if (!map.getSource("cells")) map.addSource("cells", { type: "geojson", data: cellsGeo });
    if (!map.getSource("route")) map.addSource("route", { type: "geojson", data: routeGeo });
    map.addLayer({ id: "route-glow", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": accent(t), "line-width": 12, "line-opacity": 0.22, "line-blur": 4 } });
    map.addLayer({ id: "route-line", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": accent(t), "line-width": 3.2, "line-opacity": 0.95 } });
    map.addLayer({ id: "cells", type: "circle", source: "cells",
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, ["case", ["==", ["get", "known"], 1], 4, 2.4], 6, ["case", ["==", ["get", "known"], 1], 8, 5]],
               "circle-color": ["case", ["==", ["get", "known"], 1], "#F2B84B", "#A9B4C0"],
               "circle-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 1, 0.78],
               "circle-stroke-color": "#0E131A", "circle-stroke-width": ["case", ["==", ["get", "known"], 1], 1.5, 0.8] } });
    map.addLayer({ id: "cell-labels", type: "symbol", source: "cells", filter: ["==", ["get", "known"], 1], minzoom: 3,
      layout: { "text-field": ["get", "name"], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-offset": [0, 1.1], "text-anchor": "top" },
      paint: { "text-color": "#F2B84B", "text-halo-color": "#0E131A", "text-halo-width": 1.2 } });
  }
  map.on("style.load", addLayers);

  var hovered = null;
  map.on("mousemove", "cells", function (e) {
    map.getCanvas().style.cursor = "pointer";
    var f = e.features[0];
    if (hovered !== null) map.setFeatureState({ source: "cells", id: hovered }, { hover: false });
    hovered = f.id; map.setFeatureState({ source: "cells", id: hovered }, { hover: true });
    var i = f.properties.i;
    popup.setLngLat([D.earth.lon[i], D.earth.lat[i]])
      .setHTML("<strong>" + esc(D.earth.name[i]) + "</strong>" + (D.earth.known[i] ? ' <span class="chip ok">known analog</span>' : "") + '<span class="mono">' + ll(D.earth.lat[i], D.earth.lon[i]) + "</span>")
      .addTo(map);
  });
  map.on("mouseleave", "cells", function () {
    map.getCanvas().style.cursor = "";
    if (hovered !== null) map.setFeatureState({ source: "cells", id: hovered }, { hover: false });
    hovered = null; popup.remove();
  });
  var cursor = document.getElementById("cursor");
  map.on("mousemove", function (e) { cursor.className = "mono"; cursor.textContent = ll(e.lngLat.lat, wrapLon(e.lngLat.lng), 3); });
  map.on("mouseout", function () { cursor.className = "idle"; cursor.textContent = "Move over the map to read coordinates"; });
  map.on("click", function (e) {
    var hit = map.queryRenderedFeatures(e.point, { layers: ["cells"] });
    if (hit.length) { var i = hit[0].properties.i; setStart([D.earth.lat[i], D.earth.lon[i]]); }
    else setStart([round2(e.lngLat.lat), round2(wrapLon(e.lngLat.lng))]);
  });

  function centroid(points) {   // mean direction of [lat, lon] points, as [lat, lon]
    var x = 0, y = 0, z = 0;
    points.forEach(function (p) { var la = p[0] * RAD, lo = p[1] * RAD; x += Math.cos(la) * Math.cos(lo); y += Math.cos(la) * Math.sin(lo); z += Math.sin(la); });
    var n = Math.sqrt(x * x + y * y + z * z);
    if (n < 1e-6) return points[0];
    return [Math.atan2(z, Math.sqrt(x * x + y * y)) / RAD, Math.atan2(y, x) / RAD];
  }

  // ---------------------------------------------------------- the route layer
  var markers = [];
  function drawRoute(t, row, fit) {
    markers.forEach(function (m) { m.remove(); }); markers = [];
    var path = [], prev = null;
    var seq = (state.start ? [{ ll: state.start.slice(), start: true }] : []).concat(row ? row.stops.map(function (s, n) {
      return { ll: [D.earth.lat[s.index], D.earth.lon[s.index]], index: s.index, n: n + 1 };
    }) : []);
    seq.forEach(function (p) {
      var here = [p.ll[1], p.ll[0]];
      if (prev) { var a = arc(prev, p.ll); path = path.concat(a.slice(1)); here = a[a.length - 1]; }
      else path.push(here);
      p.pos = here; prev = [here[1], here[0]];
    });
    routeGeo = { type: "FeatureCollection", features: path.length > 1 ? [{ type: "Feature", geometry: { type: "LineString", coordinates: path }, properties: {} }] : [] };
    if (map.getSource("route")) map.getSource("route").setData(routeGeo);
    ["route-glow", "route-line"].forEach(function (id) { if (map.getLayer(id)) map.setPaintProperty(id, "line-color", accent(t)); });
    seq.forEach(function (p) {
      var el = document.createElement("div");
      if (p.start) {
        el.className = "start-pin"; el.title = "Start: drag to move";
        var mk = new maplibregl.Marker({ element: el, draggable: true }).setLngLat(p.pos).addTo(map);
        mk.on("dragend", function () { var q = mk.getLngLat(); setStart([round2(q.lat), round2(wrapLon(q.lng))]); });
        markers.push(mk);
      } else {
        el.className = "stop-pin"; el.style.background = accent(t); el.textContent = p.n;
        el.title = "Stop " + p.n + ": " + D.earth.name[p.index] + " (" + cellLL(p.index) + ")";
        el.addEventListener("click", function (e) {
          e.stopPropagation();   // not a map click, so it does not move the start
          state.stop = state.stop === p.n - 1 ? null : p.n - 1;
          render(false);
          var li = panel.querySelector(".stops li.sel");
          if (li) li.scrollIntoView({ block: "nearest", behavior: "smooth" });
        });
        markers.push(new maplibregl.Marker({ element: el }).setLngLat(p.pos).addTo(map));
      }
    });
    if (fit && path.length) {
      var pad = fitPadding();
      if (state.proj === "globe") {
        // The whole sphere, centred on the campaign, sized to the area the overlays leave free.
        var w = map.getCanvas().clientWidth, h = map.getCanvas().clientHeight;
        var free = Math.min(w - pad.left - pad.right, h - pad.top - pad.bottom);
        var c = centroid(seq.map(function (p) { return p.ll; }));
        c[0] = Math.max(-60, Math.min(60, c[0]));   // a polar centre would need a giant sphere; from 60° the pole is still in view
        // MapLibre sizes the globe so that its scale at the centre matches Mercator, hence the cos(latitude) term.
        var zoom = Math.log2(Math.max(120, free * 0.85) * Math.PI * Math.cos(c[0] * RAD) / (1.09 * 512));
        map.easeTo({ center: [c[1], c[0]], zoom: Math.max(0.5, Math.min(zoom, 4)), padding: pad, pitch: 0, bearing: 0, duration: 1100 });
      } else {
        map.setPadding({ top: 0, right: 0, bottom: 0, left: 0 });   // the globe fit leaves persistent padding behind; fitBounds adds its own
        var b = path.reduce(function (bb, c) { return bb.extend(c); }, new maplibregl.LngLatBounds(path[0], path[0]));
        map.fitBounds(b, { padding: pad, maxZoom: 6, duration: 1100 });
      }
    }
  }

  // ------------------------------------------------- evidence, recommendation
  var UNITS = D.units || {};
  function num(v) { var a = Math.abs(v); if (a === 0) return "0"; return a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : a >= 1 ? v.toFixed(2) : v.toFixed(3); }
  function fmtVal(v, unit) {
    if (v == null || v !== v) return "no data";
    if (unit === "share_of_year") return num(100 * v) + "% of the year";
    var u = unit in UNITS ? UNITS[unit] : unit;
    return num(v) + (u === "°" ? u : u ? " " + u : "");
  }
  function score(t, i) { var s = t.scores && t.scores[i]; return s == null ? null : s; }
  function worthKm() { return Math.round(500 * Math.pow(60, state.worth / 100) / 100) * 100; }
  function recommend(R) {   // price each requirement in kilometres and take the campaign with the best net value
    var w = worthKm(), best = null;
    R.forEach(function (r) { var sc = r.covered - r.km / w; if (!best || sc > best.sc + 1e-9) best = { k: r.k, sc: sc }; });
    return best ? best.k : null;
  }
  function evidence(t, i) {   // one row per requirement: the site's measured value against the target band
    return '<table class="ev"><thead><tr><th>Requirement</th><th>This site</th><th>Target band</th><th></th></tr></thead><tbody>' + (t.detail || []).map(function (r) {
      var v = D.earth.cols && D.earth.cols[r.earth_col] ? D.earth.cols[r.earth_col][i] : null, ok = v != null && v >= r.lo && v <= r.hi;
      return "<tr" + (ok ? "" : ' class="fail"') + "><td>" + esc(r.label) + "</td><td>" + fmtVal(v, r.unit) + "</td><td>" + fmtVal(r.lo, r.unit) + " to " + fmtVal(r.hi, r.unit) +
        ' <span class="em-muted">(target ' + fmtVal(r.target, r.unit) + ")</span></td><td>" + (ok ? '<span class="pass">pass</span>' : '<span class="nope">fail</span>') + "</td></tr>";
    }).join("") + "</tbody></table>";
  }

  // --------------------------------------------------------------- the panel
  var panel = document.getElementById("panel"), coordsBox = document.getElementById("coords"), barsBox = document.getElementById("basemaps");
  function stacked() { return window.innerWidth <= 860; }
  function measure() {   // the panel and the map controls keep clear of the boxes whatever their rendered height
    document.documentElement.style.setProperty("--coords-h", coordsBox.offsetHeight + "px");
    document.documentElement.style.setProperty("--bars-h", barsBox.offsetHeight + "px");
    document.documentElement.style.setProperty("--ui-w", (Math.max(panel.offsetWidth, coordsBox.offsetWidth) + 32) + "px");
  }
  if (window.ResizeObserver) { var ro = new ResizeObserver(measure); ro.observe(coordsBox); ro.observe(barsBox); }
  measure();
  function fitPadding() {
    var w = map.getCanvas().clientWidth, h = map.getCanvas().clientHeight;
    var pr = panel.getBoundingClientRect(), cr = coordsBox.getBoundingClientRect();
    var pad = stacked()
      ? { top: Math.round(pr.bottom) + 14, left: 20, right: 20, bottom: Math.round(h - cr.top) + 44 }   // 44: the scale and attribution strip above the box
      : { top: 24, left: 24, right: Math.max(24, Math.round(map.getCanvas().getBoundingClientRect().right - pr.left) + 24), bottom: 48 };
    if (pad.left + pad.right > 0.7 * w) { pad.left = 16; pad.right = 16; }
    if (pad.top + pad.bottom > 0.75 * h) { pad.top = Math.round(0.35 * h); pad.bottom = Math.round(0.3 * h); }
    return pad;
  }
  var wasStacked = stacked(), resizeTimer = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { measure(); if (stacked() !== wasStacked) { wasStacked = stacked(); render(true); } }, 150);
  });
  function render(fit) {
    var t = target(), R = rows(t), nReq = t.requirements.length, s = state.start;
    document.documentElement.style.setProperty("--accent", accent(t));
    if (!R.length) state.k = null;
    else if (!R.some(function (x) { return x.k === state.k; })) state.k = R[R.length - 1].k;
    var row = R.filter(function (x) { return x.k === state.k; })[0];
    if (row && !(state.stop < row.stops.length)) state.stop = null;
    var rec = recommend(R), recRow = R.filter(function (x) { return x.k === rec; })[0], nxt = recRow ? R[R.indexOf(recRow) + 1] : null;
    var h = '<div class="head"><div><div class="eyebrow">EarthMimic · field campaign</div>' +
      "<h1>" + esc(t.name) + ' <span class="chip ' + esc(t.body) + '">' + esc(t.body) + "</span></h1></div>" +
      '<button type="button" class="tog" id="em-tog" aria-expanded="' + !state.collapsed + '" aria-controls="panel" title="' + (state.collapsed ? "Show the campaigns" : "Hide the campaigns") + '">' +
      (state.collapsed ? "&#9662;" : "&#9652;") + "</button></div>";
    if (!embedded) h += '<select id="em-target" aria-label="Target site">' + D.targets.map(function (x) {
      return '<option value="' + esc(x.id) + '"' + (x.id === t.id ? " selected" : "") + ">" + esc(x.name) + " · " + esc(x.body) + "</option>";
    }).join("") + "</select>";
    h += '<div class="start"><span class="lbl">Start point</span>' + (s ? '<button type="button" id="em-clear">Clear</button>' : "") +
      (s ? '<span class="val">' + ll(s[0], s[1]) + "</span>" : '<span class="val none">Not set: click the map or type coordinates</span>') + "</div>" +
      '<div class="more">';
    if (!R.length) h += '<p class="hint">No requirement of this target can be tested on Earth, so there is nothing to route.</p>';
    else {
      h += '<div class="k">Campaigns by number of sites</div><div class="cards">' + R.map(function (x) {
        return '<button type="button" class="card' + (x.k === state.k ? " sel" : "") + (x.k === rec ? " rec" : "") + '" data-k="' + x.k + '" aria-pressed="' + (x.k === state.k) + '">' +
          (x.k === rec ? '<span class="badge">Recommended</span>' : "") +
          '<div class="n">' + x.k + "<span>" + (x.k === 1 ? "site" : "sites") + "</span></div>" +
          '<div><div class="bar"><i style="width:' + (100 * x.covered / nReq).toFixed(0) + '%"></i></div><div class="sub">' + x.covered + " of " + nReq + " requirements</div></div>" +
          '<div class="km">' + Math.round(x.km).toLocaleString() + "<span>" + (s ? "km" : "km between") + "</span></div></button>";
      }).join("") + "</div>" +
      '<p class="hint">Fewer sites suit heavy equipment that must be set up; fewer kilometres suit portable instruments.' + (s ? "" : " Set a start point to count the first leg.") + "</p>";
      var rationale = "";
      if (recRow) {
        var gain = nxt ? nxt.covered - recRow.covered : 0;
        rationale = "At " + worthKm().toLocaleString() + " km per requirement, " + recRow.k + (recRow.k === 1 ? " site" : " sites") + " is the best trade: " +
          recRow.covered + " of " + nReq + " requirements for " + Math.round(recRow.km).toLocaleString() + " km." +
          (nxt ? " The next site adds " + gain + (gain === 1 ? " requirement" : " requirements") + " for " + Math.round(nxt.km - recRow.km).toLocaleString() + " km more." : " No further site adds coverage.");
      }
      h += '<div class="k">Balance coverage against cost</div><div class="bal">' +
        '<input id="em-worth" type="range" min="0" max="100" step="1" value="' + state.worth + '" aria-label="How many kilometres one extra requirement is worth">' +
        '<div class="sub">One extra requirement is worth up to <strong id="em-worth-v">' + worthKm().toLocaleString() + " km</strong> of travel. Coverage always ranks first; this only decides how far to go for one more requirement.</div></div>" +
        '<p class="hint">' + rationale + "</p>";
      if (row) {
        var cov = coveredLabels(t, row), miss = t.requirements.filter(function (l) { return cov.indexOf(l) < 0; });
        var scs = row.stops.map(function (st) { return score(t, st.index); }).filter(function (v) { return v != null; });
        var mean = scs.length ? scs.reduce(function (a, b) { return a + b; }, 0) / scs.length : null;
        h += '<div class="k">Route' + (s ? " from the start" : "") + (mean != null ? ' <span class="em-muted">· mean match ' + Math.round(100 * mean) + "%</span>" : "") + '</div><ol class="stops">' + row.stops.map(function (st, n) {
          var sc = score(t, st.index), sel = state.stop === n;
          return '<li data-i="' + n + '"' + (sel ? ' class="sel"' : "") + ' aria-expanded="' + sel + '"><span class="num">' + (n + 1) + '</span><span><span class="nm">' + esc(D.earth.name[st.index]) + "</span>" +
            (sc != null ? '<span class="chip">' + Math.round(100 * sc) + "% match</span>" : "") + '<br><span class="where">' + ll(D.earth.lat[st.index], D.earth.lon[st.index]) + "</span></span>" +
            (sel ? evidence(t, st.index) : "") + "</li>";
        }).join("") + '</ol><p class="hint">Click a stop, here or on the map, for the measurements behind it.</p>' +
          '<div class="k">What this campaign tests</div><div class="chips">' + cov.map(function (l) { return '<span class="chip ok">' + esc(l) + "</span>"; }).join("") +
          miss.map(function (l) { return '<span class="chip miss" title="Not covered by this campaign">' + esc(l) + "</span>"; }).join("") + "</div>";
        var profiles = row.profiles || t.profiles || 0, why = "Campaigns are ranked by coverage first and distance second. ";
        if (row.candidates) {
          why += "Checked " + row.candidates.toLocaleString() + (row.candidates === 1 ? " way" : " ways") + " of choosing " + row.k + " of " + profiles + " distinct site profiles" +
            (row.exact === false ? " (too many to check them all, so a greedy search finished the job)" : "") + ". " +
            (row.ties > 1 ? row.ties.toLocaleString() + " of them reach " + row.covered + " of " + nReq + " requirements; this one is the shortest" +
              (row.runner_up_km != null ? ", " + Math.round(row.runner_up_km - row.km).toLocaleString() + " km shorter than the next" : "") + "."
              : "Only this one reaches " + row.covered + " of " + nReq + " requirements.");
        }
        h += '<div class="k">Why this route</div><p class="hint">' + why + "</p>";
      }
    }
    h += '<div class="foot">' + (D.synthetic ? '<span class="chip">Synthetic demo data</span> ' : '<span class="chip ok">Real data</span> ' + (D.sources && D.sources.length ? esc(D.sources.join(" · ")) + ". " : "")) +
      "Distances are great-circle; the map does not know roads or permits.</div></div>";
    panel.innerHTML = h;
    panel.classList.toggle("collapsed", !!state.collapsed);
    document.getElementById("em-tog").addEventListener("click", function () { state.collapsed = !state.collapsed; render(true); });
    var sel = document.getElementById("em-target");
    if (sel) sel.addEventListener("change", function (e) { state.target = e.target.value; state.k = null; state.stop = null; render(true); });
    var slider = document.getElementById("em-worth");
    if (slider) {
      slider.addEventListener("input", function () { state.worth = parseInt(slider.value, 10); document.getElementById("em-worth-v").textContent = worthKm().toLocaleString() + " km"; });
      slider.addEventListener("change", function () { render(false); });
    }
    Array.prototype.forEach.call(panel.querySelectorAll(".stops li[data-i]"), function (li) {
      li.addEventListener("click", function (e) {
        if (e.target.closest("table")) return;
        var n = parseInt(li.getAttribute("data-i"), 10);
        state.stop = state.stop === n ? null : n;
        render(false);
      });
    });
    var clr = document.getElementById("em-clear");
    if (clr) clr.addEventListener("click", function () { setStart(null); });
    Array.prototype.forEach.call(panel.querySelectorAll(".card"), function (b) {
      b.addEventListener("click", function () { state.k = parseInt(b.getAttribute("data-k"), 10); state.stop = null; render(true); });
    });
    document.getElementById("in-lat").value = s ? s[0] : "";
    document.getElementById("in-lon").value = s ? s[1] : "";
    drawRoute(t, row, fit);
  }

  function setStart(s, silent) {
    state.start = s;
    try { history.replaceState(null, "", location.pathname + location.search + (s ? "#start=" + s[0] + "," + s[1] : "#free")); } catch (e) {}
    render(false);
    if (!silent && embedded) window.parent.postMessage({ type: "earthmimic-start", target: target().id, start: s }, "*");
  }

  document.getElementById("entry").addEventListener("submit", function (e) {
    e.preventDefault();
    var la = parseFloat(document.getElementById("in-lat").value), lo = parseFloat(document.getElementById("in-lon").value);
    if (isNaN(la) || isNaN(lo)) return;
    setStart([round2(Math.max(-90, Math.min(90, la))), round2(wrapLon(lo))]);
    render(true);
  });
  Array.prototype.forEach.call(document.querySelectorAll("#basemaps [data-style]"), function (b) {
    b.addEventListener("click", function () {
      state.style = b.getAttribute("data-style");
      Array.prototype.forEach.call(document.querySelectorAll("#basemaps [data-style]"), function (x) { x.setAttribute("aria-pressed", x === b); });
      map.setStyle(STYLES[state.style], { diff: false });
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll("#basemaps [data-proj]"), function (b) {
    b.addEventListener("click", function () {
      state.proj = b.getAttribute("data-proj");
      Array.prototype.forEach.call(document.querySelectorAll("#basemaps [data-proj]"), function (x) { x.setAttribute("aria-pressed", x === b); });
      applyProjectionLayout();
      // MapLibre animates the change of projection; a fit computed mid-way lands in the wrong place, so wait for it.
      var done = false, settle = function () { if (done) return; done = true; render(true); };
      map.once("projectiontransition", settle);
      setTimeout(settle, 1400);
      map.setProjection({ type: state.proj });
    });
  });
  window.addEventListener("message", function (e) {
    var d = e.data;
    if (!d || d.type !== "earthmimic-set-start") return;
    if (d.target && d.target !== target().id) { state.target = d.target; state.k = null; }
    setStart(d.start ? [d.start[0], d.start[1]] : null, true);
  });

  function applyProjectionLayout() {
    document.body.classList.toggle("flat", state.proj === "mercator");
    measure();
    map.resize();
  }
  applyProjectionLayout();
  if (state.start === undefined) { var t0 = target(); state.start = t0.start ? [t0.start[0], t0.start[1]] : null; }
  render(false);                                          // the panel and markers never wait for tiles
  map.once("load", function () { render(true); });        // the fit waits for the style, so the globe is measured right
})();
</script>
</body>
</html>
"""
