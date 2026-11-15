# EarthMimic run report

Earth cells: 494. Targets: 13.

## Data cleaning

- Earth cells: 494 rows in, 494 rows out.
- Target sites: 13 rows in, 13 rows out.

| Table | Rule | Column | Count | Action |
|---|---|---|---|---|
| Earth cells | Extreme outlier | wind_ms | 4 | flagged, value kept |
| Earth cells | Extreme outlier | precip_mm_day | 4 | flagged, value kept |

## Relationship agent

- Run 21: 0 of 15 tool calls used.
- Run 22: 0 of 15 tool calls used.

| Target column | Earth column | Status | Confidence | Deciding check |
|---|---|---|---|---|
| surf_temp_mean_K | temp_mean_c | accepted | 1.00 | All checks passed. |
| temp_swing_K | temp_swing_c | accepted | 1.00 | All checks passed. |
| wind_ms | wind_ms | accepted (input only) | 1.00 | Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead. |
| dust_tau | dust_aod | accepted | 1.00 | All checks passed. |
| uvb_wm2 | uvb_wm2 | accepted | 1.00 | All checks passed. |
| surf_temp_max_K | warm_month_high_c | accepted | 0.60 | Related but not identical concepts; confidence starts at 0.60. |
| shallow_ice_share | frozen_ground_share | accepted | 0.60 | Related but not identical concepts; confidence starts at 0.60. |
| subsurface_h2o_share | soil_wetness | accepted | 0.50 | Related but not identical concepts; confidence starts at 0.50. |
| precip_mm_day | precip_mm_day | accepted | 1.00 | All checks passed. |
| slope_deg | slope_deg | accepted | 1.00 | All checks passed. |
| roughness_deg | roughness_deg | accepted | 0.50 | Moves almost in step with 'slope_deg' (rank correlation +0.97); counted at half weight so the same signal is not counted twice. |
| relief_m | relief_m | accepted | 0.50 | Moves almost in step with 'slope_deg' (rank correlation +0.98); counted at half weight so the same signal is not counted twice. |
| albedo | albedo | accepted | 1.00 | All checks passed. |
| surf_pressure_Pa | pressure_kpa | accepted | 1.00 | All checks passed. |
| elevation_m | elevation_m | denied | 0.00 | Elevation depends on a local reference. Measured from each body’s own reference surface. |
| grazing_sun_share | grazing_sun_share | accepted | 1.00 | All checks passed. |
| insolation_wm2 | insolation_wm2 | accepted | 0.50 | Moves almost in step with 'grazing_sun_share' (rank correlation -0.97); counted at half weight so the same signal is not counted twice. |
| daily_high_c | daily_high_c | accepted | 0.50 | Moves almost in step with 'temp_mean_c' (rank correlation +0.99); counted at half weight so the same signal is not counted twice. |
| daily_low_c | daily_low_c | accepted | 0.50 | Moves almost in step with 'temp_mean_c' (rank correlation +0.98); counted at half weight so the same signal is not counted twice. |
| liquid_window_c | liquid_window_c | accepted | 1.00 | All checks passed. |
| thaw_share | thaw_share | accepted | 1.00 | All checks passed. |
| wind_pressure_pa | wind_pressure_pa | accepted | 1.00 | All checks passed. |

## Known-analog check (balanced weights)

4 of 10 known analogs rank in the top 5% of Earth cells (random ranking would give about 0.5). Median percentile: 90.6.

| Known analog | Best target | Rank | Percentile |
|---|---|---|---|
| Atacama Desert | Gale crater (Curiosity) | 8 | 98.6 |
| McMurdo Dry Valleys | Jezero crater (Perseverance) | 49 | 90.3 |
| Haughton crater, Devon Island | Vastitas Borealis (Phoenix) | 46 | 90.9 |
| Askja, Iceland | Shackleton crater floor | 18 | 96.6 |
| Mauna Kea, Hawaii | Gale crater (Curiosity) | 143 | 71.3 |
| Rio Tinto, Spain | Jezero crater (Perseverance) | 104 | 79.1 |
| Utah desert (MDRS) | Jezero crater (Perseverance) | 95 | 81.0 |
| Dallol, Ethiopia | Jezero crater (Perseverance) | 23 | 95.5 |
| Svalbard | Jezero crater (Perseverance) | 195 | 60.7 |
| Qaidam Basin | Arcadia Planitia | 6 | 99.0 |

## Moon: Shackleton crater rim

Rim of Shackleton crater near the south pole.

