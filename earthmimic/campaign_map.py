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
    hazards = payload.get("extremes", {}).get("hazards", [])
    for t in payload["targets"]:
        # Earth's extremes connected to this landing site: for each hazard measured on both worlds, the Earth
        # site that comes closest to the landing site's value. Volcanic ground has no value there, so it is
        # offered for every target as the most eruption-prone site.
        stress = []
        for z in hazards:
            c = z.get("targets", {}).get(t["id"])
            if c and c.get("site"):
                stress.append(dict(key=z["key"], label=z["label"], tests=z["tests"], unit=z["unit"], verdict=c["verdict"],
                                   index=c["site"]["index"], here=c["site"]["value"], there=c["value"], extreme=z["extreme"]))
                units[z["unit"]] = pretty_unit(z["unit"])
            elif z.get("events") and z.get("top"):
                top = z["top"][0]
                stress.append(dict(key=z["key"], label=z["label"], tests=z["tests"], unit="", verdict="events",
                                   index=top["index"], here=top["value"], there=None, near=top.get("near", "")))
        c = t["campaign"]
        by_label = {r["label"]: r for r in t.get("plan", {}).get("requirements", [])}
        prof = {p["target_col"]: p for p in t.get("profile", [])}
        detail = []   # the tolerance band behind each requirement, so the page can show a site's value against it
        for label in c.get("requirements", []):
            r = by_label.get(label)
            if r:
                p = prof.get(r["target_col"], {})
                detail.append(dict(label=label, earth_col=r["earth_col"], unit=r["unit"], partial=bool(r.get("partial")),
                                   target=round(r["target"], 4), lo=round(r["lo"], 4), hi=round(r["hi"], 4),
                                   # what the similarity of one site on this variable is computed from
                                   bandwidth=p.get("bandwidth", 0.0), scale=p.get("scale", "linear"),
                                   dim=p.get("dimension", ""), source=p.get("source", "dataset")))
                cols_needed.add(r["earth_col"])
                units[r["unit"]] = pretty_unit(r["unit"])
        # Every variable of the target, whatever became of it, so nothing is hidden on the map page.
        variables = []
        for p in t.get("profile", []):
            v = p.get("target_value")
            variables.append(dict(label=p["label"], dim=p["dimension"], status=p["status"], reason=p.get("reason", ""),
                                  earth_col=p.get("earth_col", ""), unit=p.get("unit", ""),
                                  target=None if v is None else round(v, 4)))
            if p.get("earth_col"):
                cols_needed.add(p["earth_col"])
            if p.get("unit"):
                units[p["unit"]] = pretty_unit(p["unit"])
        targets.append(dict(id=t["id"], name=t["name"], body=t["body"], lat=t["lat"], lon=t["lon"],
                            requirements=c.get("requirements", []), masks=c.get("masks", []), scores=c.get("scores", []),
                            profiles=c.get("profiles", 0), detail=detail, variables=variables, stress=stress,
                            start=c.get("start"), rows=c.get("rows", [])))
    meta = e.get("col_meta", {})
    cols = {k: v for k, v in e.get("cols", {}).items() if k in cols_needed or k in meta}
    for m in meta.values():
        units[m["unit"]] = pretty_unit(m["unit"])
    ev = [dict(c=x["cat"], t=x["title"], la=x["lat"], lo=x["lon"], n=x["n"], d=x.get("last", ""))
          for x in payload.get("extremes", {}).get("events", [])]
    return dict(earth=dict(lat=e["lat"], lon=e["lon"], name=names, known=[bool(k) for k in e["known"]], cols=cols, meta=meta),
                events=ev,
                dims=payload.get("dims", {}),
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
.em-muted { color: var(--muted); font-weight: 400; }
.brief { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.brief div { padding: 8px 8px 7px; border-radius: 10px; background: var(--glass-2); border: 1px solid var(--line); }
.brief b { display: block; font: 600 20px/1.1 var(--display); color: var(--ink); }
.brief span { display: block; font-size: 10.5px; line-height: 1.25; color: var(--muted); margin-top: 3px; }
.chips.mini { grid-column: 1 / -1; margin: 2px 0 2px; }
.chips.mini .chip { font-size: 10.5px; padding: 0 6px; }
.ev.vm { margin-top: 2px; }
/* ---- stress-test sites */
.stress-pin { width: 22px; height: 22px; border-radius: 6px; transform: rotate(45deg); display: grid; place-items: center; background: var(--sc, #fff);
  border: 2px solid #0E131A; box-shadow: 0 0 0 1.5px var(--sc, #fff), 0 2px 8px rgba(0, 0, 0, .5); cursor: pointer; }
.stress-pin b { transform: rotate(-45deg); font: 700 11px/1 var(--text); color: #0E131A; }
.stress-pin.dim { opacity: .35; }
.slist { display: grid; gap: 5px; }
.slist button { display: grid; grid-template-columns: 22px 1fr; gap: 9px; align-items: start; width: 100%; text-align: left; padding: 7px 9px; border-radius: 9px;
  background: var(--glass-2); border: 1px solid var(--line); color: var(--ink); }
.slist button:hover, .slist button.sel { border-color: var(--sc); background: rgba(255, 255, 255, .09); }
.slist .code { width: 20px; height: 20px; border-radius: 5px; background: var(--sc); color: #0E131A; font: 700 11px/20px var(--text); text-align: center; margin-top: 1px; }
.slist .h { font-weight: 500; }
.slist .h small { font-weight: 600; color: var(--sc); margin-left: 6px; }
.slist .d { display: block; font-size: 11.5px; color: var(--muted); }
.stoggle { float: right; font: 500 11px var(--text); letter-spacing: 0; text-transform: none; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--line); background: transparent; color: var(--muted); }
.stoggle:hover { color: var(--ink); border-color: var(--ink); }
.spop { min-width: 210px; max-width: 270px; }
.spop .sv { display: block; margin: 5px 0 2px; padding-left: 8px; border-left: 3px solid var(--sc); }
.spop .sv b { color: var(--sc); font-weight: 600; }
.spop .sv span { display: block; color: var(--muted); font-size: 11.5px; }
.maplibregl-popup-close-button { color: var(--muted); font-size: 16px; padding: 0 6px; }
#legend i.stress { background: #6FBF98; border-radius: 3px; transform: rotate(45deg); width: 10px; height: 10px; margin: 0 1px; border: 1.5px solid #0E131A; box-shadow: 0 0 0 1px #6FBF98; }
/* ---- simple view */
.verdict { display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; padding: 12px 14px; border-radius: 12px;
  background: var(--glass-2); border: 1px solid var(--line); border-left: 4px solid var(--gc, var(--ok)); }
.verdict .big { font: 600 34px/1 var(--display); color: var(--gc, var(--ok)); white-space: nowrap; }
.verdict .big span { display: block; font: 600 10px/1.3 var(--text); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: 4px; }
.verdict b { display: block; font-size: 15px; font-weight: 600; line-height: 1.25; }
.verdict p { margin: 4px 0 0; font-size: 12.5px; color: var(--muted); }
.g-ex { --gc: #6FBF98; } .g-good { --gc: #A8CF7A; } .g-fair { --gc: #F2B84B; } .g-near { --gc: #E08A5C; } .g-none { --gc: #7C8794; }
.meters { display: grid; gap: 7px; }
.meter { display: grid; grid-template-columns: 1fr auto; gap: 2px 10px; align-items: baseline; font-size: 12.5px; }
.meter .nm2 { color: var(--ink); }
.meter .gw { font-weight: 600; color: var(--gc); white-space: nowrap; }
.meter .gw small { font-weight: 400; color: var(--muted); margin-left: 4px; }
.meter .track { grid-column: 1 / -1; height: 7px; border-radius: 4px; background: rgba(255, 255, 255, .1); overflow: hidden; }
.meter .track i { display: block; height: 100%; border-radius: 4px; background: var(--gc); }
.scale { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 11px; color: var(--muted); margin: 8px 0 0; }
.scale span::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--gc); margin-right: 5px; vertical-align: -1px; }
.cant { font-size: 12.5px; color: var(--muted); margin: 0; }
.cant b { color: var(--ink); font-weight: 500; }
.dbtn { width: 100%; margin-top: 14px; padding: 9px 12px; border-radius: 10px; border: 1px solid var(--line); background: rgba(255, 255, 255, .06); color: var(--ink); font-weight: 500; }
.dbtn:hover { background: rgba(255, 255, 255, .12); }
.vg { font-size: 12px; font-weight: 600; margin: 10px 0 4px; }
.vg.bad { color: var(--start); }
.vars { list-style: none; margin: 0; padding: 0; display: grid; gap: 5px; font-size: 12px; color: var(--muted); }
.vars li { padding: 5px 8px; border-radius: 8px; background: var(--glass-2); border: 1px solid var(--line); }
.vars strong { color: var(--ink); font-weight: 500; }
.ev tr.sep td { font-size: 10px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); padding-top: 9px; }

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
#legend i.volc { background: #FF6B4A; border-radius: 2px; transform: rotate(45deg); width: 9px; height: 9px; margin: 0 2px; }
#legend i.dustev { background: #D9B36C; border-radius: 2px; transform: rotate(45deg); width: 9px; height: 9px; margin: 0 2px; }
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
  <div><i></i>Earth cell</div><div><i class="known"></i>Known analog site</div><div id="lg-volc" hidden><i class="volc"></i>Volcanic eruptions (NASA EONET)</div><div id="lg-dust" hidden><i class="dustev"></i>Dust storm (NASA EONET)</div><div><i class="stop"></i>Campaign stop, in order</div><div><i class="stress"></i>Stress-test site for this landing site</div><div><i class="startp"></i>Start point</div><div><i class="line"></i>Great-circle route</div>
</div>
<script src="https://unpkg.com/maplibre-gl@__VERSION__/dist/maplibre-gl.js"></script>
<script>
(function () {
  var D = __DATA__;
  var N = D.earth.lat.length, RAD = Math.PI / 180;
  var embedded = window.parent && window.parent !== window;
  var params = new URLSearchParams(location.search);
  var state = { target: params.get("target"), start: undefined, k: null, style: "dark", proj: "globe", collapsed: false,
                worth: 51, stop: null, details: false, stress: true, spick: null };   // worth: slider position for "km one extra requirement is worth"; stop: expanded stop
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

  // ---------------------------------------- campaigns: chosen by the pipeline, re-ordered here for any start point
  // Which sites make up the best k-site campaign does not depend on where you start (coverage, confirmation and
  // match quality decide that). Only the visiting order and the distance do, so that is all the browser recomputes.
  function bestOrder(idx, start) {
    var best = idx.slice(), bk = Infinity;
    var km = function (order) {
      var d = 0, prev = start;
      order.forEach(function (ix) { if (prev) d += haverKm(prev[0], prev[1], D.earth.lat[ix], D.earth.lon[ix]); prev = [D.earth.lat[ix], D.earth.lon[ix]]; });
      return d;
    };
    var perm = function (cur, rest) {
      if (!rest.length) { var d = km(cur); if (d < bk) { bk = d; best = cur.slice(); } return; }
      for (var q = 0; q < rest.length; q++) perm(cur.concat([rest[q]]), rest.slice(0, q).concat(rest.slice(q + 1)));
    };
    perm([], idx);
    return { order: best, km: bk };
  }
  function legsOf(order, start) {
    var prev = start, out = [];
    order.forEach(function (ix) { out.push(prev ? haverKm(prev[0], prev[1], D.earth.lat[ix], D.earth.lon[ix]) : null); prev = [D.earth.lat[ix], D.earth.lon[ix]]; });
    return out;
  }
  function rows(t) {
    var s = state.start || null;
    return (t.rows || []).map(function (r) {
      var o = bestOrder(r.stops.map(function (x) { return x.index; }), s);
      return { k: r.k, covered: r.covered, confirmed: r.confirmed || 0, labels: r.labels, mean_score: r.mean_score,
               candidates: r.candidates, exact: r.exact, km: o.km, legs: legsOf(o.order, s),
               stops: o.order.map(function (ix) { return { index: ix }; }) };
    });
  }
  function coveredLabels(t, row) { return row.labels || []; }
  // How alike one site is to the target on one variable, 0 to 1: the same Gaussian the ranking uses.
  function simOf(r, v) {
    if (v == null || v !== v || !(r.bandwidth > 0)) return null;
    var z;
    if (r.scale === "log") { if (!(v > 0) || !(r.target > 0)) return null; z = (Math.log10(v) - Math.log10(r.target)) / r.bandwidth; }
    else z = (v - r.target) / r.bandwidth;
    return Math.exp(-0.5 * z * z);
  }
  function passes(r, v) { return v != null && v === v && v >= r.lo && v <= r.hi; }
  function pc(x) { return x == null ? "n/a" : Math.round(100 * x) + "%"; }
  // One word for a match percentage. A site counts as matching a property from about 61% up.
  function grade(x) {
    if (x == null) return { cls: "g-none", word: "No data" };
    x = Math.round(100 * x) / 100;   // grade the number that is shown, so "90%" never reads as merely good
    return x >= 0.9 ? { cls: "g-ex", word: "Excellent" } : x >= 0.75 ? { cls: "g-good", word: "Good" } :
           x >= 0.6 ? { cls: "g-fair", word: "Fair" } : { cls: "g-none", word: "Too different" };
  }
  function plural(n, one, many) { return n + " " + (n === 1 ? one : many); }
  // The whole campaign in plain words: what it tests, how closely, and what Earth cannot do.
  function simpleView(t, row, per, meanVar, nReq) {
    var V = t.variables || [], count = function (st) { return V.filter(function (v) { return v.status === st; }).length; };
    var broken = V.filter(function (v) { return v.status === "breaks_down"; }), noData = count("not_tested");
    var all = row.covered === nReq, g = grade(meanVar), body = t.body === "Moon" ? "the Moon" : t.body;
    var h = '<div class="k">The result in short</div><div class="verdict ' + (all ? g.cls : "g-fair") + '">' +
      '<div class="big">' + row.covered + "/" + nReq + "<span>properties</span></div><div><b>" +
      (all ? "This trip tests everything Earth can test for " + esc(t.name) + "."
           : "This trip tests " + row.covered + " of the " + nReq + " properties Earth can test for " + esc(t.name) + ".") + "</b>" +
      "<p>" + plural(row.stops.length, "stop", "stops") + ", " + Math.round(row.km).toLocaleString() + " km" + (state.start ? " from your start" : " between stops") + ". " +
      "On average the best stop is <strong>" + pc(meanVar) + "</strong> like the real site on each property: " + g.word.toLowerCase() + "." +
      (row.confirmed ? " " + plural(row.confirmed, "property is", "properties are") + " double-checked at a second stop." : "") + "</p></div></div>";
    h += '<div class="k">How close each property gets</div><div class="meters">' + per.map(function (p) {
      var v = p.best >= 0 ? p.sims[p.best] : null, gr = p.n ? grade(v) : { cls: "g-none", word: "Not matched" };
      if (p.n && p.r.partial && !(v >= 0.6)) gr = { cls: "g-near", word: "Closest on Earth" };
      return '<div class="meter ' + gr.cls + '"><span class="nm2">' + esc(p.r.label) + '</span><span class="gw">' + gr.word +
        "<small>" + (p.n ? pc(v) + " · stop " + (p.best + 1) : "no stop matches") + "</small></span>" +
        '<span class="track"><i style="width:' + (p.n && v != null ? Math.max(4, Math.round(100 * v)) : 0) + '%"></i></span></div>';
    }).join("") + "</div>" +
      '<p class="scale"><span class="g-ex">Excellent 90%+</span><span class="g-good">Good 75%+</span><span class="g-fair">Fair 60%+</span><span class="g-near">Closest on Earth</span></p>' +
      '<p class="hint">100% means the Earth site has exactly the value measured on ' + body + ". Below 60% a site does not count as a match.</p>";
    if (broken.length || noData) h += '<div class="k">What this trip cannot tell you</div><p class="cant">' +
      (broken.length ? "<b>" + plural(broken.length, "property", "properties") + " cannot be reproduced anywhere on Earth:</b> " +
        broken.map(function (v) { return esc(v.label.toLowerCase()); }).join(", ") + ". " : "") +
      (noData ? "<b>" + plural(noData, "more has", "more have") + " no measurement yet</b> on " + body + "." : "") + "</p>";
    return h;
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
  // Recorded natural events: where Earth is at its most violent. Shown under the cells, for context.
  var eventsGeo = { type: "FeatureCollection", features: (D.events || []).map(function (e, k) {
    return { type: "Feature", id: k, geometry: { type: "Point", coordinates: [e.lo, e.la] }, properties: { c: e.c, t: e.t, n: e.n, d: e.d } };
  }) };
  if ((D.events || []).some(function (e) { return e.c === "volcanoes"; })) document.getElementById("lg-volc").hidden = false;
  if ((D.events || []).some(function (e) { return e.c === "dustHaze"; })) document.getElementById("lg-dust").hidden = false;
  function addLayers() {   // runs after every style load: layers and projection belong to the style
    var t = target();
    map.setProjection({ type: state.proj });
    if (!map.getSource("cells")) map.addSource("cells", { type: "geojson", data: cellsGeo });
    if (!map.getSource("route")) map.addSource("route", { type: "geojson", data: routeGeo });
    if (!map.getSource("events")) map.addSource("events", { type: "geojson", data: eventsGeo });
    map.addLayer({ id: "events", type: "circle", source: "events",
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, ["min", 4.5, ["+", 1.4, ["*", 0.35, ["sqrt", ["get", "n"]]]]], 6, ["min", 11, ["+", 3.5, ["*", 0.8, ["sqrt", ["get", "n"]]]]]],
               "circle-color": ["case", ["==", ["get", "c"], "volcanoes"], "#FF6B4A", "#D9B36C"], "circle-opacity": 0.5,
               "circle-stroke-color": ["case", ["==", ["get", "c"], "volcanoes"], "#FF6B4A", "#D9B36C"], "circle-stroke-width": 0.8, "circle-stroke-opacity": 0.9 } });
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
  map.on("mousemove", "events", function (e) {
    if (hovered !== null) return;   // an Earth cell under the pointer wins
    var p = e.features[0].properties;
    popup.setLngLat(e.features[0].geometry.coordinates)
      .setHTML("<strong>" + esc(p.t) + "</strong>" + '<span class="mono">' + (p.c === "volcanoes" ? "Volcanic activity" : "Dust storm") + " · " + p.n + (p.n === 1 ? " event" : " events") + " recorded by NASA EONET" + (p.d ? ", latest " + esc(p.d) : "") + "</span>")
      .addTo(map);
  });
  map.on("mouseleave", "events", function () { if (hovered === null) popup.remove(); });
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

  // ------------------------------------------------- stress-test sites of the selected landing site
  // Earth's extremes that connect to this landing site: one diamond per site, lettered by hazard.
  var SV = { earth: ["#6FBF98", "Earth is harsher", "over-test here with margin"], same: ["#A8CF7A", "About as harsh", "a realistic rehearsal"],
             target: ["#FF8A7A", "Harsher at the landing site", "the nearest Earth gets"], events: ["#FF6B4A", "Recorded by NASA", "eruptions logged by NASA EONET"] };
  var CODE = { cold: "C", cycling: "S", dust: "D", wind: "W", uv: "U", dry: "A", rough: "R", frozen: "F", thin_air: "T", volcanic: "V" };
  var stressMarkers = [], stressByIndex = {};
  function stressLine(t, z) {   // "here X, there Y" in plain words
    if (z.verdict === "events") return z.here + " eruptions recorded within reach" + (z.near ? ", most active: " + esc(z.near) : "");
    return fmtVal(z.here, z.unit) + " here · " + fmtVal(z.there, z.unit) + " at " + esc(t.name.replace(/\s*\(.*\)$/, ""));
  }
  function stressPopup(t, i, group) {
    return '<div class="spop"><strong>' + esc(D.earth.name[i]) + '</strong><span class="mono">' + ll(D.earth.lat[i], D.earth.lon[i]) + "</span>" +
      '<span class="em-muted" style="display:block;margin-top:4px">Stress-test site for ' + esc(t.name) + "</span>" + group.map(function (z) {
        var v = SV[z.verdict];
        return '<span class="sv" style="--sc:' + v[0] + '"><b>' + esc(z.label) + "</b> · " + v[1] + "<span>" + stressLine(t, z) + "</span><span>Tests " + esc(z.tests) + ".</span></span>";
      }).join("") + "</div>";
  }
  function drawStress(t) {
    stressMarkers.forEach(function (m) { m.remove(); }); stressMarkers = []; stressByIndex = {};
    if (!state.stress) return;
    var by = {};
    (t.stress || []).forEach(function (z) { (by[z.index] = by[z.index] || []).push(z); });
    Object.keys(by).forEach(function (k) {
      var i = parseInt(k, 10), group = by[k], el = document.createElement("div");
      // a site serving several hazards takes the colour of its weakest verdict, so green always means "enough"
      var worst = group.some(function (z) { return z.verdict === "target"; }) ? "target" : group.some(function (z) { return z.verdict === "same"; }) ? "same" : group[0].verdict;
      el.className = "stress-pin"; el.style.setProperty("--sc", SV[worst][0]);
      el.innerHTML = "<b>" + (group.length > 1 ? group.length : CODE[group[0].key] || "!") + "</b>";
      el.title = group.map(function (z) { return z.label; }).join(", ") + ": " + D.earth.name[i];
      var mk = new maplibregl.Marker({ element: el }).setLngLat([D.earth.lon[i], D.earth.lat[i]])
        .setPopup(new maplibregl.Popup({ offset: 16, closeButton: true, maxWidth: "290px" }).setHTML(stressPopup(t, i, group))).addTo(map);
      el.addEventListener("click", function (e) { e.stopPropagation(); mk.togglePopup(); });   // not a map click: the start point stays put
      stressMarkers.push(mk); stressByIndex[i] = mk;
    });
  }
  function stressList(t) {
    var S = t.stress || [];
    if (!S.length) return "";
    var n = { earth: 0, same: 0, target: 0 };
    S.forEach(function (z) { if (z.verdict in n) n[z.verdict]++; });
    var h = '<div class="k">Stress tests: Earth at its harshest<button type="button" class="stoggle" id="em-stress" aria-pressed="' + state.stress + '">' + (state.stress ? "Hide on map" : "Show on map") + "</button></div>" +
      '<p class="hint" style="margin:0 0 7px">Where to push one stress as far as Earth can, matched to ' + esc(t.name) + ". Earth matches or beats it on " + (n.earth + n.same) + " of " + (n.earth + n.same + n.target) +
      " hazards. Diamonds on the map; click one for the comparison.</p>" + '<div class="slist">' + S.map(function (z, k) {
        var v = SV[z.verdict];
        return '<button type="button" data-s="' + k + '" style="--sc:' + v[0] + '"' + (state.spick === k ? ' class="sel"' : "") + '><span class="code">' + (CODE[z.key] || "!") + "</span><span>" +
          '<span class="h">' + esc(z.label) + "<small>" + v[1] + "</small></span>" + '<span class="d">' + esc(D.earth.name[z.index]) + "</span>" + '<span class="d">' + stressLine(t, z) + "</span></span></button>";
      }).join("") + "</div>";
    return h;
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
  var WORD = { breaks_down: "not reproducible", not_tested: "no target data", input_only: "input only", not_comparable: "not comparable" };
  function cellVal(col, i) { return D.earth.cols && D.earth.cols[col] ? D.earth.cols[col][i] : null; }
  function evidence(t, i) {   // one row per variable: first the requirements against their bands, then everything else measured
    var h = '<table class="ev"><thead><tr><th>Variable</th><th>This site</th><th>Target</th><th>Match</th></tr></thead><tbody>' + (t.detail || []).map(function (r) {
      var v = cellVal(r.earth_col, i), ok = passes(r, v), sm = simOf(r, v);
      return "<tr" + (ok ? "" : ' class="fail"') + "><td>" + esc(r.label) + (r.partial ? ' <span class="em-muted">(closest Earth gets)</span>' : "") + "</td><td>" + fmtVal(v, r.unit) + "</td><td>" + fmtVal(r.target, r.unit) +
        ' <span class="em-muted">(passes ' + fmtVal(r.lo, r.unit) + " to " + fmtVal(r.hi, r.unit) + ")</span></td><td>" +
        '<span class="' + (ok ? "pass" : "nope") + '">' + pc(sm) + "</span> " + (ok ? "pass" : "fail") + "</td></tr>";
    }).join("");
    var V = t.variables || [], seen = {}, meta = D.earth.meta || {};
    V.forEach(function (v) { if (v.earth_col) seen[v.earth_col] = 1; });
    var rest = V.filter(function (v) { return v.status in WORD; });
    if (rest.length) h += '<tr class="sep"><td colspan="4">Not routed: the other variables of this target</td></tr>' + rest.map(function (v) {
      return '<tr class="fail"><td>' + esc(v.label) + "</td><td>" + (v.earth_col ? fmtVal(cellVal(v.earth_col, i), v.unit) : "–") + "</td><td>" +
        (v.target != null && v.unit ? "target " + fmtVal(v.target, v.unit) : "–") + "</td><td>" + WORD[v.status] + "</td></tr>";
    }).join("");
    var extra = Object.keys(meta).filter(function (c) { return !seen[c] && D.earth.cols[c]; });
    if (extra.length) h += '<tr class="sep"><td colspan="4">Also measured here, no counterpart on the target</td></tr>' + extra.map(function (c) {
      return '<tr class="fail"><td>' + esc(meta[c].label) + "</td><td>" + fmtVal(cellVal(c, i), meta[c].unit) + "</td><td>–</td><td></td></tr>";
    }).join("");
    return h + "</tbody></table>";
  }
  // Every variable of the target and what became of it, so the panel accounts for all of them.
  var GROUPS = [["breaks_down", "Cannot be reproduced anywhere on Earth", "bad"], ["not_tested", "No target data yet", ""],
                ["input_only", "Used as an input to a derived property", ""], ["not_comparable", "Not comparable between worlds", ""]];
  function allVars(t) {
    var V = t.variables || [];
    if (!V.length) return "";
    var routed = V.filter(function (v) { return v.status === "match" || v.status === "partial"; }).length;
    var h = '<div class="k">All ' + V.length + ' variables of this target</div><p class="hint">' + routed + " are requirements and are routed above. The rest are listed here with the reason.</p>";
    GROUPS.forEach(function (g) {
      var items = V.filter(function (v) { return v.status === g[0]; });
      if (!items.length) return;
      h += '<div class="vg ' + g[2] + '">' + g[1] + " · " + items.length + '</div><ul class="vars">' + items.map(function (v) {
        return "<li><strong>" + esc(v.label) + "</strong>" + (v.target != null && v.unit ? " · target " + fmtVal(v.target, v.unit) : "") + (v.reason ? "<br>" + esc(v.reason) : "") + "</li>";
      }).join("") + "</ul>";
    });
    return h;
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
    var h = '<div class="head"><div><div class="eyebrow">' + (embedded ? "EarthMimic" : '<a href="index.html" title="Back to the home page" style="color:inherit">EarthMimic</a>') + " · field campaign</div>" +
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
          '<div><div class="bar"><i style="width:' + (100 * x.covered / nReq).toFixed(0) + '%"></i></div><div class="sub">' + x.covered + " of " + nReq + " variables matched" + (x.confirmed ? " · " + x.confirmed + " confirmed twice" : "") + "</div></div>" +
          '<div class="km">' + Math.round(x.km).toLocaleString() + "<span>" + (s ? "km" : "km between") + "</span></div></button>";
      }).join("") + "</div>" +
      '<p class="hint">' + (state.details ? "Stops are chosen among the best-matching Earth sites. Each extra stop is there because it matches a new variable or confirms one at a second, independent site." : "More stops test more, and double-check more. Pick a trip.") + (s ? "" : " Set a start point to count the first leg.") + "</p>";
      var rationale = "";
      if (recRow) {
        var gain = nxt ? nxt.covered - recRow.covered : 0;
        rationale = "At " + worthKm().toLocaleString() + " km per requirement, " + recRow.k + (recRow.k === 1 ? " site" : " sites") + " is the best trade: " +
          recRow.covered + " of " + nReq + " requirements for " + Math.round(recRow.km).toLocaleString() + " km." +
          (nxt ? " The next site adds " + gain + (gain === 1 ? " requirement" : " requirements") + " for " + Math.round(nxt.km - recRow.km).toLocaleString() + " km more." : " No further site adds coverage.");
      }
      if (state.details) h += '<div class="k">Balance coverage against cost</div><div class="bal">' +
        '<input id="em-worth" type="range" min="0" max="100" step="1" value="' + state.worth + '" aria-label="How many kilometres one extra requirement is worth">' +
        '<div class="sub">One extra requirement is worth up to <strong id="em-worth-v">' + worthKm().toLocaleString() + " km</strong> of travel. Coverage always ranks first; this only decides how far to go for one more requirement.</div></div>" +
        '<p class="hint">' + rationale + "</p>";
      if (row) {
        var cov = coveredLabels(t, row), miss = t.requirements.filter(function (l) { return cov.indexOf(l) < 0; });
        var DT = t.detail || [], idx = row.stops.map(function (st) { return st.index; });
        // per variable: its match at every stop, the best stop, and how many stops pass it
        var per = DT.map(function (r) {
          var sims = idx.map(function (i) { return simOf(r, cellVal(r.earth_col, i)); });
          var ok = idx.map(function (i) { return passes(r, cellVal(r.earth_col, i)); });
          var best = -1; sims.forEach(function (v, n) { if (v != null && (best < 0 || v > sims[best])) best = n; });
          return { r: r, sims: sims, ok: ok, best: best, n: ok.filter(Boolean).length };
        });
        var matched = per.filter(function (p) { return p.n > 0; });
        var meanVar = matched.length ? matched.reduce(function (a, p) { return a + (p.sims[p.best] || 0); }, 0) / matched.length : null;
        var scs = idx.map(function (i) { return score(t, i); }).filter(function (v) { return v != null; });
        var mean = scs.length ? scs.reduce(function (a, b) { return a + b; }, 0) / scs.length : null;
        h += simpleView(t, row, per, meanVar, nReq);
        if (state.details) h += '<div class="k">This campaign in brief</div><div class="brief">' +
          "<div><b>" + row.stops.length + "</b><span>" + (row.stops.length === 1 ? "stop" : "stops") + "</span></div>" +
          "<div><b>" + row.covered + "/" + nReq + "</b><span>variables matched</span></div>" +
          "<div><b>" + (row.confirmed || 0) + "</b><span>confirmed at 2+ stops</span></div>" +
          "<div><b>" + pc(meanVar) + "</b><span>best match per variable, mean</span></div>" +
          "<div><b>" + pc(mean) + "</b><span>overall site match, mean</span></div>" +
          "<div><b>" + Math.round(row.km).toLocaleString() + "</b><span>km" + (s ? " from start" : " between stops") + "</span></div></div>";
        h += '<div class="k">' + (state.details ? "Route" + (s ? " from the start" : "") : "Where to go, in order") + '</div><ol class="stops">' + row.stops.map(function (st, n) {
          var sc = score(t, st.index), sel = state.stop === n, leg = row.legs && row.legs[n];
          var here = per.filter(function (p) { return p.ok[n]; });
          var fresh = here.filter(function (p) { return p.ok.indexOf(true) === n; }).length;
          return '<li data-i="' + n + '"' + (sel ? ' class="sel"' : "") + ' aria-expanded="' + sel + '"><span class="num">' + (n + 1) + '</span><span><span class="nm">' + esc(D.earth.name[st.index]) + "</span>" +
            (state.details && sc != null ? '<span class="chip">' + Math.round(100 * sc) + "% match</span>" : "") + '<br><span class="where">' + ll(D.earth.lat[st.index], D.earth.lon[st.index]) +
            (leg != null ? " · " + Math.round(leg).toLocaleString() + " km from " + (n === 0 ? "the start" : "stop " + n) : "") + "</span>" +
            (state.details
              ? '<br><span class="where">Matches ' + here.length + " of " + nReq + " here" + (n > 0 ? ": " + fresh + " new, " + (here.length - fresh) + " confirming" : "") + "</span></span>" +
                '<span class="chips mini">' + here.map(function (p) { return '<span class="chip ok" title="' + esc(p.r.label) + '">' + esc(p.r.label) + " " + pc(p.sims[n]) + "</span>"; }).join("") + "</span>"
              : '<br><span class="where">Good for ' + here.length + " of " + nReq + ": " +
                esc(here.slice().sort(function (a, b) { return (b.sims[n] || 0) - (a.sims[n] || 0); }).slice(0, 3).map(function (p) { return p.r.label.toLowerCase(); }).join(", ")) +
                (here.length > 3 ? " and " + (here.length - 3) + " more" : "") + "</span></span>") +
            (sel ? evidence(t, st.index) : "") + "</li>";
        }).join("") + '</ol><p class="hint">Click a stop, here or on the map, for every measurement behind it.</p>';
        if (state.details) {
        h += '<div class="k">Variables matched, and how well</div><table class="ev vm"><thead><tr><th>Variable</th><th>Best match</th><th>Where</th><th>Stops passing</th></tr></thead><tbody>' +
          per.map(function (p) {
            return "<tr" + (p.n ? "" : ' class="fail"') + "><td>" + esc(p.r.label) + (p.r.partial ? ' <span class="em-muted">(closest Earth gets)</span>' : "") + "</td><td>" +
              (p.n ? '<span class="pass">' + pc(p.sims[p.best]) + "</span>" : '<span class="nope">' + pc(p.best >= 0 ? p.sims[p.best] : null) + "</span>") + "</td><td>" +
              (p.best >= 0 ? "stop " + (p.best + 1) : "–") + "</td><td>" + (p.n ? p.n + " of " + idx.length + (p.n > 1 ? " · confirmed" : "") : "not covered") + "</td></tr>";
          }).join("") + "</tbody></table>" +
          '<p class="hint">Match is 100% when the site equals the target value and falls off with distance; a site passes a variable at about 61% or more.</p>';
        var why = "Campaigns are ranked by variables matched, then by variables confirmed at a second site, then by how well the stops match the target overall. ";
        if (row.candidates) why += "Checked " + row.candidates.toLocaleString() + (row.candidates === 1 ? " way" : " ways") + " of choosing " + row.k + " of the " + (t.profiles || 0) + " best-matching candidate sites" +
          (row.exact === false ? " (too many to check them all, so a greedy search finished the job)" : "") + ". ";
        why += "The stops are then visited in the shortest order" + (s ? " from your start point." : ".");
        h += '<div class="k">Why this route</div><p class="hint">' + why + "</p>";
        }
      }
    }
    h += stressList(t);
    if (state.details) h += allVars(t);
    h += '<button type="button" class="dbtn" id="em-details" aria-pressed="' + state.details + '">' + (state.details ? "Hide details" : "Show details: numbers, legs and every variable") + "</button>";
    h += '<div class="foot">' + (D.synthetic ? '<span class="chip">Synthetic demo data</span> ' : '<span class="chip ok">Real data</span> ' + (D.sources && D.sources.length ? esc(D.sources.join(" · ")) + ". " : "")) +
      'Distances are great-circle; the map does not know roads or permits.<br><a href="explorer.html" style="color:inherit">Explorer</a> · <a href="evidence.html" style="color:inherit">Evidence</a></div></div>';
    panel.innerHTML = h;
    panel.classList.toggle("collapsed", !!state.collapsed);
    document.getElementById("em-tog").addEventListener("click", function () { state.collapsed = !state.collapsed; render(true); });
    var sel = document.getElementById("em-target");
    if (sel) sel.addEventListener("change", function (e) { state.target = e.target.value; state.k = null; state.stop = null; state.spick = null; render(true); });
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
    var sbtn = document.getElementById("em-stress");
    if (sbtn) sbtn.addEventListener("click", function () { state.stress = !state.stress; state.spick = null; render(false); });
    Array.prototype.forEach.call(panel.querySelectorAll(".slist button[data-s]"), function (b) {
      b.addEventListener("click", function () {
        var k = parseInt(b.getAttribute("data-s"), 10), z = (t.stress || [])[k];
        if (!z) return;
        if (!state.stress) state.stress = true;
        state.spick = k; render(false);
        var mk = stressByIndex[z.index];
        map.easeTo({ center: [D.earth.lon[z.index], D.earth.lat[z.index]], zoom: Math.max(map.getZoom(), 2.2), duration: 900 });
        if (mk && !mk.getPopup().isOpen()) mk.togglePopup();
      });
    });
    var dbtn = document.getElementById("em-details");
    if (dbtn) dbtn.addEventListener("click", function () { state.details = !state.details; render(false); });
    var clr = document.getElementById("em-clear");
    if (clr) clr.addEventListener("click", function () { setStart(null); });
    Array.prototype.forEach.call(panel.querySelectorAll(".card"), function (b) {
      b.addEventListener("click", function () { state.k = parseInt(b.getAttribute("data-k"), 10); state.stop = null; render(true); });
    });
    document.getElementById("in-lat").value = s ? s[0] : "";
    document.getElementById("in-lon").value = s ? s[1] : "";
    drawRoute(t, row, fit);
    drawStress(t);
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
