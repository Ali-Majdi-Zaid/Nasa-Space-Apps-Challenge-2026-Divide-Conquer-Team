"""Home page: index.html.

A small landing page for a run. It says what EarthMimic does in one
breath, shows the headline numbers of this run, and links into the two
working pages: the dashboard and the campaign map. Every number on it is
read from the pipeline payload, so it never drifts from the results.
"""
from __future__ import annotations

import html
import json


def _best_site(payload: dict, target: dict) -> tuple[str, float | None]:
    """Name and score of the best-matching Earth site for one target."""
    scores = target.get("campaign", {}).get("scores") or []
    best, at = None, -1
    for i, s in enumerate(scores):
        if s is not None and (best is None or s > best):
            best, at = s, i
    if at < 0:
        return "", None
    e = payload["earth"]
    return (e["known"][at] or e["region"][at] or e["ids"][at]), best


def summary(payload: dict) -> dict:
    """The numbers the page shows."""
    rels = payload["agent"]["relationships"]
    bench = payload.get("benchmark", {}).get("balanced", {}).get("summary", {})
    targets = []
    for t in payload["targets"]:
        name, score = _best_site(payload, t)
        rows = t.get("campaign", {}).get("rows") or []
        last = rows[-1] if rows else None
        targets.append(dict(id=t["id"], name=t["name"], body=t["body"], best=name, score=score,
                            reqs=len(t.get("campaign", {}).get("requirements") or []),
                            stops=last["k"] if last else 0, covered=last["covered"] if last else 0))
    return dict(
        cells=len(payload["earth"]["ids"]), targets=targets,
        moon=sum(1 for t in targets if t["body"] == "Moon"), mars=sum(1 for t in targets if t["body"] == "Mars"),
        pairings=sum(1 for r in rels if r["verdict"] == "accepted"),
        bench_hit=bench.get("in_top_5_percent"), bench_n=bench.get("n"), bench_chance=bench.get("expected_by_chance"),
        sources=payload.get("data_sources", []), synthetic=bool(payload.get("synthetic")),
        generated=payload.get("generated", ""))


def build(payload: dict) -> str:
    s = summary(payload)
    esc = html.escape
    cards = []
    for t in s["targets"]:
        pct = f"{round(100 * t['score'])}%" if t["score"] is not None else "n/a"
        trip = (f"{t['stops']} stops test {t['covered']} of {t['reqs']} properties" if t["stops"] else "nothing testable yet")
        cards.append(
            f'<a class="t {esc(t["body"])}" href="campaign_map.html?target={esc(t["id"])}">'
            f'<span class="body">{esc(t["body"])}</span><strong>{esc(t["name"])}</strong>'
            f'<span class="best">Best match on Earth: {esc(t["best"]) or "none"}</span>'
            f'<span class="row"><b>{pct}</b><span>{esc(trip)}</span></span></a>')
    bench = ""
    if s["bench_n"]:
        bench = (f'<div><b>{s["bench_hit"]} of {s["bench_n"]}</b><span>analog sites from the literature land in our '
                 f'top 5%. Chance alone would give {s["bench_chance"]}.</span></div>')
    sources = " · ".join(esc(x) for x in s["sources"]) or "see the Evidence page"
    badge = ('<span class="pill warn">Synthetic demo data</span>' if s["synthetic"]
             else '<span class="pill">Real NASA data</span>')
    blob = json.dumps(dict(generated=s["generated"]))
    return (TEMPLATE
            .replace("__BADGE__", badge)
            .replace("__CELLS__", f"{s['cells']:,}")
            .replace("__MOON__", str(s["moon"])).replace("__MARS__", str(s["mars"]))
            .replace("__PAIRINGS__", str(s["pairings"]))
            .replace("__BENCH__", bench)
            .replace("__CARDS__", "\n".join(cards))
            .replace("__SOURCES__", sources)
            .replace("__GENERATED__", esc(s["generated"]))
            .replace("__META__", blob.replace("</", "<\\/")))


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EarthMimic</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600&display=swap">
<style>
:root {
  --bg: #0B1017; --panel: rgba(255, 255, 255, .045); --line: rgba(255, 255, 255, .1); --ink: #E8ECF1; --muted: #9AA6B2;
  --moon: #7FA9D6; --mars: #E08A5C; --earth: #6FBF98; --warn: #F2B84B;
  --display: "Barlow Condensed", "Arial Narrow", system-ui, sans-serif; --text: Barlow, "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html { background: var(--bg); }
body { margin: 0; color: var(--ink); font: 400 16px/1.55 var(--text);
  background: radial-gradient(60rem 34rem at 82% -8%, rgba(127, 169, 214, .16), transparent 62%),
              radial-gradient(48rem 30rem at 4% 108%, rgba(224, 138, 92, .13), transparent 60%), var(--bg); min-height: 100vh; }
a { color: inherit; }
.wrap { max-width: 68rem; margin: 0 auto; padding: 0 1.25rem 3rem; }
header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1.25rem 0; }
.logo { font: 600 1.35rem/1 var(--display); letter-spacing: .04em; text-decoration: none; display: flex; align-items: center; gap: .55rem; }
.logo i { width: .8rem; height: .8rem; border-radius: 50%; background: var(--earth); box-shadow: .55rem -.25rem 0 -.2rem var(--moon), 1rem .1rem 0 -.18rem var(--mars); margin-right: .7rem; }
.pill { font-size: .72rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--earth); border: 1px solid rgba(111, 191, 152, .4); border-radius: 999px; padding: .2rem .7rem; }
.pill.warn { color: var(--warn); border-color: rgba(242, 184, 75, .45); }