Earth can test 25% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-209 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Relief within the site.** The target value (1.21e+03 m) is far outside Earth’s range (1.94 m to 753 m). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean slope.** The target value (24.7°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (8.77°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 52.9°E) | 0.559 | 75% | Temperature extremes |
| 2 | Hot hyper-arid desert plain, Sahara and North Africa (25.0°N, 30.5°E) | 0.551 | 71% | Geology and surface materials |
| 3 | Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 47.1°E) | 0.548 | 68% | Geology and surface materials |
| 4 | Hot hyper-arid desert plain, Sahara and North Africa (30.0°N, 5.8°E) | 0.545 | 66% | Temperature extremes |
| 5 | Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 47.6°E) | 0.544 | 65% | Temperature extremes |

Best candidates more than 500 km from any known analog: Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 52.9°E) at 0.559; Hot hyper-arid desert plain, Sahara and North Africa (25.0°N, 30.5°E) at 0.551; Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 47.1°E) at 0.548.

Test plan: 7 requirements can be tested on Earth. The best single site passes 5. 2 site(s) together pass 7 (smallest possible set).

- St. Elias Mountains, Alaska (60.5°N, 139.5°W): area with ice stable in the top metre, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 52.9°E): annual maximum surface temperature, precipitation, surface albedo

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 5 of 7 | 0 | 54% | 0 | Karakoram, Baltoro (35.7°N, 76.5°E) |
| 2 | 6 of 7 | 3 | 54% | 7,100 | Karakoram, Baltoro (35.7°N, 76.5°E) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 3 | 7 of 7 | 3 | 54% | 9,990 | Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 52.9°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 4 | 7 of 7 | 4 | 55% | 12,362 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Karakoram, Baltoro (35.7°N, 76.5°E) -> Hot hyper-arid desert plain, Arabia and the Middle East (20.0°N, 52.9°E) -> Hot hyper-arid desert plain, Sahara and North Africa (25.0°N, 30.5°E) |

## Moon: Shackleton to de Gerlache ridge

Sunlit ridge between Shackleton and de Gerlache craters.

