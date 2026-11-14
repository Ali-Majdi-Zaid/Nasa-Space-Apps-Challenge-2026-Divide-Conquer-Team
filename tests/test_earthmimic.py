"""Tests. Run with:  python -m unittest discover -s tests -v"""
import copy
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from earthmimic import astronomy, campaign, campaign_map, cleaning, demo_data, derived, pipeline, planner
from earthmimic.agent import LLMProposer, Proposal, RelationshipAgent
from earthmimic.benchmark import known_analog_benchmark
from earthmimic.io import load
from earthmimic.llm import CachedProposer, anthropic_complete
from earthmimic.matching import Matcher, haversine_km
from earthmimic.presets import PRESETS
from earthmimic.schema import BODIES, DIMENSIONS, convert, convert_delta
from earthmimic.sensitivity import stability
from earthmimic.store import MemoryStore, SqliteStore

ROOT = Path(__file__).resolve().parent.parent
BAL = PRESETS["balanced"]["weights"]


class Base(unittest.TestCase):
    """Runs the whole demo pipeline once: raw data -> cleaning -> agent -> matching."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        demo_data.generate_raw(cls.tmp / "raw")
        cls.run_ = pipeline.run(cls.tmp / "data", cls.tmp / "out", raw_dir=cls.tmp / "raw", fresh_store=True)
        cls.ds, cls.agent, cls.matcher = cls.run_["dataset"], cls.run_["agent"], cls.run_["matcher"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def rel(self, tcol, ecol, result=None):
        return next(r for r in (result or self.agent).relationships if r.target_col == tcol and r.earth_col == ecol)


class TestUnits(unittest.TestCase):
    def test_conversions(self):
        self.assertAlmostEqual(convert(273.15, "K", "degC"), 0.0)
        self.assertAlmostEqual(convert(700, "Pa", "kPa"), 0.7)
        self.assertAlmostEqual(convert(95, "percent", "fraction"), 0.95)
        self.assertEqual(convert(40, "K_delta", "degC_delta"), 40)

    def test_an_uncertainty_is_converted_as_a_difference(self):
        self.assertAlmostEqual(convert_delta(5, "K", "degC", at=215), 5.0)   # not -268
        self.assertAlmostEqual(convert_delta(100, "Pa", "kPa", at=700), 0.1)

    def test_unknown_conversion_raises(self):
        with self.assertRaises(KeyError):
            convert(1, "K", "kPa")


class TestCleaning(Base):
    def counts(self, report=None):
        out = {}
        for c in (report or self.run_["cleaning"])["changes"]:
            out[(c["table"], c["rule"])] = out.get((c["table"], c["rule"]), 0) + c["count"]
        return out

    def test_every_planted_defect_is_caught(self):
        n = self.counts()
        self.assertEqual(n[("Earth cells", "No-data sentinel code")], 20)
        self.assertEqual(n[("Earth cells", "Physically impossible value")], 9)
        self.assertEqual(n[("Earth cells", "Missing or impossible coordinates")], 4)
        self.assertEqual(n[("Earth cells", "Exact duplicate row")], 12)
        self.assertEqual(n[("Earth cells", "Same id with conflicting values")], 5)
        self.assertEqual(n[("Earth cells", "Longitude given as 0 to 360")], 6)
        self.assertEqual(n[("Earth cells", "Text where a number belongs")], 2)
        self.assertEqual(n[("Target sites", "Exact duplicate row")], 1)

    def test_cleaned_tables_are_valid(self):
        earth = pd.read_csv(self.tmp / "data" / "earth_cells.csv")
        self.assertFalse(earth["cell_id"].duplicated().any())
        self.assertTrue(earth["lat"].abs().le(90).all() and earth["lon"].abs().le(180).all())
        self.assertFalse(earth.isin([-9999.0]).any().any())
        self.assertTrue(earth["ice_fraction"].dropna().between(0, 1).all())
        self.assertTrue((earth["temp_mean_c"].dropna() > -273.15).all())
        self.assertEqual(len(pd.read_csv(self.tmp / "data" / "targets.csv")), 6)

    def test_nothing_is_filled_in(self):
        raw = pd.read_csv(self.tmp / "raw" / "earth_cells.csv")
        clean = pd.read_csv(self.tmp / "data" / "earth_cells.csv")
        self.assertGreaterEqual(clean["temp_mean_c"].isna().sum(), raw["temp_mean_c"].isna().sum())

    def test_cleaning_clean_data_changes_nothing(self):
        again = cleaning.clean_folder(self.tmp / "data", self.tmp / "data2")
        changed = [c for c in again["changes"] if c["action"] != "flagged, value kept"]
        self.assertEqual(changed, [])

    def test_report_fingerprints_the_inputs(self):
        files = {f["name"]: f for f in self.run_["cleaning"]["files"]}
        self.assertEqual(len(files["earth_cells.csv"]["sha256"]), 64)

    def test_outliers_are_flagged_not_removed(self):
        df = pd.DataFrame({"cell_id": [f"c{i}" for i in range(200)], "lat": 0.0, "lon": 0.0,
                           "slope_deg": [5.0 + 0.01 * i for i in range(199)] + [80.0]})
        cols = {"slope_deg": self.ds.earth_cols["slope_deg"]}
        out, log = cleaning.clean_table(df, cols, "cell_id", "t", normalise_lon=True)
        self.assertEqual(out["slope_deg"].max(), 80.0)
        self.assertEqual([c["count"] for c in log if c["rule"] == "Extreme outlier"], [1])


class TestAstronomy(unittest.TestCase):
    def test_pole_matches_the_closed_form(self):
        # At a pole the Sun's elevation equals its declination, so the share of the year
        # between 0 and 5 degrees is asin(sin 5 / sin tilt) / pi.
        tilt = BODIES["Earth"]["obliquity_deg"]
        exact = np.arcsin(np.sin(np.radians(5)) / np.sin(np.radians(tilt))) / np.pi
        self.assertAlmostEqual(astronomy.grazing_share(90, tilt), exact, places=2)

    def test_hemispheres_are_symmetric(self):
        self.assertAlmostEqual(astronomy.grazing_share(72, 23.44), astronomy.grazing_share(-72, 23.44), places=4)

    def test_lunar_pole_is_always_grazing_when_lit(self):
        # Tilt 1.54 degrees: the Sun never rises above about 2 degrees, and is up half the time.
        self.assertAlmostEqual(astronomy.grazing_share(-89.5, BODIES["Moon"]["obliquity_deg"]), 0.5, places=2)

    def test_equator_gets_little_low_sun_and_high_latitudes_get_more(self):
        self.assertLess(astronomy.grazing_share(0, 23.44), 0.04)
        self.assertGreater(astronomy.grazing_share(70, 23.44), 0.09)

    def test_rehearsal_window(self):
        w = astronomy.rehearsal_window(85)
        self.assertGreaterEqual(w["peak_hours"], 11)
        self.assertGreater(w["days_6h"], 30)
        self.assertEqual(astronomy.rehearsal_window(10)["days_6h"], 0)


class TestDerived(Base):
    def test_water_boils_near_100_at_sea_level_and_near_2_on_mars(self):
        w = derived._liquid_window({"surface_pressure": np.array([101.325, 0.7, 0.5, 0.0])}, None)
        self.assertAlmostEqual(w[0], 100, delta=1.0)
        self.assertAlmostEqual(w[1], 1.9, delta=0.2)
        self.assertEqual(list(w[2:]), [0.0, 0.0])   # below the triple point there is no liquid at all

    def test_wind_force_accounts_for_thin_air(self):
        v = lambda p, t, s: {"surface_pressure": np.array([p]), "mean_temperature": np.array([t]), "wind_speed": np.array([s])}
        earth = derived._wind_pressure(v(101.325, 15, 6), BODIES["Earth"]["gas_constant"])[0]
        mars = derived._wind_pressure(v(0.7, -58, 6), BODIES["Mars"]["gas_constant"])[0]
        self.assertAlmostEqual(earth, 0.5 * 1.225 * 36, delta=0.3)
        self.assertGreater(earth / mars, 50)       # same speed, far weaker push
        self.assertEqual(derived._wind_pressure(v(0, -160, 0), None)[0], 0.0)

    def test_derived_columns_exist_on_both_sides(self):
        for d in derived.DERIVED:
            self.assertIn(d.column.name, self.ds.earth.columns)
            self.assertIn(d.column.name, self.ds.targets.columns)
            self.assertEqual(self.rel(d.column.name, d.column.name).verdict, "accepted")

    def test_wind_speed_becomes_an_input_only(self):
        self.assertFalse(self.rel("wind_ms", "wind_ms").scored)
        status = {p.target_col: p.status for p in self.matcher.profile("mars-delta")}
        self.assertEqual(status["wind_ms"], "input_only")
        self.assertIn(status["wind_pressure_pa"], ("match", "partial"))
        # ...and the derived column is not penalised as a copy of the column it replaces.
        self.assertGreater(self.rel("wind_pressure_pa", "wind_pressure_pa").confidence, 0.9)

    def test_wide_ranging_quantity_is_compared_by_ratio(self):
        self.assertEqual(self.rel("wind_pressure_pa", "wind_pressure_pa").scale, "log")
        ds = copy.deepcopy(self.ds)
        p = next(p for p in self.matcher.profile("mars-delta") if p.target_col == "wind_pressure_pa")
        ds.earth.iloc[0, ds.earth.columns.get_loc("wind_pressure_pa")] = p.target_value * 2
        ds.earth.iloc[1, ds.earth.columns.get_loc("wind_pressure_pa")] = p.target_value / 2
        s = Matcher(ds, self.agent).single("mars-delta", "wind_pressure_pa")
        self.assertAlmostEqual(s[0], s[1], places=9)   # double and half are equally far


class TestAgent(Base):
    def test_all_pairings_are_decided_within_budget_per_run(self):
        self.assertTrue(all(r["used"] <= 15 for r in self.run_["runs"]))
        self.assertEqual(self.run_["runs"][0]["used"], 15)
        self.assertGreater(len(self.run_["runs"]), 1)
        self.assertFalse(any(r.verdict == "pending" for r in self.agent.relationships))

    def test_budget_leaves_the_rest_pending(self):
        tight = RelationshipAgent(self.ds, max_tool_calls=4).run()
        self.assertEqual(tight.tool_calls_used, 4)
        self.assertEqual(len(tight.accepted()), 4)
        self.assertTrue(tight.waiting_on_budget())

    def test_datum_dependent_column_is_denied_for_free(self):
        self.assertEqual(self.rel("elevation_m", "elevation_m").verdict, "denied")
        log = [line for run in self.run_["runs"] for line in run["log"]]
        self.assertFalse(any("elevation" in line and line.startswith("Tool call") for line in log))

    def test_unit_conversion_is_recorded(self):
        self.assertEqual(self.rel("surf_temp_mean_K", "temp_mean_c").conversion, "K -> degC")
        self.assertEqual(self.rel("basalt_abundance_pct", "basalt_fraction").conversion, "percent -> fraction")

    def test_related_concept_gets_lower_confidence(self):
        self.assertGreater(self.rel("weh_fraction", "ice_fraction").confidence,
                           self.rel("weh_fraction", "soil_moisture").confidence)

    def test_bad_proposals_cannot_get_through(self):
        class Bad:
            def propose(self, t, e):
                return [Proposal("slope_deg", "temp_mean_c", 1.0, "wrong quantity"),
                        Proposal("surf_temp_mean_K", "pressure_kpa", 1.0, "wrong quantity"),
                        Proposal("made_up", "slope_deg", 1.0, "no such column"),
                        Proposal("weh_fraction", "basalt_fraction", 1.0, "same quantity, different thing"),
                        Proposal("slope_deg", "slope_deg", 1.0, "fine")]
        res = RelationshipAgent(self.ds, proposer=Bad()).run()
        self.assertEqual([r.id for r in res.accepted()], ["slope_deg__slope_deg"])

    def test_proposer_cannot_exceed_registered_prior(self):
        class Eager:
            def propose(self, t, e):
                return [Proposal("weh_fraction", "soil_moisture", 1.0, "overconfident")]
        res = RelationshipAgent(self.ds, proposer=Eager()).run()
        self.assertAlmostEqual(res.accepted()[0].confidence, 0.5)

    def test_constant_column_is_denied_and_sparse_column_stays_pending(self):
        ds = copy.deepcopy(self.ds)
        ds.earth["slope_deg"] = 3.0
        ds.earth.loc[ds.earth.index[: int(0.6 * len(ds.earth))], "roughness_m"] = np.nan
        res = RelationshipAgent(ds, max_tool_calls=99).run()
        self.assertEqual(self.rel("slope_deg", "slope_deg", res).verdict, "denied")
        sparse = self.rel("rms_roughness_m", "roughness_m", res)
        self.assertEqual((sparse.verdict, sparse.pending_reason), ("pending", "evidence"))

    def test_duplicate_signal_is_downweighted(self):
        ds = copy.deepcopy(self.ds)
        ds.earth["roughness_m"] = ds.earth["slope_deg"] * 0.2 + 0.1   # same signal as slope
        res = RelationshipAgent(ds, max_tool_calls=99).run()
        rough = self.rel("rms_roughness_m", "roughness_m", res)
        self.assertEqual(rough.verdict, "accepted")
        self.assertAlmostEqual(rough.confidence, 0.5, places=2)


class TestStore(Base):
    def test_decisions_are_reused_while_data_is_unchanged(self):
        store = MemoryStore()
        agent = RelationshipAgent(self.ds, max_tool_calls=99)
        first = agent.run(store, store.new_run())
        second = agent.run(store, store.new_run())
        self.assertGreater(first.tool_calls_used, 0)
        self.assertEqual(second.tool_calls_used, 0)
        self.assertEqual({r.id: r.verdict for r in first.relationships}, {r.id: r.verdict for r in second.relationships})
        self.assertTrue(all(r.origin == "reused" for r in second.accepted()))

    def test_changed_data_is_rechecked(self):
        store, ds = MemoryStore(), copy.deepcopy(self.ds)
        agent = RelationshipAgent(ds, max_tool_calls=99)
        agent.run(store, store.new_run())
        ds.earth["slope_deg"] = ds.earth["slope_deg"] * 1.1
        again = agent.run(store, store.new_run())
        self.assertEqual(again.tool_calls_used, 1)
        self.assertTrue(any("slope_deg ~ slope_deg" in line and line.startswith("Tool call 1") for line in again.log))

    def test_pending_pairings_go_first_next_run(self):
        store = MemoryStore()
        agent = RelationshipAgent(self.ds, max_tool_calls=5)
        first = agent.run(store, store.new_run())
        left = {r.id for r in first.relationships if r.verdict == "pending"}
        self.assertEqual(set(store.pending()), left)
        second = agent.run(store, store.new_run())
        checked = {r.id for r in second.relationships if r.origin == "checked" and r.verdict == "accepted"}
        self.assertEqual(len(checked), 5)
        self.assertTrue(checked <= left)

    def test_sqlite_store_round_trip_and_history(self):
        path = self.tmp / "store_test.sqlite"
        store = SqliteStore(path)
        agent = RelationshipAgent(self.ds, max_tool_calls=3)
        agent.run(store, store.new_run())
        agent.run(store, store.new_run())
        store.close()
        store = SqliteStore(path)   # reopen: decisions survive the process
        row = store.get("slope_deg__slope_deg")
        self.assertEqual(row["verdict"], "accepted")
        self.assertEqual(row["payload"]["checks"][0]["name"], "Columns exist")
        last = next(r for r in RelationshipAgent(self.ds, max_tool_calls=0).run(store, store.new_run()).relationships
                    if r.verdict == "pending")
        self.assertEqual([h["verdict"] for h in store.history(last.id)][-1], "pending")
        store.close()


class TestLanguageModel(Base):
    REPLY = '```json\n' + json.dumps([
        {"target_col": "surf_temp_mean_K", "earth_col": "temp_mean_c", "prior": 0.9, "rationale": "both temperature"},
        {"target_col": "weh_fraction", "earth_col": "basalt_fraction", "prior": 0.8, "rationale": "plausible but wrong"},
        {"target_col": "dust_tau"},  # malformed
    ]) + '\n```'

    def test_model_output_is_parsed_and_still_validated(self):
        res = RelationshipAgent(self.ds, proposer=LLMProposer(lambda prompt: self.REPLY)).run()
        verdict = {r.id: r for r in res.relationships}
        self.assertEqual(verdict["surf_temp_mean_K__temp_mean_c"].verdict, "accepted")
        self.assertAlmostEqual(verdict["surf_temp_mean_K__temp_mean_c"].confidence, 0.9, places=2)
        self.assertEqual(verdict["weh_fraction__basalt_fraction"].verdict, "denied")

    def test_api_request_shape_and_reply_parsing(self):
        seen = {}

        def fake_urlopen(req, timeout):
            seen["url"], seen["headers"], seen["body"] = req.full_url, dict(req.header_items()), json.loads(req.data)
            return io.BytesIO(json.dumps({"content": [{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}]}).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            text = anthropic_complete(model="some-model", api_key="k")("ping")
        self.assertEqual(text, "hello world")
        self.assertEqual(seen["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(seen["body"]["model"], "some-model")
        self.assertEqual(seen["body"]["messages"], [{"role": "user", "content": "ping"}])
        headers = {k.lower(): v for k, v in seen["headers"].items()}
        self.assertEqual((headers["x-api-key"], headers["anthropic-version"]), ("k", "2023-06-01"))

    def test_proposals_are_cached_for_reproducible_offline_runs(self):
        calls = []
        cache = self.tmp / "llm_cache.json"
        make = lambda: CachedProposer(LLMProposer(lambda p: calls.append(1) or self.REPLY), cache)
        a = make().propose(self.ds.target_cols, self.ds.earth_cols)
        b = make().propose(self.ds.target_cols, self.ds.earth_cols)
        self.assertEqual(len(calls), 1)
        self.assertEqual([(p.target_col, p.earth_col) for p in a], [(p.target_col, p.earth_col) for p in b])

    def test_unreachable_model_falls_back_to_rules(self):
        def down(prompt):
            raise OSError("no network")
        prop = CachedProposer(LLMProposer(down), self.tmp / "llm_cache_none.json")
        res = RelationshipAgent(self.ds, proposer=prop, max_tool_calls=99).run()
        self.assertGreater(len(res.accepted()), 10)
        self.assertTrue(any("used the rule-based proposer" in line for line in res.log))


class TestMatching(Base):
    def test_scores_are_between_0_and_1(self):
        for tid in self.ds.targets.index:
            for preset in PRESETS.values():
                total = self.matcher.score(tid, preset["weights"]).total
                ok = total[~np.isnan(total)]
                self.assertTrue(((ok >= 0) & (ok <= 1)).all())

    def test_perfect_twin_scores_one(self):
        ds = copy.deepcopy(self.ds)
        used, _ = self.matcher.similarities("mars-delta")
        for p in used:
            ds.earth.iloc[0, ds.earth.columns.get_loc(p.earth_col)] = p.target_value
        self.assertAlmostEqual(Matcher(ds, self.agent).score("mars-delta", BAL).total[0], 1.0, places=9)

    def test_no_atmosphere_breaks_wind_and_dust(self):
        status = {p.target_col: p.status for p in self.matcher.profile("moon-ridge")}
        for col in ("dust_tau", "wind_pressure_pa", "surf_pressure_Pa", "liquid_window_c"):
            self.assertEqual(status[col], "breaks_down", col)
        self.assertEqual(status["elevation_m"], "not_comparable")

    def test_frozen_site_does_not_use_soil_moisture(self):
        water = next(p for p in self.matcher.profile("mars-ice") if p.target_col == "weh_fraction")
        self.assertEqual(water.earth_col, "ice_fraction")
        self.assertTrue(any("Liquid soil water" in a for a in water.alternates))

    def test_earth_cannot_match_a_lunar_pole_for_low_sun(self):
        sun = next(p for p in self.matcher.profile("moon-ridge") if p.target_col == "grazing_sun_share")
        self.assertEqual(sun.status, "breaks_down")
        self.assertAlmostEqual(sun.target_value, 0.5, places=2)

    def test_uncertainty_widens_the_bandwidth(self):
        p = next(p for p in self.matcher.profile("mars-delta") if p.target_col == "surf_temp_mean_K")
        base = self.rel("surf_temp_mean_K", "temp_mean_c").bandwidth
        self.assertAlmostEqual(p.uncertainty, 5.0)
        self.assertAlmostEqual(p.bandwidth, np.hypot(base, 5.0))

    def test_zero_weight_dimension_has_no_influence(self):
        res = self.matcher.score("mars-delta", dict(BAL, habitability=0.0))
        for p, u in zip(res.used, res.pair_weights):
            if p.dimension == "habitability":
                self.assertEqual(u, 0.0)
        self.assertAlmostEqual(res.pair_weights.sum(), 1.0)

    def test_dimension_weight_does_not_depend_on_variable_count(self):
        res = self.matcher.score("mars-delta", BAL)
        by_dim = {}
        for p, u in zip(res.used, res.pair_weights):
            by_dim[p.dimension] = by_dim.get(p.dimension, 0) + u
        self.assertAlmostEqual(max(by_dim.values()), min(by_dim.values()))

    def test_coverage_is_a_share(self):
        for tid in self.ds.targets.index:
            self.assertTrue(0 < self.matcher.coverage(tid, BAL) < 1)

    def test_explain_matches_score(self):
        res, order = self.matcher.top("moon-ridge", BAL, 1)
        ex = self.matcher.explain("moon-ridge", self.ds.earth.index[order[0]], BAL)
        rebuilt = sum(r["similarity"] * r["weight"] for r in ex["properties"] if r["similarity"] is not None)
        self.assertAlmostEqual(rebuilt, ex["score"], places=9)

    def test_single_property_mode(self):
        used, sims = self.matcher.similarities("mars-ice")
        j = next(j for j, p in enumerate(used) if p.target_col == "weh_fraction")
        self.assertTrue(np.array_equal(self.matcher.single("mars-ice", "weh_fraction"), sims[:, j], equal_nan=True))
        with self.assertRaises(KeyError):
            self.matcher.single("mars-ice", "surf_pressure_Pa")   # not testable on Earth


class TestPlanner(Base):
    def test_minimum_cover_is_minimal(self):
        # Requirements 0..3. No single set covers all; {0,1}+{2,3} does; the greedy pick {0,1,2} would need 2 as well.
        masks = [0b0111, 0b0011, 0b1100, 0b1000]
        combos, exact = planner._minimum_cover(masks, 0b1111, 4)
        self.assertTrue(exact)
        self.assertTrue(all(len(c) == 2 for c in combos))
        self.assertIn((0, 2), combos)

    def test_plan_covers_everything_coverable(self):
        for tid in self.ds.targets.index:
            pl = planner.plan(self.matcher, tid, self.matcher.score(tid, BAL).total)
            covered = {j for s in pl.sites for j in s["covers"]}
            self.assertEqual(covered, set(range(len(pl.requirements))) - set(pl.uncovered))
            self.assertTrue(pl.exact)
            passes = planner.pass_matrix(self.matcher, pl.requirements)
            for s in pl.sites:   # every claimed pass is real
                self.assertEqual([j for j in range(len(pl.requirements)) if passes[s["index"], j]], s["covers"])
            if len(pl.sites) > 1:  # then truly no single site passes them all
                self.assertLess(passes.sum(axis=1).max(), len(covered))

    def test_requirement_bands_stay_physical(self):
        reqs, _ = planner.requirements(self.matcher, "mars-delta")
        water = next(r for r in reqs if r.target_col == "weh_fraction")
        self.assertGreaterEqual(water.lo, 0.0)
        self.assertLessEqual(next(r for r in reqs if r.target_col == "noon_sun_elev_deg").hi, 90.0)


class TestCampaign(Base):
    def _check(self, tid, curve, start):
        reqs, _ = planner.requirements(self.matcher, tid)
        passes = planner.pass_matrix(self.matcher, reqs)
        lat, lon = self.ds.earth["lat"].to_numpy(float), self.ds.earth["lon"].to_numpy(float)
        rows = curve["rows"]
        self.assertEqual(curve["start"], list(start) if start else None)
        for n, row in enumerate(rows, 1):
            self.assertEqual(row["k"], n)                       # one more site per row
            self.assertEqual(len(row["stops"]), n)
            self.assertEqual(len({s["cell_id"] for s in row["stops"]}), n)
            covered = {j for s in row["stops"] for j in range(len(reqs)) if passes[s["index"], j]}
            self.assertEqual(len(covered), row["covered"])        # every claimed pass is real
            self.assertEqual(sorted(row["labels"]), sorted(reqs[j].label for j in covered))
            km, prev = 0.0, start
            for s in row["stops"]:
                self.assertEqual(self.ds.earth.index[s["index"]], s["cell_id"])
                if prev is not None:
                    km += haversine_km(prev[0], prev[1], lat[s["index"]], lon[s["index"]])
                prev = (lat[s["index"]], lon[s["index"]])
            self.assertAlmostEqual(km, row["km"], delta=1.0)     # the printed length is the route's length
        for a, b in zip(rows, rows[1:]):
            self.assertGreaterEqual(b["covered"], a["covered"])  # more sites never cover less
        self.assertEqual(curve["requirements"], [r.label for r in reqs])
        self.assertEqual(len(curve["masks"]), len(self.ds.earth))   # one pass/fail mask per cell, for the map page
        self.assertEqual(len(curve["scores"]), len(self.ds.earth))
        for row in rows:   # the evidence that a row is the best: how many alternatives, how many tie, the runner-up
            self.assertGreaterEqual(row["candidates"], 1)
            self.assertGreaterEqual(row["ties"], 1)
            self.assertIn(row["exact"], (True, False))
            if row["runner_up_km"] is not None:
                self.assertGreaterEqual(row["runner_up_km"], row["km"])
        for i, m in enumerate(curve["masks"]):
            self.assertEqual([j for j in range(len(reqs)) if m >> j & 1], [j for j in range(len(reqs)) if passes[i, j]])
        return reqs, passes

    def test_curve_ends_at_everything_coverable(self):
        for tid in self.ds.targets.index:
            total = self.matcher.score(tid, BAL).total
            curve = campaign.curve(self.matcher, tid, total)
            reqs, passes = self._check(tid, curve, None)
            pl = planner.plan(self.matcher, tid, total)
            coverable = len(pl.requirements) - len(pl.uncovered)
            if curve["rows"]:
                self.assertEqual(curve["rows"][-1]["covered"], coverable)
                self.assertEqual(curve["rows"][0]["covered"], int(passes.sum(axis=1).max()))
                self.assertLessEqual(curve["rows"][-1]["k"], len(pl.sites))   # never worse than the test plan
            else:
                self.assertEqual(coverable, 0)

    def test_start_point_is_part_of_the_route(self):
        tid = self.ds.targets.index[0]
        total = self.matcher.score(tid, BAL).total
        start = (33.3, 44.4)
        curve = campaign.curve(self.matcher, tid, total, start)
        self._check(tid, curve, start)
        free = campaign.curve(self.matcher, tid, total)
        self.assertEqual([r["covered"] for r in curve["rows"]], [r["covered"] for r in free["rows"]])  # coverage does not depend on where you start
        first = curve["rows"][0]["stops"][0]
        self.assertAlmostEqual(curve["rows"][0]["km"], haversine_km(33.3, 44.4, first["lat"], first["lon"]), delta=1.0)

    def test_greedy_fallback_stays_consistent(self):
        tid = self.ds.targets.index[0]
        total = self.matcher.score(tid, BAL).total
        with mock.patch.object(campaign, "MAX_SUBSETS", 1):
            curve = campaign.curve(self.matcher, tid, total, (10.0, 20.0))
        self.assertTrue(curve["rows"])
        self._check(tid, curve, (10.0, 20.0))


class TestCampaignMap(Base):
    def test_map_page_carries_every_target_and_the_sync_protocol(self):
        payload = self.run_["payload"]
        self.assertTrue(payload["campaign_map"])
        html = (self.tmp / "out" / "campaign_map.html").read_text(encoding="utf-8")
        for t in payload["targets"]:
            self.assertIn(json.dumps(t["name"])[1:-1], html)
        for needle in ("earthmimic-start", "earthmimic-set-start", "maplibre-gl", "openfreemap", "World_Imagery", "mousemove"):
            self.assertIn(needle, html)
        for placeholder in ("__DATA__", "__VERSION__"):
            self.assertNotIn(placeholder, html)
        data = campaign_map.map_data(payload)
        self.assertIsInstance(data["sources"], list)
        for t in data["targets"]:   # every requirement carries its band and the Earth column to read the value from
            self.assertEqual([d["label"] for d in t["detail"]], t["requirements"])
            for d in t["detail"]:
                self.assertIn(d["earth_col"], data["earth"]["cols"])
                self.assertLessEqual(d["lo"], d["hi"])
        self.assertEqual(len(data["earth"]["name"]), len(self.ds.earth))
        self.assertTrue(all(data["earth"]["name"]))
        self.assertEqual([t["id"] for t in data["targets"]], list(self.ds.targets.index))


class TestValidation(Base):
    def test_planted_cells_are_recovered(self):
        """Recovery test: cells built to resemble a target must rank near the top for it."""
        fixture = json.loads((self.tmp / "data" / "demo_fixture.json").read_text())
        n = len(self.ds.earth)
        for f in fixture:
            total = np.nan_to_num(self.matcher.score(f["target"], BAL).total, nan=-1)
            rank = int((total > total[self.ds.earth.index.get_loc(f["cell_id"])]).sum()) + 1
            self.assertLessEqual(rank, 0.02 * n, f"{f['cell_id']} ranked {rank} for {f['target']}")

    def test_benchmark_reports_every_known_analog(self):
        b = known_analog_benchmark(self.matcher, BAL)
        self.assertEqual(len(b), len(self.ds.known))
        self.assertTrue((b["percentile"] > 95).all())

    def test_stability_is_reproducible_and_bounded(self):
        a = stability(self.matcher, "mars-delta", BAL, n_runs=60, seed=3)
        b = stability(self.matcher, "mars-delta", BAL, n_runs=60, seed=3)
        self.assertTrue(a.equals(b))
        self.assertTrue(((a["stability"] > 0) & (a["stability"] <= 1)).all())
        self.assertTrue((a["rank_p05"] <= a["rank_p95"]).all())


class TestOutputs(Base):
    def test_files_are_written(self):
        for name in ("report.md", "dashboard.html", "results.json", "relationships.json", "relationships.sqlite", "campaign_map.html"):
            self.assertTrue((self.tmp / "out" / name).stat().st_size > 0)
        html = (self.tmp / "out" / "dashboard.html").read_text()
        self.assertNotIn("__PAYLOAD__", html)
        self.assertNotIn("/*__SCORING_JS__*/", html)
        self.assertNotIn("__LAND__", html)

    def test_demo_locations_fall_on_land(self):
        earth = self.ds.earth
        fixture = {f["cell_id"] for f in json.loads((self.tmp / "data" / "demo_fixture.json").read_text(encoding="utf-8"))}
        natural = earth[~earth.index.isin(fixture)]
        on_land = demo_data._on_land(natural["lat"].to_numpy(), natural["lon"].to_numpy())
        self.assertGreater(on_land.mean(), 0.99)
        self.assertFalse(demo_data._on_land(np.array([0.0, -40.0]), np.array([-30.0, 80.0])).any())   # mid-Atlantic, Indian Ocean

    def test_second_pipeline_run_reuses_the_store(self):
        again = pipeline.run(self.tmp / "data", self.tmp / "out")
        self.assertEqual(sum(r["used"] for r in again["runs"]), 0)
        self.assertEqual(len(again["agent"].accepted()), len(self.agent.accepted()))

    def test_presets_cover_known_dimensions_only(self):
        for p in PRESETS.values():
            self.assertTrue(set(p["weights"]) <= set(DIMENSIONS))

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_browser_scoring_matches_python(self):
        """The dashboard's JavaScript engine must agree with the Python engine."""
        script = (
            "const EM=require(process.argv[1]);const D=JSON.parse(require('fs').readFileSync(process.argv[2]));"
            "const out={};for(const t of D.targets){const u=EM.usedPairs(t);const s=EM.similarities(D.earth.cols,u);"
            "out[t.id]={};for(const k in D.presets){const w=D.presets[k].weights;"
            "out[t.id][k]={total:Array.from(EM.combine(s,EM.pairWeights(u,w),D.params.min_data_share)).map(v=>v===v?v:null),"
            "coverage:EM.coverage(t.profile,w)};}}console.log(JSON.stringify(out));")
        res = subprocess.run(["node", "-e", script, str(ROOT / "dashboard" / "scoring.js"),
                              str(self.tmp / "out" / "results.json")], capture_output=True, text=True, check=True)
        js = json.loads(res.stdout)
        for tid in self.ds.targets.index:
            for key, preset in PRESETS.items():
                py = self.matcher.score(tid, preset["weights"])
                got = np.array([np.nan if v is None else v for v in js[tid][key]["total"]], float)
                self.assertTrue(np.array_equal(np.isnan(got), np.isnan(py.total)))
                # The dashboard payload rounds Earth values to 5 decimals.
                self.assertLess(np.nanmax(np.abs(got - py.total)), 2e-3)
                self.assertAlmostEqual(js[tid][key]["coverage"], py.coverage, places=9)