.hero { display: grid; grid-template-columns: 1.15fr .85fr; gap: 2rem; align-items: center; padding: 2.2rem 0 2.6rem; }
.eyebrow { font-size: .75rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin: 0 0 .7rem; }
h1 { font: 600 clamp(2.4rem, 5.4vw, 4rem)/1.02 var(--display); margin: 0; letter-spacing: .005em; }
h1 em { font-style: normal; color: var(--earth); }
.lead { font-size: 1.1rem; color: var(--muted); max-width: 34rem; margin: 1rem 0 1.6rem; }
.cta { display: flex; flex-wrap: wrap; gap: .7rem; }
.btn { display: inline-block; padding: .75rem 1.2rem; border-radius: 10px; font-weight: 600; text-decoration: none; border: 1px solid var(--line); background: var(--panel); transition: transform .15s, background .15s, border-color .15s; }
.btn:hover { transform: translateY(-1px); border-color: var(--ink); }
.btn.primary { background: var(--earth); border-color: var(--earth); color: #0B1017; }
.btn.primary:hover { background: #86cfab; }
.btn small { display: block; font-weight: 400; font-size: .8rem; opacity: .8; }
:focus-visible { outline: 2px solid var(--earth); outline-offset: 3px; }
.orbit { width: 100%; max-width: 26rem; justify-self: end; }
.orbit .ring { fill: none; stroke: var(--line); stroke-dasharray: 2 6; }
.orbit .link { fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-dasharray: 5 7; animation: flow 6s linear infinite; }
.orbit text { font: 600 11px var(--text); letter-spacing: .1em; text-transform: uppercase; fill: var(--muted); }
@keyframes flow { to { stroke-dashoffset: -120; } }
@media (prefers-reduced-motion: reduce) { .orbit .link { animation: none; } .btn { transition: none; } }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; }
.stats div { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem; }
.stats b { display: block; font: 600 2rem/1.05 var(--display); }
.stats span { display: block; font-size: .85rem; color: var(--muted); margin-top: .35rem; }

h2 { font: 600 1.6rem/1.1 var(--display); margin: 2.8rem 0 .3rem; }
.sub { color: var(--muted); margin: 0 0 1.1rem; max-width: 44rem; }
.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; counter-reset: s; }
.steps div { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 1.1rem 1.1rem 1.2rem; counter-increment: s; }
.steps div::before { content: counter(s); display: grid; place-items: center; width: 1.9rem; height: 1.9rem; border-radius: 50%; font: 600 1rem var(--display); color: #0B1017; background: var(--earth); margin-bottom: .7rem; }
.steps strong { display: block; margin-bottom: .25rem; }
.steps p { margin: 0; font-size: .92rem; color: var(--muted); }

.targets { display: grid; grid-template-columns: repeat(auto-fill, minmax(15.5rem, 1fr)); gap: .8rem; }
.t { display: grid; gap: .25rem; text-decoration: none; background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem; border-top: 3px solid var(--c); transition: transform .15s, border-color .15s; }
.t.Moon { --c: var(--moon); } .t.Mars { --c: var(--mars); }
.t:hover { transform: translateY(-2px); border-color: var(--c); }
.t .body { font-size: .7rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--c); }
.t strong { font: 600 1.2rem/1.15 var(--display); }
.t .best { font-size: .85rem; color: var(--muted); min-height: 2.6em; }
.t .row { display: flex; align-items: baseline; gap: .6rem; margin-top: .2rem; }
.t .row b { font: 600 1.5rem/1 var(--display); color: var(--c); }
.t .row span { font-size: .8rem; color: var(--muted); }

