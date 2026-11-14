# EarthMimic

Find Earth locations that can stand in for Moon and Mars sites, explain what
makes each one analogous, say plainly where the analogy breaks down, and plan
the smallest set of sites that covers a mission's test requirements.

Built for the NASA Space Apps challenge on planetary analogs.

> **Status: running on synthetic demo data.** `python -m earthmimic demo`
> generates placeholder datasets so the whole system can be run and inspected.
> None of the demo measurements are real. The Sun-geometry values are computed
> from latitude and axial tilt and are real. See "Plugging in real data".

## Quick start

    pip install -r requirements.txt
    python -m earthmimic demo            # generate raw demo data, clean it, run everything
    open out/dashboard.html              # interactive dashboard (one self-contained file)
    open out/campaign_map.html           # campaign routes on a real world map; click to set the start
    cat out/report.md                    # the same results as text
    python -m unittest discover -s tests # 73 tests

Python 3.10 or newer. One test also uses Node.js if it is installed.

## The pipeline

    raw data -> cleaning -> computed + derived variables -> relationship agent
             -> relationship store -> matching engine -> dashboard and report

| Stage | Module | What it does |
|---|---|---|
| Data cleaning | `cleaning.py` | Removes duplicates, sentinel codes, impossible values and bad coordinates; flags outliers; never fills gaps. Writes a report with counts, examples and a SHA-256 of every input file. |
| Sun geometry | `astronomy.py` | Computes, for any latitude and axial tilt, how much of the year the Sun sits 0 to 5 degrees above the horizon (the lighting of the lunar poles), and when each Earth site gets it. |
| Derived variables | `derived.py` | Physics quantities that mean the same thing on every world: wind force (dynamic pressure), liquid-water temperature window, typical daily high and low. |
| Relationship agent | `agent.py` | Decides which Moon/Mars column is comparable with which Earth column. A proposer suggests; fixed checks decide. Each pairing ends accepted, pending or denied. 15 tool calls per run. |
| Relationship store | `store.py` | SQLite. Decisions are reused while the data is unchanged, pending pairings go first next run, and every status change is kept as history. |
| Matching engine | `matching.py` | Scores every Earth cell from 0 to 1 on what Earth can test; reports what it cannot. Supports mission weights and single-property ranking. |
| Mission presets | `presets.py` | Dimension weights for rover testing, astrobiology, crew operations, resource extraction. |
| Sensitivity | `sensitivity.py` | Re-ranks 300 times with perturbed weights and confidences. |
| Validation | `benchmark.py` | Do known analogs rank near the top unprompted? Which top sites are far from every known analog? |
| Test planner | `planner.py` | Turns each testable property into a pass/fail requirement and finds the smallest set of sites that together pass all of them. |
| Campaign planner | `campaign.py` | For each number of sites, the sites that cover the most requirements and the shortest route between them: a cost-coverage curve. |
| Campaign map | `campaign_map.py` | A real world map (MapLibre GL: vector tiles, satellite, 3D globe) of every Earth cell and the campaign routes, with live cursor coordinates; click it or type coordinates to set the start. |
| Real-data ingestion | `ingest.py` | Downloads LRO Diviner, MGS MOLA, NASA POWER and Earth terrain data, merges hand-entered Mars climate values, and builds the raw data folder. |
| Language model | `llm.py` | Optional: lets a model propose pairings. Proposals are cached, and still have to pass every check. |
| Dashboard | `dashboard/` | Six views: Analogs, Limits, Test plan, Validation, Agent, Data. Re-scores live in the browser. |

## The dashboard

One self-contained HTML file; it needs no server and works offline (fonts fall
back to system fonts without internet).

- **Analogs:** an equal-area world map (Equal Earth projection) with Arctic and
  Antarctic insets, colored by match score. Beside the ranked sites, every
  property is drawn as a strip: the grey bar is the range found on Earth, the
  tick is the target, the dot is the selected site, and a red arrow means the
  target lies beyond anything on Earth.
- **Limits:** a matrix of every target against every dimension, showing what
  is testable, partly testable, or breaks down.
- **Test plan:** which site covers which requirement, the tolerance bands, and
  the field campaign curve: for one, two, three... sites, the most requirements
  covered and the shortest route. Type a starting point, or click the embedded
  world map (`campaign_map.html`, also usable on its own) to set it; the routes
  are recomputed in the browser and drawn on the map as great-circle arcs.
  The map shows the cursor's latitude and longitude live, places every marker
  by coordinates, and offers street, light, dark and satellite base maps on a
  flat map or a 3D globe. It needs an internet connection for the map tiles;
  everything else works offline.
- **Validation, Agent, Data:** rankings of known analogs, the agent's
  decisions, and the cleaning report.