if __name__ == "__main__":
    unittest.main()


class TestIngest(unittest.TestCase):
    """Real-data readers, exercised on small files written in the exact published formats."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    @staticmethod
    def prp_record(v1, v2, v3, lon, lat, alt, t_avg, t_max, ice):
        """One 210-byte record laid out as in dlre_prp_south.xml (field start bytes 1, 15, 29, ... 198)."""
        from earthmimic.ingest import PRP_FIELDS, PRP_RECORD_BYTES
        values = [*v1, *v2, *v3, lon, lat, alt, t_avg, t_max, ice]
        rec = bytearray(b" " * PRP_RECORD_BYTES)
        for (name, start, length), v in zip(PRP_FIELDS, values):
            text = f"{v:.5f}"[:length].rjust(length).encode()
            rec[start - 1:start - 1 + length] = text
        for start, length in [(f[1], f[2]) for f in PRP_FIELDS[:-1]]:
            rec[start - 1 + length] = ord(",")           # delimiter between fields
        rec[-2:] = b"\r\n"
        return bytes(rec)

    def make_prp(self, path, tilt_deg):
        """Triangles near the lunar south pole, all tilted by `tilt_deg` from horizontal."""
        from earthmimic.ingest import MOON_RADIUS_KM, PRP_RECORD_BYTES
        R, recs = MOON_RADIUS_KM, []
        rise = np.tan(np.radians(tilt_deg)) * 0.2          # over a 0.2 km run
        for k in range(40):
            x0, y0 = 0.3 * (k % 8) - 1.0, 0.3 * (k // 8) - 1.0   # km from the pole, in the polar plane
            z0 = -np.sqrt(R**2 - x0**2 - y0**2)
            v1, v2, v3 = (x0, y0, z0), (x0 + 0.2, y0, z0 - rise), (x0, y0 + 0.2, z0)
            cx, cy = x0 + 0.07, y0 + 0.07
            lat, lon = -90 + np.degrees(np.hypot(cx, cy) / R), np.degrees(np.arctan2(cy, cx)) % 360
            recs.append(self.prp_record(v1, v2, v3, lon, lat, 0.5, 60.0 + k, 200.0 + k, 0.5 if k < 10 else -999.0))
        far = self.prp_record((300, 0, -1700), (300.2, 0, -1700), (300, 0.2, -1700), 0.0, -80.0, 9.0, 300, 390, 0.1)
        header = b"header".ljust(PRP_RECORD_BYTES - 2) + b"\r\n"
        path.write_bytes(header + b"".join(recs) + far)

    def test_diviner_table_is_read_by_byte_position(self):
        from earthmimic import ingest
        path = self.tmp / "prp.tab"
        self.make_prp(path, tilt_deg=12.0)
        sites = pd.DataFrame([dict(target_id="pole", name="Pole", lat=-90.0, lon=0.0, radius_km=5.0),
                              dict(target_id="nowhere", name="Nowhere", lat=-60.0, lon=10.0, radius_km=5.0)])
        out = ingest.read_diviner_prp(path, sites, log=lambda *_: None).set_index("target_id")
        self.assertEqual(out.loc["pole", "n_samples"], 40)                      # the far triangle is excluded
        self.assertAlmostEqual(out.loc["pole", "surf_temp_mean_K"], 60 + 19.5, places=3)
        self.assertAlmostEqual(out.loc["pole", "surf_temp_max_K"], 239.0, places=3)
        self.assertAlmostEqual(out.loc["pole", "shallow_ice_share"], 0.25)       # -999 means "no stable ice"
        self.assertAlmostEqual(out.loc["pole", "slope_deg"], 12.0, delta=0.2)
        self.assertEqual(out.loc["pole", "surf_pressure_Pa"], 0.0)
        self.assertEqual(out.loc["nowhere", "n_samples"], 0)

    def make_mola(self, path, metres_per_degree):
        """Full-size 16 px/deg grid, big-endian int16, rising steadily toward the north."""
        from earthmimic.ingest import MOLA_LINES, MOLA_PPD, MOLA_SAMPLES
        lat = 90 - (np.arange(MOLA_LINES) + 0.5) / MOLA_PPD
        z = np.round(lat * metres_per_degree).astype(">i2")
        np.repeat(z[:, None], MOLA_SAMPLES, axis=1).tofile(path)

    def test_mola_grid_orientation_slope_and_wraparound(self):
        from earthmimic import ingest
        path = self.tmp / "megt.img"
        self.make_mola(path, metres_per_degree=100.0)
        sites = pd.DataFrame([dict(target_id="a", name="A", lat=20.0, lon=77.0, radius_km=25.0),
                              dict(target_id="b", name="B", lat=-30.0, lon=359.99, radius_km=25.0),
                              dict(target_id="c", name="C", lat=-30.0, lon=-0.01, radius_km=25.0)])
        out = ingest.read_mola(path, sites, log=lambda *_: None).set_index("target_id")
        self.assertAlmostEqual(out.loc["a", "elevation_m"], 2000, delta=15)       # north is up, values in metres
        self.assertAlmostEqual(out.loc["b", "elevation_m"], -3000, delta=15)
        km_per_degree = ingest.MARS_RADIUS_KM * np.pi / 180
        expected = np.degrees(np.arctan(100.0 / (km_per_degree * 1000)))
        self.assertAlmostEqual(out.loc["a", "slope_deg"], expected, delta=0.01)
        self.assertAlmostEqual(out.loc["b", "elevation_m"], out.loc["c", "elevation_m"], places=6)   # 360 wraps to 0
        self.assertAlmostEqual(out.loc["a", "surf_pressure_Pa"], 610 * np.exp(-out.loc["a", "elevation_m"] / 10800), places=6)
        with self.assertRaises(IOError):
            (self.tmp / "short.img").write_bytes(b"\0" * 10)
            ingest.read_mola(self.tmp / "short.img", sites)

    def make_tes_albedo(self, path, value=0.22):
        """Full-size 8 px/deg albedo map, little-endian float32, zeros poleward of 80 degrees (no coverage)."""
        from earthmimic.ingest import TES_LINES, TES_PPD, TES_SAMPLES
        lat = 90 - (np.arange(TES_LINES) + 0.5) / TES_PPD
        a = np.where(np.abs(lat) <= 80, value, 0.0).astype("<f4")
        np.repeat(a[:, None], TES_SAMPLES, axis=1).tofile(path)

    def test_tes_albedo_reader_samples_sites_and_skips_gaps(self):
        from earthmimic import ingest
        path = self.tmp / "alb.img"
        self.make_tes_albedo(path, value=0.22)
        sites = pd.DataFrame([dict(target_id="a", name="A", lat=18.0, lon=77.0, radius_km=25.0),
                              dict(target_id="b", name="B", lat=-30.0, lon=359.99, radius_km=25.0),
                              dict(target_id="c", name="C", lat=-88.0, lon=0.0, radius_km=25.0)])
        out = ingest.read_tes_albedo(path, sites, log=lambda *_: None).set_index("target_id")
        self.assertAlmostEqual(out.loc["a", "albedo"], 0.22, places=4)
        self.assertAlmostEqual(out.loc["b", "albedo"], 0.22, places=4)            # 360 wraps to 0
        self.assertTrue(np.isnan(out.loc["c", "albedo"]))                         # zeros = no TES coverage
        with self.assertRaises(IOError):
            (self.tmp / "alb_short.img").write_bytes(b"\0" * 10)
            ingest.read_tes_albedo(self.tmp / "alb_short.img", sites)

    def make_lola_albedo(self, path, upper=0.20, lower=0.40):
        """Full-size 844 x 844 south polar albedo map. The upper image half is y > 0, the lon-0 side."""
        from earthmimic.ingest import LDAM_SIZE
        a = np.full((LDAM_SIZE, LDAM_SIZE), lower, "<f4")
        a[: LDAM_SIZE // 2, :] = upper
        a.tofile(path)

    def test_lola_albedo_polar_geometry(self):
        from earthmimic import ingest
        path = self.tmp / "ldam.img"
        self.make_lola_albedo(path, upper=0.20, lower=0.40)
        sites = pd.DataFrame([dict(target_id="a", name="A", lat=-80.0, lon=0.0, radius_km=10.0),
                              dict(target_id="b", name="B", lat=-80.0, lon=180.0, radius_km=10.0),
                              dict(target_id="c", name="C", lat=-40.0, lon=0.0, radius_km=10.0)])
        out = ingest.read_lola_albedo(path, sites, log=lambda *_: None).set_index("target_id")
        # lon 0 has y = +rho, which lies in the low-line (upper) half of the image.
        self.assertAlmostEqual(out.loc["a", "albedo"], 0.20, places=4)
        self.assertAlmostEqual(out.loc["b", "albedo"], 0.40, places=4)
        self.assertTrue(np.isnan(out.loc["c", "albedo"]))      # north of the map's coverage
        with self.assertRaises(IOError):
            (self.tmp / "ldam_short.img").write_bytes(b"\0" * 10)
            ingest.read_lola_albedo(self.tmp / "ldam_short.img", sites)

    @staticmethod
    def power_reply(land=True, t=15.0, p=98.0):
        months = lambda base: {m: base + i for i, m in enumerate(
            ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])} | {"ANN": base + 5.5}
        return {"type": "Feature", "properties": {"parameter": {
            "TS": months(t), "T2M": months(t - 1), "T2M_MAX": months(t + 6), "T2M_RANGE": months(8.0 + (t + 30) / 10), "WS10M": months(3.0 + (t + 30) / 20),
            "PS": {m: p for m in months(0)}, "GWETTOP": months(0.3) if land else {m: -999.0 for m in months(0)},
            "ALLSKY_SFC_UV_INDEX": months(5.0), "PRECTOTCORR": months(1.0),
            "ALLSKY_SRF_ALB": {m: 0.1 + (t + 30) / 300 for m in months(0)},
            "AOD_55": {m: 0.05 + (t + 30) / 200 for m in months(0)}}}}

    def test_power_reply_parsing_and_fill_values(self):
        from earthmimic import ingest
        flat = ingest.parse_power(self.power_reply())
        self.assertAlmostEqual(flat["TS"], 20.5)
        self.assertAlmostEqual(flat["T2M_MAX_MONTH_MAX"], 15 + 6 + 11)
        self.assertTrue(np.isnan(ingest.parse_power(self.power_reply(land=False))["GWETTOP"]))
        with self.assertRaises(ValueError):
            ingest.parse_power({"messages": ["error"]})
        url = ingest.power_url(12.5, -70.25, ["T2M", "PS"])
        self.assertTrue(url.startswith("https://power.larc.nasa.gov/api/temporal/climatology/point?"))
        for part in ("parameters=T2M,PS", "community=AG", "longitude=-70.2500", "latitude=12.5000", "format=JSON"):
            self.assertIn(part, url)

    def test_unknown_power_parameter_is_dropped_not_fatal(self):
        import urllib.error
        from earthmimic import ingest

        def get(url):
            if "GWETTOP" in url:
                raise urllib.error.HTTPError(url, 422, "unprocessable", {}, None)
            return self.power_reply()
        ok = ingest.working_power_parameters(0, 0, ["T2M", "GWETTOP", "PS"], get, log=lambda *_: None)
        self.assertEqual(ok, ["T2M", "PS"])

    @staticmethod
    def terrarium_png(elevation):
        """Encode an elevation array (metres) as a terrarium PNG tile."""
        import io
        from PIL import Image
        v = np.asarray(elevation, float) + 32768
        rgb = np.dstack([np.floor(v / 256), np.floor(v) % 256, np.floor((v % 1) * 256)]).astype(np.uint8)
        buf = io.BytesIO()
        Image.fromarray(rgb, "RGB").save(buf, "PNG")
        return buf.getvalue()

    def tile_server(self, metres_per_pixel_east):
        """Fake tile server: the ground rises steadily toward the east, continuous across tile edges."""
        requested = []

        def get_bytes(url):
            z, x, y = (int(v) for v in url.split("/terrarium/")[1].replace(".png", "").split("/"))
            requested.append((z, x, y))
            gx = x * 256 + np.arange(256)
            return self.terrarium_png(np.tile(metres_per_pixel_east * gx, (256, 1)) - 500.0)
        return get_bytes, requested

    def test_builtin_png_reader_matches_pillow(self):
        import io
        from PIL import Image
        from earthmimic.ingest import _decode_png_builtin
        rng = np.random.default_rng(0)
        smooth = (np.add.outer(np.arange(64), np.arange(80)) % 256).astype(np.uint8)
        rgb = np.dstack([smooth, smooth[::-1], rng.integers(0, 255, smooth.shape, dtype=np.uint8)])
        for mode, img in (("RGB", Image.fromarray(rgb, "RGB")), ("RGBA", Image.fromarray(rgb, "RGB").convert("RGBA")),
                          ("P", Image.fromarray(rgb, "RGB").quantize(40)), ("L", Image.fromarray(smooth, "L")),
                          ("P4", Image.fromarray(rgb, "RGB").quantize(12))):
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            expected = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
            self.assertTrue(np.array_equal(_decode_png_builtin(buf.getvalue()), expected), mode)

    def test_terrarium_encoding_round_trip(self):
        from earthmimic import ingest
        elev = np.array([[-431.5, 0.0], [8848.25, 1234.75]])
        got = ingest.terrarium_to_metres(ingest.decode_png(self.terrarium_png(elev)))
        self.assertTrue(np.allclose(got, elev, atol=1 / 256))

    def test_earth_slope_is_measured_over_the_mars_baseline(self):
        from earthmimic import ingest
        get_bytes, requested = self.tile_server(metres_per_pixel_east=40.0)
        lat, lon = 30.0, 10.0
        z = ingest.terrain_zoom(lat)
        px_m = ingest.EARTH_CIRCUMFERENCE_KM * 1000 * np.cos(np.radians(lat)) / (256 * 2**z)
        self.assertLess(abs(px_m / 1000 - ingest.TERRAIN_BASELINE_KM) / ingest.TERRAIN_BASELINE_KM, 0.45)
        out = ingest.terrain_stats(lat, lon, 25.0, self.tmp / "tiles_a", get_bytes)
        self.assertAlmostEqual(out["slope_deg"], np.degrees(np.arctan(40.0 / px_m)), places=3)
        self.assertGreater(out["relief_m"], 0)
        self.assertEqual(len(requested), 1)
        ingest.terrain_stats(lat, lon, 25.0, self.tmp / "tiles_a", get_bytes)
        self.assertEqual(len(requested), 1)                                  # second call reads the cached tile
        # A site sitting on a tile edge needs the neighbouring tile and must give the same slope.
        edge_lon = -180 + 360 * 20 / 2**z + 0.01
        edge = ingest.terrain_stats(lat, edge_lon, 25.0, self.tmp / "tiles_b", get_bytes)
        self.assertGreaterEqual(len({(x, y) for _, x, y in requested[1:]}), 2)
        self.assertAlmostEqual(edge["slope_deg"], out["slope_deg"], places=3)
        self.assertEqual(ingest.terrain_stats(86.0, 0.0, 25.0, self.tmp / "tiles_c", get_bytes), {})   # beyond Web Mercator

    def test_certificate_failure_gives_instructions_not_a_traceback(self):
        import ssl
        import urllib.error
        from earthmimic import ingest

        def refuse(req, timeout, context):
            raise urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))
        dest = self.tmp / "cert" / "file.tab"
        with mock.patch("urllib.request.urlopen", refuse):
            with self.assertRaises(ingest.CertificateProblem) as caught:
                ingest.download("https://pds-geosciences.wustl.edu/x/file.tab", dest, 10, log=lambda *_: None)
            with self.assertRaises(ingest.CertificateProblem):       # not retried, not swallowed as "no data"
                ingest.fetch_power(pd.DataFrame([dict(cell_id="a", lat=0.0, lon=0.0)]), self.tmp / "cert" / "p",
                                   pause=0, log=lambda *_: None)
        text = str(caught.exception)
        for part in ("pds-geosciences.wustl.edu", "pip install truststore", "file.tab", "--no-verify-ssl"):
            self.assertIn(part, text)

    def test_operating_system_certificate_checking_is_used_when_available(self):
        import ssl
        import truststore
        from earthmimic import ingest
        self.assertIsInstance(ingest._ssl_context(), truststore.SSLContext)
        ingest.set_ssl_verification(False)
        try:
            self.assertEqual(ingest._ssl_context().verify_mode, ssl.CERT_NONE)
        finally:
            ingest.set_ssl_verification(True)

    def test_hand_entered_mars_climate_is_merged_and_cited(self):
        from earthmimic import ingest
        sites = pd.DataFrame([dict(target_id="m1", body="Mars", name="One", lat=0.0, lon=0.0, radius_km=25, description=""),
                              dict(target_id="m2", body="Mars", name="Two", lat=10.0, lon=5.0, radius_km=25, description="")])
        mola = pd.DataFrame([dict(target_id="m1", n_samples=9, slope_deg=1.0, relief_m=50.0, elevation_m=-2000.0, surf_pressure_Pa=734.0),
                             dict(target_id="m2", n_samples=9, slope_deg=2.0, relief_m=80.0, elevation_m=1000.0, surf_pressure_Pa=556.0)])
        path = self.tmp / "mars_climate.csv"
        ingest.write_mars_climate_template(path, sites)
        self.assertTrue(ingest.read_mars_climate(path)[0].empty)            # an untouched template adds nothing
        df = pd.read_csv(path, comment="#").astype({"source": object})
        df.loc[0, ["surf_temp_mean_K", "temp_swing_K", "surf_pressure_Pa", "wind_ms", "dust_tau", "source"]] = \
            [215.0, 70.0, 700.0, 6.0, 0.5, "MCD v6.1, climatology scenario"]
        path.write_text(ingest.MARS_CLIMATE_HELP + df.to_csv(index=False))
        climate, source = ingest.read_mars_climate(path)
        t, meta = ingest.targets_table(None, None, sites, mola, climate, source)
        t = t.set_index("target_id")
        self.assertEqual(t.loc["m1", "surf_pressure_Pa"], 700.0)             # database value replaces the estimate
        self.assertEqual(t.loc["m2", "surf_pressure_Pa"], 556.0)             # estimate kept where nothing was entered
        self.assertEqual(t.loc["m1", "dust_tau"], 0.5)
        by = {m["name"]: m for m in meta}
        self.assertEqual(by["wind_ms"]["version"], "MCD v6.1, climatology scenario")
        self.assertIn("MCD v6.1", by["surf_pressure_Pa"]["version"])

    def test_fetch_builds_a_folder_the_pipeline_runs_on(self):
        from earthmimic import ingest
        raw, dl = self.tmp / "real_raw", self.tmp / "real_raw" / "downloads"
        dl.mkdir(parents=True)
        get_bytes, _ = self.tile_server(metres_per_pixel_east=3.0)
        self.make_prp(dl / "dlre_prp_south.tab", tilt_deg=8.0)
        self.make_mola(dl / "megt90n000eb.img", metres_per_degree=50.0)
        self.make_tes_albedo(dl / "global_albedo_8ppd.img")
        self.make_lola_albedo(dl / "ldam_50s_3000m_float.img")
        calls = []

        def get(url):
            calls.append(url)
            lat = float(url.split("latitude=")[1].split("&")[0])
            lon = float(url.split("longitude=")[1].split("&")[0])
            return self.power_reply(land=not (abs(lon) > 150), t=28 - 0.6 * abs(lat), p=101.0 - 0.3 * abs(lat))
        prp_size = (dl / "dlre_prp_south.tab").stat().st_size
        with mock.patch.dict(ingest.SOURCES["diviner_prp_south"], {"bytes": prp_size}):
            ingest.write_default_site_files(raw / "sites", grid_step=10.0)
            moon = pd.read_csv(raw / "sites" / "moon_sites.csv")
            moon.loc[0, ["lat", "lon"]] = [-90.0, 0.0]        # put one site on the test triangles
            moon.to_csv(raw / "sites" / "moon_sites.csv", index=False)
            ingest.fetch(raw, get=get, get_bytes=get_bytes, pause=0, log=lambda *_: None)
            # Fill in Mars climate for one site, as a user would from the climate database.
            cpath = raw / "sites" / "mars_climate.csv"
            c = pd.read_csv(cpath, comment="#").astype({"source": object})
            row = c.index[c["target_id"] == "mars-jezero"][0]
            c.loc[row, ["surf_temp_mean_K", "temp_swing_K", "surf_pressure_Pa", "wind_ms", "dust_tau", "source"]] = \
                [215.0, 70.0, 700.0, 6.0, 0.5, "test values"]
            cpath.write_text(ingest.MARS_CLIMATE_HELP + c.to_csv(index=False))
            n_calls = len(calls)
            ingest.fetch(raw, get=get, get_bytes=get_bytes, pause=0, log=lambda *_: None)   # second time: everything comes from the cache
        self.assertEqual(len(calls), n_calls)

        earth = pd.read_csv(raw / "earth_cells.csv")
        from earthmimic.demo_data import _on_land
        grid = earth[earth["cell_id"].str.startswith("G")]
        self.assertTrue(_on_land(grid["lat"].to_numpy(float), grid["lon"].to_numpy(float)).all())  # grid cells are on land
        self.assertIn("K04", set(earth["cell_id"]))           # named sites (Mauna Kea) are kept even where POWER has no soil wetness
        self.assertGreater(len(earth), 100)
        targets = pd.read_csv(raw / "targets.csv")
        self.assertEqual(set(targets["body"]), {"Moon", "Mars"})

        result = pipeline.run(self.tmp / "real", self.tmp / "real_out", raw_dir=raw, fresh_store=True)
        self.assertFalse(result["dataset"].synthetic)
        accepted = {r.id for r in result["agent"].accepted()}
        for rid in ("surf_temp_mean_K__temp_mean_c", "surf_pressure_Pa__pressure_kpa",
                    "surf_temp_max_K__warm_month_high_c", "grazing_sun_share__grazing_sun_share",
                    "liquid_window_c__liquid_window_c", "slope_deg__slope_deg", "relief_m__relief_m",
                    "dust_tau__dust_aod", "temp_swing_K__temp_swing_c", "wind_pressure_pa__wind_pressure_pa"):
            self.assertIn(rid, accepted)
        self.assertIn("slope_deg", earth.columns)
        self.assertTrue(earth.loc[earth["lat"].abs() < 80, "slope_deg"].notna().all())
        status = {p.target_col: p.status for p in result["matcher"].profile("mars-jezero")}
        self.assertEqual(status["surf_pressure_Pa"], "breaks_down")
        self.assertIn(status["slope_deg"], ("match", "partial"))
        self.assertNotEqual(status["surf_temp_mean_K"], "not_tested")  # climate was entered for this site
        other = {p.target_col: p.status for p in result["matcher"].profile("mars-gale")}
        self.assertEqual(other["surf_temp_mean_K"], "not_tested")      # ...and not for this one
        self.assertNotIn("Synthetic", (self.tmp / "real_out" / "report.md").read_text())
        # A site with nothing testable must not break the run or fake a ranking.
        empty = [t for t in result["dataset"].targets.index if not result["matcher"].similarities(t)[0]]
        for tid in empty:
            self.assertTrue(np.isnan(result["matcher"].score(tid, BAL).total).all())
        self.assertTrue(stability(result["matcher"], empty[0], BAL, n_runs=5).empty if empty else True)