footer { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--line); font-size: .85rem; color: var(--muted); }
footer p { margin: .3rem 0; }
@media (max-width: 52rem) {
  .hero { grid-template-columns: 1fr; padding-top: 1rem; } .orbit { justify-self: center; max-width: 19rem; order: -1; }
  .stats { grid-template-columns: repeat(2, 1fr); } .steps { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <a class="logo" href="index.html"><i></i>EarthMimic</a>
    __BADGE__
  </header>

  <section class="hero">
    <div>
      <p class="eyebrow">NASA Space Apps Challenge 2026</p>
      <h1>Rehearse the Moon and Mars <em>here on Earth</em>.</h1>
      <p class="lead">EarthMimic finds the places on Earth that behave most like a landing site on the Moon or Mars, plans a field trip through them, and tells you honestly what no place on Earth can reproduce.</p>
      <div class="cta">
        <a class="btn primary" href="explorer.html">Explorer<small>One site, one property, one answer</small></a>
        <a class="btn" href="campaign_map.html">Field trip map<small>Where to go and what to test</small></a>
        <a class="btn" href="evidence.html">Evidence<small>How we know</small></a>
      </div>
    </div>
    <svg class="orbit" viewBox="0 0 320 260" role="img" aria-label="Earth linked to the Moon and Mars">
      <defs>
        <radialGradient id="ge" cx="35%" cy="30%"><stop offset="0" stop-color="#a6e3c4"/><stop offset="1" stop-color="#2f7d5c"/></radialGradient>
        <radialGradient id="gm" cx="35%" cy="30%"><stop offset="0" stop-color="#c7dcf3"/><stop offset="1" stop-color="#55779c"/></radialGradient>
        <radialGradient id="gr" cx="35%" cy="30%"><stop offset="0" stop-color="#f3b594"/><stop offset="1" stop-color="#a9471f"/></radialGradient>
      </defs>
      <ellipse class="ring" cx="150" cy="140" rx="118" ry="86"/>
      <path class="link" stroke="#7FA9D6" d="M150 140 Q 200 60 252 62"/>
      <path class="link" stroke="#E08A5C" d="M150 140 Q 110 215 52 204"/>
      <circle cx="150" cy="140" r="46" fill="url(#ge)"/>
      <circle cx="252" cy="62" r="17" fill="url(#gm)"/>
      <circle cx="52" cy="204" r="24" fill="url(#gr)"/>
      <text x="150" y="204" text-anchor="middle">Earth</text>
      <text x="252" y="98" text-anchor="middle">Moon</text>
      <text x="52" y="246" text-anchor="middle">Mars</text>
    </svg>
  </section>

  <section class="stats" aria-label="This run in numbers">
    <div><b>__CELLS__</b><span>places on Earth compared, each from NASA measurements</span></div>
    <div><b>__MOON__ + __MARS__</b><span>landing sites: Moon south pole and Mars</span></div>
    <div><b>__PAIRINGS__</b><span>properties matched between worlds, each one checked</span></div>
    __BENCH__
  </section>

  <h2>How it works</h2>
  <p class="sub">Three steps, the same for every landing site.</p>
  <section class="steps">
    <div><strong>Compare</strong><p>Temperature, terrain, dust, ice, sunlight and more are measured on both worlds and compared property by property.</p></div>
    <div><strong>Rank and route</strong><p>Every place on Earth gets a match percentage. The best ones are joined into a field trip where each stop tests or double-checks something.</p></div>
    <div><strong>Stay honest</strong><p>Where Earth cannot stand in, such as near-vacuum pressure or lunar cold, the page says so and leaves it out of the score.</p></div>
  </section>

  <h2>Pick a landing site</h2>
  <p class="sub">Each card opens the field trip for that site on the map. The percentage is how alike its best Earth site is.</p>
  <section class="targets">
__CARDS__
  </section>

  <footer>
    <p><strong>Data:</strong> __SOURCES__.</p>
    <p>Only data from NASA and its Space Apps partner agencies is used. Results generated __GENERATED__.</p>
  </footer>
</div>
<script type="application/json" id="meta">__META__</script>
</body>
</html>
"""