Map outlines are Natural Earth 1:110m land (public domain), stored in
`dashboard/land.json`. All text files are read and written as UTF-8.

## What the agent checks

Free checks on metadata: both columns exist; neither depends on a local
reference (such as an elevation datum); same physical quantity; concept tags
agree; units are convertible; a derived column uses the same formula on both
sides.

Checks that read the data (one tool call per pairing): Earth data is complete
enough; the column actually varies; whether values span orders of magnitude
(then sites are compared by ratio, on a log scale); the column is not a copy
of a signal already accepted in the same dimension (then it counts half).

| Status | Meaning |
|---|---|
| accepted | Passed every check. Used for matching, with a confidence between 0 and 1. |
| pending | Not enough evidence yet (sparse data, or the run's budget ran out). Re-checked first next run. |
| denied | Failed a check that more data cannot fix. |

A raw column replaced by a derived one (wind speed, replaced by wind force)
stays accepted as an input but is not scored.

## How a score is computed

For a target value `t` and an Earth cell's value `x` of one accepted pairing:

    similarity = exp(-0.5 * ((x - t) / bandwidth)^2)
    bandwidth  = sqrt((0.75 * robust spread of the Earth column)^2 + (target uncertainty)^2)

On a log scale `x` and `t` are replaced by their base-10 logarithms. Each
pairing's weight is its dimension's weight, shared among the pairings in that
dimension in proportion to confidence. A cell's score is the weighted mean of
its similarities over the pairings it has data for.

At each target site a property is one of:

| Status | Meaning | Effect |
|---|---|---|
| match | Target value lies within Earth's range | full weight |
| partial | Just beyond Earth's range | half weight |
| breaks down | Far outside Earth's range, or vetoed by a physical rule | excluded, reported |
| not tested | Pairing still pending, or no target value | excluded, reported |
| input only | Replaced by a derived property | excluded |
| not comparable | Depends on a local reference | excluded |

"Coverage" is the share of the mission's weight that Earth can test at all.

## Real data: the fetch command

    python -m earthmimic fetch --out data/real_raw
    python -m earthmimic run --raw data/real_raw --data data/real --out out

Add `--start LAT,LON` (for example `--start 33.3,44.4`) to route the field
campaigns in the report and dashboard from your own base; without it the
routes are free-floating and the dashboard lets you type a start later, or
click one on the map.

`fetch` needs internet and about 700 MB of disk. It pulls together five
sources, each read according to its published label or documentation:

| World | Source | What comes out per site |
|---|---|---|
| Moon | LRO Diviner South Polar Resource Product (PDS, `dlre_prp_south.tab`, 605 MB) | Mean and maximum surface temperature, share of area with ice stable in the top metre, slope, relief |
| Mars | MGS MOLA topography, 16 px/deg (PDS, `megt90n000eb.img`, 33 MB) | Elevation, slope, relief, and a pressure estimate from elevation |
| Mars | Mars Climate Database (LMD, with ESA and CNES), entered by hand | Surface temperature, day-night swing, pressure, wind, dust |
| Earth | NASA POWER climatology API (no login) | Surface temperature, warmest-month high, day-night swing, wind, pressure, soil wetness, UV, precipitation, albedo, aerosol optical depth |
| Earth | Terrain Tiles on AWS Open Data (built from SRTM and others) | Slope and relief over the same 3.7 km baseline as the Mars grid |

**The one manual step.** The Mars Climate Database has a public web interface
but no documented data API. After the first `fetch`, open
`data/real_raw/sites/mars_climate.csv`, look up the five values for each site
in the database's web interface, type them in with the version and scenario
you used, and run `fetch` again. Without this, Mars temperature, wind and
dust are reported as not tested.

Sites are listed in `data/real_raw/sites/` (`moon_sites.csv`, `mars_sites.csv`,
`earth_sites.csv`). Edit them and rerun; downloads and replies are cached, so
reruns are fast. The default coordinates are approximate starting points:
check them against the IAU Gazetteer and mission pages before presenting.
The default Earth list is a 10-degree grid plus ten known analog sites; use
`--grid-step 5` for a denser grid (about four times as many requests).

Which properties end up comparable on both sides:

| Property | Moon | Mars | Earth |
|---|---|---|---|
| Mean surface temperature | Diviner | climate database | POWER |
| Warm extreme | Diviner annual maximum | derived daily high | POWER warmest-month high |
| Day-night swing | not available | climate database | POWER |
| Slope and relief | Diviner triangles (shorter baseline) | MOLA | terrain tiles |
| Surface pressure, liquid-water window | 0 (no atmosphere) | climate database or MOLA estimate | POWER |
| Wind force | none (no atmosphere) | climate database | POWER |
| Dust | none (no atmosphere) | climate database | POWER aerosol optical depth |
| Low-Sun lighting | computed | computed | computed |
| Ice stable in the top metre | Diviner | not available | no Earth counterpart yet |

Not covered yet: surface composition and mineralogy, radar, vegetation, and an
Earth counterpart for lunar ground ice. Properties with data on only one side
are listed in the Limits view; they are never invented.

The readers are tested on small files written in the exact published formats.
The live downloads and the live POWER and tile replies have not been run from
the development environment, which has no access to those servers. If a reply
differs from its documentation the error message says what was received, and
a POWER parameter the service does not accept is skipped rather than fatal.

To add another product, write a function that returns one row per site and add
its columns in `targets_table` or `earth_table` in `ingest.py`.

## Plugging in your own tables

Put these files in a folder and run:

    python -m earthmimic run --raw RAW_FOLDER --data CLEAN_FOLDER --out out

No code changes are needed.

| File | Contents |
|---|---|
| `earth_cells.csv` | One row per Earth location: `cell_id`, `lat`, `lon`, optional `region`, then one column per variable |
| `earth_meta.json` | One entry per Earth variable column (below) |
| `targets.csv` | One row per Moon/Mars site: `target_id`, `body` (Moon or Mars), `name`, optional `description`, `lat`, `lon`, then variables |
| `targets_meta.json` | One entry per target variable column |
| `known_analogs.csv` | Optional: `cell_id`, `name`, `body` for sites already used as analogs |

A metadata entry:

    {"name": "surf_temp_mean_K", "label": "Mean surface temperature",
     "dimension": "thermal", "quantity": "temperature", "unit": "K",
     "concept": "mean_temperature", "priority": 9,
     "uncertainty": 5.0, "version": "MCS v5.3"}

- `dimension`: terrain, thermal, illumination, water, dust, geology, habitability or physics.
- `quantity`: the physical quantity. Columns are only paired when it matches.
- `unit`: if the two datasets differ, a conversion must exist in `UNIT_CONVERSIONS` (`schema.py`).
- `concept`: what is measured. Identical tags pair automatically; related tags
  go in `RELATED_CONCEPTS`. Leave it empty to let a language model propose the pairing.
- `uncertainty`: 1-sigma measurement uncertainty in the column's unit (optional).
- `version`: dataset name and version, shown in the Data view (optional).
- `comparable: false` for values tied to a local reference.
- `source: "physical prior"` for values declared rather than measured.
- `valid_min` / `valid_max`: override the default physical bounds used in cleaning.

Derived variables need these concept tags on both sides: `mean_temperature`,
`diurnal_swing`, `surface_pressure`, `wind_speed`. A `grazing_sun_share`
column in `targets.csv` overrides the computed value (use it for permanently
shadowed sites).

`data/demo_raw` and `data/demo`, written by the demo command, are working
examples. Leave `SYNTHETIC_DATA.txt` out of a real data folder: its presence
is what switches on the "synthetic" warnings.

Gridded products (rasters) must be sampled to one row per location first.
That step is not part of this repository yet.

## Using a language model as the proposer

    export ANTHROPIC_API_KEY=...
    export EARTHMIMIC_MODEL=...          # the model id to use
    python -m earthmimic run --data data/real --out out --llm

Or from Python, with any provider:

    from earthmimic import pipeline
    from earthmimic.agent import LLMProposer
    from earthmimic.llm import CachedProposer

    def complete(prompt: str) -> str:
        ...  # call your model and return its text reply

    proposer = CachedProposer(LLMProposer(complete), "out/llm_proposals.json")
    pipeline.run("data/real", "out", proposer=proposer)

The model only proposes. Its suggestions go through the same checks, it cannot
pair columns whose concept tags disagree, and it cannot claim more confidence
than the registry allows. Proposals are cached, so reruns are reproducible and
work offline; if the model cannot be reached the rule-based proposer is used
and the run log says so.

## Limits

- The demo data is synthetic and the demo plants look-alike cells so the
  benchmark has something to find. Demo results say nothing about real sites.
- The model proposer is tested against a simulated API reply, not a live one.
- For columns with no concept tags, the checks confirm that a pairing is
  dimensionally and statistically usable, not that it is scientifically
  meaningful. Tag concepts wherever you can.
- The physical rule table (`schema.py`) has two rules. Real data will need more.
- Sun geometry assumes a circular orbit and ignores terrain shadowing and
  refraction. Daily high and low are approximated as mean plus or minus half
  the day-night swing. The boiling point uses the Magnus approximation.
- The campaign planner measures travel as great-circle distance between the
  stops. It does not yet know roads, access or permits, and it visits one
  representative cell per distinct set of passed requirements.
- Similarity is computed per property. It does not yet compare imagery,
  spectra or spatial texture.