Earth can test 30% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-148 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean slope.** The target value (9.72°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (5.05°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.607 | 66% | Geology and surface materials |
| 2 | Cold humid hills, Siberia (60.0°N, 150.0°E) | 0.593 | 62% | Geology and surface materials |
| 3 | Hot hyper-arid desert plain, Arabia and the Middle East (15.0°N, 46.3°E) | 0.587 | 62% | Temperature extremes |
| 4 | Hot hyper-arid hills, Sahara and North Africa (30.0°N, 34.8°E) | 0.584 | 60% | Geology and surface materials |
| 5 | Temperate semi-arid mountains, Arabia and the Middle East (40.0°N, 42.5°E) | 0.584 | 51% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.607; Cold humid hills, Siberia (60.0°N, 150.0°E) at 0.593; Hot hyper-arid desert plain, Arabia and the Middle East (15.0°N, 46.3°E) at 0.587.

Test plan: 8 requirements can be tested on Earth. The best single site passes 5. 2 site(s) together pass 8 (smallest possible set).

- Karakoram, Baltoro (35.7°N, 76.5°E): precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Temperate semi-arid hills, Central and East Asia (40.0°N, 114.5°E): annual maximum surface temperature, area with ice stable in the top metre, relief within the site

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 5 of 8 | 0 | 61% | 0 | Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 2 | 7 of 8 | 2 | 58% | 6,044 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Cold semi-arid plain, Central and East Asia (45.0°N, 116.5°E) |
| 3 | 8 of 8 | 4 | 58% | 9,543 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Cold semi-arid plain, Central and East Asia (45.0°N, 116.5°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |
| 4 | 8 of 8 | 6 | 58% | 12,543 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Cold semi-arid plain, Central and East Asia (45.0°N, 116.5°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) -> Temperate semi-arid mountains, Arabia and the Middle East (40.0°N, 42.5°E) |
| 5 | 8 of 8 | 7 | 58% | 10,716 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Cold humid hills, Siberia (60.0°N, 150.0°E) -> Cold semi-arid plain, Central and East Asia (45.0°N, 116.5°E) -> Cold arid desert plain, Siberia (50.0°N, 93.9°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |

## Moon: Shackleton crater floor

Permanently shadowed crater floor.

Earth can test 27% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-221 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-169 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (11.8 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean slope.** The target value (12.4°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (9.06°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.818 | 100% | Water and ice |
| 2 | Polar semi-arid hills, Siberia (65.0°N, 144.0°E) | 0.759 | 100% | Geology and surface materials |
| 3 | Polar semi-arid hills, Siberia (65.0°N, 132.0°E) | 0.726 | 100% | Water and ice |
| 4 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.699 | 87% | Geology and surface materials |
| 5 | Oymyakon, Siberia (63.5°N, 142.8°E) | 0.659 | 81% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.818; Polar semi-arid hills, Siberia (65.0°N, 144.0°E) at 0.759; Polar semi-arid hills, Siberia (65.0°N, 132.0°E) at 0.726.

Test plan: 7 requirements can be tested on Earth. The best single site passes 5. 2 site(s) together pass 7 (smallest possible set).

- Eureka, Ellesmere Island (80.0°N, 85.9°W): area with ice stable in the top metre, precipitation, relief within the site, surface albedo, share of the day above freezing
- Karakoram, Baltoro (35.7°N, 76.5°E): precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 5 of 7 | 0 | 82% | 0 | Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 2 | 7 of 7 | 3 | 76% | 7,100 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Karakoram, Baltoro (35.7°N, 76.5°E) |
| 3 | 7 of 7 | 6 | 71% | 9,855 | Karakoram, Baltoro (35.7°N, 76.5°E) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) -> St. Elias Mountains, Alaska (60.5°N, 139.5°W) |
| 4 | 7 of 7 | 7 | 72% | 11,756 | Karakoram, Baltoro (35.7°N, 76.5°E) -> Polar semi-arid hills, Siberia (65.0°N, 144.0°E) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) -> St. Elias Mountains, Alaska (60.5°N, 139.5°W) |

## Moon: Malapert massif

High massif with long sunlight and Earth visibility.

Earth can test 25% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-129 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (64 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (46.4% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (31.3 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean slope.** The target value (18°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (6.17°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.
- **Relief within the site.** The target value (785 m) is just beyond anything on Earth (1.94 m to 753 m). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tien Shan (42.0°N, 80.0°E) | 0.686 | 100% | Geology and surface materials |
| 2 | Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) | 0.646 | 99% | Geology and surface materials |
| 3 | Cold semi-arid mountains, Central and East Asia (45.0°N, 81.2°E) | 0.605 | 79% | Geology and surface materials |
| 4 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.598 | 69% | Water and ice |
| 5 | Cold humid mountains, Alaska and Yukon (65.0°N, 132.0°W) | 0.592 | 81% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Tien Shan (42.0°N, 80.0°E) at 0.686; Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) at 0.646; Cold semi-arid mountains, Central and East Asia (45.0°N, 81.2°E) at 0.605.

Test plan: 7 requirements can be tested on Earth. The best single site passes 5. 2 site(s) together pass 7 (smallest possible set).

- Tien Shan (42.0°N, 80.0°E): precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Temperate semi-arid mountains, Central and East Asia (35.0°N, 70.2°E): area with ice stable in the top metre, mean slope, terrain roughness, relief within the site, surface albedo

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 5 of 7 | 0 | 69% | 0 | Tien Shan (42.0°N, 80.0°E) |
| 2 | 7 of 7 | 3 | 62% | 1,155 | Tien Shan (42.0°N, 80.0°E) -> Temperate semi-arid mountains, Central and East Asia (35.0°N, 70.2°E) |
| 3 | 7 of 7 | 5 | 63% | 8,948 | Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) -> Tien Shan (42.0°N, 80.0°E) -> Temperate semi-arid mountains, Central and East Asia (35.0°N, 70.2°E) |
| 4 | 7 of 7 | 6 | 62% | 8,952 | Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) -> Cold semi-arid mountains, Central and East Asia (45.0°N, 81.2°E) -> Tien Shan (42.0°N, 80.0°E) -> Temperate semi-arid mountains, Central and East Asia (35.0°N, 70.2°E) |

## Moon: Haworth crater

Large permanently shadowed crater.

Earth can test 29% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-234 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-180 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (21.1 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (4.3°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.918 | 100% | Geology and surface materials |
| 2 | Polar semi-arid hills, Siberia (65.0°N, 144.0°E) | 0.867 | 100% | Geology and surface materials |
| 3 | Polar semi-arid hills, Siberia (65.0°N, 132.0°E) | 0.858 | 100% | Geology and surface materials |
| 4 | Tien Shan (42.0°N, 80.0°E) | 0.791 | 82% | Water and ice |
| 5 | Polar semi-arid hills, Siberia (65.0°N, 168.0°E) | 0.788 | 92% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.918; Polar semi-arid hills, Siberia (65.0°N, 144.0°E) at 0.867; Polar semi-arid hills, Siberia (65.0°N, 132.0°E) at 0.858.

Test plan: 7 requirements can be tested on Earth. The best single site passes 6. 2 site(s) together pass 7 (smallest possible set).

- Eureka, Ellesmere Island (80.0°N, 85.9°W): area with ice stable in the top metre, precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Polar semi-arid hills, Siberia (65.0°N, 144.0°E): area with ice stable in the top metre, mean slope, relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 6 of 7 | 0 | 92% | 0 | Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 2 | 7 of 7 | 4 | 89% | 3,592 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Polar semi-arid hills, Siberia (65.0°N, 144.0°E) |
| 3 | 7 of 7 | 7 | 82% | 5,924 | Cold humid mountains, Alaska and Yukon (65.0°N, 132.0°W) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Oymyakon, Siberia (63.5°N, 142.8°E) |

## Moon: Cabeus crater

Shadowed crater where LCROSS detected water.

Earth can test 30% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-205 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (42.1% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (36.4 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean slope.** The target value (7.4°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (4.63°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tien Shan (42.0°N, 80.0°E) | 0.862 | 100% | Temperature extremes |
| 2 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.854 | 100% | Temperature extremes |
| 3 | Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) | 0.793 | 97% | Geology and surface materials |
| 4 | Cold humid mountains, Alaska and Yukon (65.0°N, 132.0°W) | 0.755 | 98% | Geology and surface materials |
| 5 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.737 | 97% | Temperature extremes |

Best candidates more than 500 km from any known analog: Tien Shan (42.0°N, 80.0°E) at 0.862; Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.854; Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) at 0.793.

Test plan: 8 requirements can be tested on Earth. The best single site passes 7. 2 site(s) together pass 8 (smallest possible set).

- Tien Shan (42.0°N, 80.0°E): annual maximum surface temperature, area with ice stable in the top metre, precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W): annual maximum surface temperature, mean slope, terrain roughness, relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 7 of 8 | 0 | 86% | 0 | Tien Shan (42.0°N, 80.0°E) |
| 2 | 8 of 8 | 5 | 83% | 7,793 | Tien Shan (42.0°N, 80.0°E) -> Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) |
| 3 | 8 of 8 | 7 | 84% | 9,426 | Tien Shan (42.0°N, 80.0°E) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) |
| 4 | 8 of 8 | 8 | 81% | 11,190 | Cold humid mountains, Alaska and Yukon (60.0°N, 150.0°W) -> Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Tien Shan (42.0°N, 80.0°E) -> Cold humid high mountains, Central and East Asia (30.0°N, 92.9°E) |

## Moon: Faustini crater

Permanently shadowed crater.

Earth can test 29% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-229 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-184 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (22.8 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (3.67°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.881 | 100% | Geology and surface materials |
| 2 | Polar semi-arid hills, Siberia (65.0°N, 144.0°E) | 0.863 | 100% | Geology and surface materials |
| 3 | Polar semi-arid hills, Siberia (70.0°N, 136.8°E) | 0.827 | 100% | Geology and surface materials |
| 4 | Oymyakon, Siberia (63.5°N, 142.8°E) | 0.822 | 99% | Geology and surface materials |
| 5 | Polar semi-arid hills, Siberia (65.0°N, 132.0°E) | 0.818 | 100% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.881; Polar semi-arid hills, Siberia (65.0°N, 144.0°E) at 0.863; Polar semi-arid hills, Siberia (70.0°N, 136.8°E) at 0.827.

Test plan: 7 requirements can be tested on Earth. The best single site passes 6. 2 site(s) together pass 7 (smallest possible set).

- Eureka, Ellesmere Island (80.0°N, 85.9°W): area with ice stable in the top metre, precipitation, mean slope, terrain roughness, surface albedo, share of the day above freezing
- Oymyakon, Siberia (63.5°N, 142.8°E): area with ice stable in the top metre, precipitation, mean slope, relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 6 of 7 | 0 | 88% | 0 | Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 2 | 7 of 7 | 5 | 85% | 3,772 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Oymyakon, Siberia (63.5°N, 142.8°E) |
| 3 | 7 of 7 | 6 | 84% | 3,902 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Polar semi-arid hills, Siberia (70.0°N, 136.8°E) -> Oymyakon, Siberia (63.5°N, 142.8°E) |
| 4 | 7 of 7 | 7 | 83% | 9,246 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Polar semi-arid hills, Siberia (70.0°N, 136.8°E) -> Oymyakon, Siberia (63.5°N, 142.8°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |

## Mars: Jezero crater (Perseverance)

Ancient river delta in an impact crater.

Earth can test 43% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (62.2 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-50 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.716 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-81.2 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.2 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.
- **Wind force on surfaces.** The target value (0.0601 Pa) is far outside Earth’s range (0.258 Pa to 95.3 Pa). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (170 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Cold hyper-arid high plateau, Central and East Asia (35.0°N, 82.4°E) | 0.648 | 88% | Terrain and topography |
| 2 | Changtang, Tibetan Plateau (34.5°N, 88.0°E) | 0.627 | 76% | Geology and surface materials |
| 3 | Cold semi-arid high plateau, Central and East Asia (30.0°N, 87.1°E) | 0.616 | 78% | Geology and surface materials |
| 4 | Cold arid high plateau, Central and East Asia (35.0°N, 88.5°E) | 0.613 | 63% | Geology and surface materials |
| 5 | Ojos del Salado, Andes (27.1°S, 68.5°W) | 0.607 | 60% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Cold hyper-arid high plateau, Central and East Asia (35.0°N, 82.4°E) at 0.648; Changtang, Tibetan Plateau (34.5°N, 88.0°E) at 0.627; Cold semi-arid high plateau, Central and East Asia (30.0°N, 87.1°E) at 0.616.

Test plan: 10 requirements can be tested on Earth. The best single site passes 7. 2 site(s) together pass 10 (smallest possible set).

- Hot hyper-arid hills, Arabia and the Middle East (30.0°N, 58.1°E): precipitation, mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon
- Polar ice sheet, Antarctica (75.0°S, 66.3°E): mean surface temperature, precipitation, mean solar energy flux, typical daily high, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 7 of 10 | 0 | 53% | 0 | McMurdo Dry Valleys (77.5°S, 162.0°E) |
| 2 | 9 of 10 | 4 | 59% | 13,552 | Cold hyper-arid high plateau, Central and East Asia (35.0°N, 82.4°E) -> McMurdo Dry Valleys (77.5°S, 162.0°E) |
| 3 | 10 of 10 | 6 | 53% | 13,717 | Hot hyper-arid hills, Arabia and the Middle East (30.0°N, 58.1°E) -> Polar ice sheet, Antarctica (80.0°S, 152.3°E) -> McMurdo Dry Valleys (77.5°S, 162.0°E) |
| 4 | 10 of 10 | 8 | 56% | 16,057 | Cold hyper-arid high plateau, Central and East Asia (35.0°N, 82.4°E) -> Hot hyper-arid hills, Arabia and the Middle East (30.0°N, 58.1°E) -> Polar ice sheet, Antarctica (80.0°S, 152.3°E) -> McMurdo Dry Valleys (77.5°S, 162.0°E) |

## Mars: Gale crater (Curiosity)

Crater floor at the foot of a layered mountain.

Earth can test 49% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (63.1 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-48 °C), so soil moisture is not a valid stand-in.
- **Relief within the site.** The target value (1.03e+03 m) is far outside Earth’s range (1.94 m to 753 m). No Earth site reproduces it.
- **Surface pressure.** The target value (0.843 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-79.4 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (4.52 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Surface UV-B irradiance.** The target value (0.864 W/m²) is just beyond anything on Earth (0.0546 W/m² to 0.5 W/m²). The most extreme Earth sites count at half weight.
- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (4.54°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (177 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) | 0.544 | 93% | Geology and surface materials |
| 2 | Tien Shan (42.0°N, 80.0°E) | 0.529 | 90% | Terrain and topography |
| 3 | Ojos del Salado, Andes (27.1°S, 68.5°W) | 0.500 | 83% | Terrain and topography |
| 4 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.481 | 64% | Terrain and topography |
| 5 | Cold humid high mountains, Central and East Asia (30.0°N, 81.3°E) | 0.472 | 60% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Tien Shan (42.0°N, 80.0°E) at 0.529; Karakoram, Baltoro (35.7°N, 76.5°E) at 0.481; Cold humid high mountains, Central and East Asia (30.0°N, 81.3°E) at 0.472.

Test plan: 11 requirements can be tested on Earth. The best single site passes 6. 4 site(s) together pass 11 (smallest possible set).

- Chajnantor Plateau, Chile (23.0°S, 67.8°W): surface uv-b irradiance, precipitation, mean slope, terrain roughness, surface albedo, time with the sun low on the horizon
- Karakoram, Baltoro (35.7°N, 76.5°E): precipitation, mean slope, terrain roughness, time with the sun low on the horizon, typical daily high, share of the day above freezing
- Polar ice sheet, Antarctica (80.0°S, 152.3°E): mean surface temperature, precipitation, mean solar energy flux, share of the day above freezing
- Hot humid hills, South and Southeast Asia (5.0°S, 140.0°E): mean slope, terrain roughness, time with the sun low on the horizon, wind force on surfaces

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 6 of 11 | 0 | 54% | 0 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) |
| 2 | 9 of 11 | 2 | 47% | 11,695 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) -> Cold humid hills, Alaska and Yukon (65.0°N, 144.0°W) |
| 3 | 10 of 11 | 5 | 44% | 21,961 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) -> Polar ice sheet, Antarctica (80.0°S, 152.3°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |
| 4 | 11 of 11 | 7 | 42% | 26,542 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) -> Polar ice sheet, Antarctica (80.0°S, 152.3°E) -> Hot humid hills, South and Southeast Asia (5.0°S, 140.0°E) -> Cold humid hills, Alaska and Yukon (65.0°N, 144.0°W) |
| 5 | 11 of 11 | 8 | 44% | 26,543 | Chajnantor Plateau, Chile (23.0°S, 67.8°W) -> Ojos del Salado, Andes (27.1°S, 68.5°W) -> Polar ice sheet, Antarctica (80.0°S, 152.3°E) -> Hot humid hills, South and Southeast Asia (5.0°S, 140.0°E) -> Cold humid hills, Alaska and Yukon (65.0°N, 144.0°W) |

## Mars: Elysium Planitia (InSight)

Smooth volcanic plain.

Earth can test 45% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (83.2 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-65 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.721 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-106 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.31 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-64.8 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (177 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.255 Pa) is just beyond anything on Earth (0.258 Pa to 95.3 Pa). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Hot humid plain, South America (10.0°S, 63.4°W) | 0.567 | 70% | Terrain and topography |
| 2 | Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) | 0.564 | 68% | Dust and wind |
| 3 | Hot humid plain, Africa (0.0°N, 15.0°E) | 0.557 | 63% | Terrain and topography |
| 4 | Hot humid plain, South America (5.0°S, 55.0°W) | 0.555 | 61% | Terrain and topography |
| 5 | Hot humid plain, South America (5.0°S, 70.0°W) | 0.552 | 58% | Dust and wind |

Best candidates more than 500 km from any known analog: Hot humid plain, South America (10.0°S, 63.4°W) at 0.567; Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) at 0.564; Hot humid plain, Africa (0.0°N, 15.0°E) at 0.557.

Test plan: 11 requirements can be tested on Earth. The best single site passes 8. 2 site(s) together pass 11 (smallest possible set).

- Polar ice sheet, Antarctica (75.0°S, 9.5°W): mean surface temperature, precipitation, mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Hot humid plain, South America (10.0°S, 63.4°W): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, wind force on surfaces

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 8 of 11 | 0 | 44% | 0 | Polar ice sheet, Antarctica (75.0°S, 9.5°W) |
| 2 | 11 of 11 | 3 | 50% | 7,947 | Hot humid plain, South America (10.0°S, 63.4°W) -> Polar ice sheet, Antarctica (75.0°S, 9.5°W) |
| 3 | 11 of 11 | 7 | 50% | 21,840 | Polar semi-arid plain, Siberia (65.0°N, 120.0°E) -> Hot humid plain, South America (10.0°S, 63.4°W) -> Polar ice sheet, Antarctica (75.0°S, 9.5°W) |
| 4 | 11 of 11 | 9 | 52% | 26,040 | Hot humid plain, South America (10.0°S, 63.4°W) -> Polar ice sheet, Antarctica (75.0°S, 9.5°W) -> Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Polar semi-arid plain, Siberia (65.0°N, 120.0°E) |
| 5 | 11 of 11 | 10 | 51% | 33,665 | Hot humid plain, South America (10.0°S, 63.4°W) -> Polar ice sheet, Antarctica (75.0°S, 9.5°W) -> Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Polar semi-arid plain, Siberia (70.0°N, 122.4°E) -> Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) |

## Mars: Chryse Planitia (Viking 1)

Outflow-channel plain.

Earth can test 48% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (48.4 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-66 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-90 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-65.9 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Dust optical depth.** The target value (1.05) is just beyond anything on Earth (0 to 0.926). The most extreme Earth sites count at half weight.
- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (166 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.151 Pa) is just beyond anything on Earth (0.258 Pa to 95.3 Pa). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) | 0.510 | 56% | Geology and surface materials |
| 2 | Hot arid desert plain, Australia and Oceania (25.0°S, 141.2°E) | 0.498 | 46% | Geology and surface materials |
| 3 | Hot semi-arid plain, Africa (30.0°S, 23.2°E) | 0.497 | 36% | Terrain and topography |
| 4 | Hot arid desert plain, Australia and Oceania (30.0°S, 133.6°E) | 0.495 | 33% | Geology and surface materials |
| 5 | Cold humid plain, Siberia (60.0°N, 110.0°E) | 0.493 | 34% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) at 0.510; Hot arid desert plain, Australia and Oceania (25.0°S, 141.2°E) at 0.498; Hot semi-arid plain, Africa (30.0°S, 23.2°E) at 0.497.

Test plan: 12 requirements can be tested on Earth. The best single site passes 8. 2 site(s) together pass 12 (smallest possible set).

- Polar ice sheet, Antarctica (80.0°S, 13.8°E): mean surface temperature, precipitation, mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Hot humid plain, Africa (0.0°N, 15.0°E): dust optical depth, mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, wind force on surfaces

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 8 of 12 | 0 | 48% | 0 | Polar ice sheet, Antarctica (80.0°S, 13.8°E) |
| 2 | 11 of 12 | 3 | 48% | 10,126 | Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Polar ice sheet, Antarctica (80.0°S, 13.8°E) |
| 3 | 12 of 12 | 5 | 48% | 13,512 | Polar ice sheet, Antarctica (80.0°S, 13.8°E) -> Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Temperate humid plain, Central and East Asia (30.0°N, 104.5°E) |
| 4 | 12 of 12 | 10 | 48% | 13,805 | Polar ice sheet, Antarctica (80.0°S, 13.8°E) -> Polar ice sheet, Antarctica (75.0°S, 28.4°E) -> Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Temperate humid plain, Central and East Asia (30.0°N, 104.5°E) |
| 5 | 12 of 12 | 11 | 48% | 22,472 | Hot humid plain, South America (10.0°S, 63.4°W) -> Polar ice sheet, Antarctica (80.0°S, 13.8°E) -> Polar ice sheet, Antarctica (75.0°S, 28.4°E) -> Hot humid plain, South and Southeast Asia (0.0°N, 110.0°E) -> Temperate humid plain, Central and East Asia (30.0°N, 104.5°E) |

## Mars: Vastitas Borealis (Phoenix)

High-latitude plain with shallow ground ice.

Earth can test 42% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (56.5 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-85.8 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-57.5 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (90.4 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Water in the shallow subsurface** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Polar humid hills, Siberia (65.0°N, 96.0°E) | 0.685 | 80% | Terrain and topography |
| 2 | Cold humid hills, Alaska and Yukon (65.0°N, 156.0°W) | 0.665 | 71% | Terrain and topography |
| 3 | Polar ice sheet, Antarctica (70.0°S, 50.4°E) | 0.649 | 66% | Water and ice |
| 4 | Cold humid hills, Alaska and Yukon (65.0°N, 144.0°W) | 0.642 | 54% | Geology and surface materials |
| 5 | Cold semi-arid plain, Arctic Canada (65.0°N, 120.0°W) | 0.642 | 58% | Terrain and topography |

Best candidates more than 500 km from any known analog: Polar humid hills, Siberia (65.0°N, 96.0°E) at 0.685; Cold humid hills, Alaska and Yukon (65.0°N, 156.0°W) at 0.665; Polar ice sheet, Antarctica (70.0°S, 50.4°E) at 0.649.

Test plan: 10 requirements can be tested on Earth. The best single site passes 7. 3 site(s) together pass 10 (smallest possible set).

- Polar ice sheet, Antarctica (70.0°S, 50.4°E): precipitation, mean slope, relief within the site, time with the sun low on the horizon, typical daily high, share of the day above freezing
- Polar humid hills, Siberia (65.0°N, 96.0°E): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, share of the day above freezing
- Polar ice sheet, Antarctica (75.0°S, 28.4°E): mean surface temperature, precipitation, relief within the site, mean solar energy flux, share of the day above freezing

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 6 of 10 | 0 | 68% | 0 | Polar humid hills, Siberia (65.0°N, 96.0°E) |
| 2 | 9 of 10 | 3 | 64% | 15,711 | Polar humid hills, Siberia (65.0°N, 96.0°E) -> Polar ice sheet, Antarctica (75.0°S, 66.3°E) |
| 3 | 10 of 10 | 6 | 62% | 16,512 | Polar humid hills, Siberia (65.0°N, 96.0°E) -> Polar ice sheet, Antarctica (70.0°S, 64.8°E) -> Polar ice sheet, Antarctica (75.0°S, 28.4°E) |
| 4 | 10 of 10 | 8 | 62% | 21,230 | Cold humid hills, Alaska and Yukon (65.0°N, 156.0°W) -> Polar humid hills, Siberia (65.0°N, 96.0°E) -> Polar ice sheet, Antarctica (75.0°S, 66.3°E) -> Polar ice sheet, Antarctica (75.0°S, 28.4°E) |
| 5 | 10 of 10 | 9 | 63% | 21,699 | Cold humid hills, Alaska and Yukon (65.0°N, 156.0°W) -> Polar humid hills, Siberia (65.0°N, 96.0°E) -> Polar ice sheet, Antarctica (70.0°S, 50.4°E) -> Polar ice sheet, Antarctica (75.0°S, 66.3°E) -> Polar ice sheet, Antarctica (75.0°S, 28.4°E) |

## Mars: Arcadia Planitia

Mid-latitude plain with shallow ice; candidate human landing zone.

Earth can test 38% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Surface pressure.** The target value (0.878 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (5.1 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Precipitation.** The target value (0 mm/day) is just beyond anything on Earth (0.01 mm/day to 10 mm/day). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (141 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

Not scored, and why:

- **Mean surface temperature** (no target data yet). The target dataset has no value for this site.
- **Day-night temperature swing** (no target data yet). The target dataset has no value for this site.
- **Mean wind speed** (input to a derived property). Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead.
- **Dust optical depth** (no target data yet). The target dataset has no value for this site.
- **Surface UV-B irradiance** (no target data yet). The target dataset has no value for this site.
- **Annual maximum surface temperature** (no target data yet). The target dataset has no value for this site.
- **Area with ice stable in the top metre** (no target data yet). The target dataset has no value for this site.
- **Elevation** (not comparable). Elevation depends on a local reference. Measured from each body’s own reference surface.
- **Typical daily high** (no target data yet). The target dataset has no value for this site.
- **Typical daily low** (no target data yet). The target dataset has no value for this site.
- **Share of the day above freezing** (no target data yet). The target dataset has no value for this site.
- **Wind force on surfaces** (no target data yet). The target dataset has no value for this site.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E) | 0.927 | 100% | Geology and surface materials |
| 2 | Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) | 0.914 | 100% | Geology and surface materials |
| 3 | Temperate arid desert plain, Central and East Asia (45.0°N, 88.2°E) | 0.894 | 95% | Geology and surface materials |
| 4 | Temperate arid desert plain, Central and East Asia (40.0°N, 62.2°E) | 0.885 | 95% | Geology and surface materials |
| 5 | Temperate hyper-arid desert plain, Central and East Asia (40.0°N, 88.4°E) | 0.874 | 78% | Water and ice |

Best candidates more than 500 km from any known analog: Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E) at 0.927; Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) at 0.914; Temperate arid desert plain, Central and East Asia (45.0°N, 88.2°E) at 0.894.

Test plan: 8 requirements can be tested on Earth. The best single site passes 7. 2 site(s) together pass 8 (smallest possible set).

- Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E): water in the shallow subsurface, precipitation, mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon
- Polar semi-arid plain, Siberia (65.0°N, 120.0°E): precipitation, mean slope, terrain roughness, relief within the site, surface albedo, mean solar energy flux

Field campaign (free-floating route): the best campaign per number of sites, drawn from the best-matching Earth sites. An extra stop is added only while it covers or confirms a requirement. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Covered | Confirmed at 2+ sites | Mean match | Route km | Stops in order |
|---|---|---|---|---|---|
| 1 | 7 of 8 | 0 | 93% | 0 | Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E) |
| 2 | 8 of 8 | 5 | 74% | 3,024 | Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E) -> Polar semi-arid plain, Siberia (65.0°N, 120.0°E) |
| 3 | 8 of 8 | 7 | 80% | 8,773 | Hot hyper-arid desert plain, Arabia and the Middle East (25.0°N, 41.5°E) -> Temperate arid desert plain, Central and East Asia (40.0°N, 101.5°E) -> Polar semi-arid plain, Siberia (65.0°N, 120.0°E) |
