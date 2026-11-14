# EarthMimic run report

Earth cells: 422. Targets: 13.

## Data cleaning

- Earth cells: 422 rows in, 422 rows out.
- Target sites: 13 rows in, 13 rows out.

| Table | Rule | Column | Count | Action |
|---|---|---|---|---|
| Earth cells | Extreme outlier | temp_mean_c | 4 | flagged, value kept |
| Earth cells | Extreme outlier | warm_month_high_c | 1 | flagged, value kept |
| Earth cells | Extreme outlier | slope_deg | 1 | flagged, value kept |
| Earth cells | Extreme outlier | roughness_deg | 4 | flagged, value kept |

## Relationship agent

- Run 17: 2 of 15 tool calls used.
- Run 18: 0 of 15 tool calls used.

| Target column | Earth column | Status | Confidence | Deciding check |
|---|---|---|---|---|
| surf_temp_mean_K | temp_mean_c | accepted | 1.00 | All checks passed. |
| temp_swing_K | temp_swing_c | accepted | 1.00 | All checks passed. |
| wind_ms | wind_ms | accepted (input only) | 1.00 | Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead. |
| dust_tau | dust_aod | accepted | 1.00 | All checks passed. |
| surf_temp_max_K | warm_month_high_c | accepted | 0.60 | Related but not identical concepts; confidence starts at 0.60. |
| shallow_ice_share | soil_wetness | denied | 0.00 | The columns are tagged as different things ('shallow_ice_stability' and 'soil_moisture') with no registered relation between them. |
| subsurface_h2o_share | soil_wetness | accepted | 0.50 | Related but not identical concepts; confidence starts at 0.50. |
| slope_deg | slope_deg | accepted | 0.99 | All checks passed. |
| roughness_deg | roughness_deg | accepted | 0.44 | Moves almost in step with 'slope_deg' (rank correlation +0.96); counted at half weight so the same signal is not counted twice. |
| relief_m | relief_m | accepted | 0.49 | Moves almost in step with 'slope_deg' (rank correlation +0.97); counted at half weight so the same signal is not counted twice. |
| surf_pressure_Pa | pressure_kpa | accepted | 1.00 | All checks passed. |
| elevation_m | elevation_m | denied | 0.00 | Elevation depends on a local reference. Measured from each body’s own reference surface. |
| grazing_sun_share | grazing_sun_share | accepted | 1.00 | All checks passed. |
| insolation_wm2 | insolation_wm2 | accepted | 0.50 | Moves almost in step with 'grazing_sun_share' (rank correlation -0.97); counted at half weight so the same signal is not counted twice. |
| daily_high_c | daily_high_c | accepted | 0.50 | Moves almost in step with 'temp_mean_c' (rank correlation +0.95); counted at half weight so the same signal is not counted twice. |
| daily_low_c | daily_low_c | accepted | 0.50 | Moves almost in step with 'temp_mean_c' (rank correlation +0.96); counted at half weight so the same signal is not counted twice. |
| liquid_window_c | liquid_window_c | accepted | 1.00 | All checks passed. |
| thaw_share | thaw_share | accepted | 1.00 | All checks passed. |
| wind_pressure_pa | wind_pressure_pa | accepted | 1.00 | All checks passed. |

## Known-analog check (balanced weights)

4 of 10 known analogs rank in the top 5% of Earth cells (random ranking would give about 0.5). Median percentile: 94.4.

| Known analog | Best target | Rank | Percentile |
|---|---|---|---|
| Atacama Desert | Arcadia Planitia | 26 | 94.1 |
| McMurdo Dry Valleys | Jezero crater (Perseverance) | 3 | 99.5 |
| Haughton crater, Devon Island | Elysium Planitia (InSight) | 23 | 94.8 |
| Askja, Iceland | Cabeus crater | 15 | 96.7 |
| Mauna Kea, Hawaii | Gale crater (Curiosity) | 42 | 90.3 |
| Rio Tinto, Spain | Arcadia Planitia | 91 | 78.7 |
| Utah desert (MDRS) | Arcadia Planitia | 100 | 76.5 |
| Dallol, Ethiopia | Jezero crater (Perseverance) | 72 | 83.2 |
| Svalbard | Jezero crater (Perseverance) | 7 | 98.6 |
| Qaidam Basin | Arcadia Planitia | 6 | 98.8 |

## Moon: Shackleton crater rim

Rim of Shackleton crater near the south pole.

Earth can test 14% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-209 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Mean slope.** The target value (24.7°) is far outside Earth’s range (0.0139° to 5.74°). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (8.77°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.
- **Relief within the site.** The target value (1.21e+03 m) is just beyond anything on Earth (2.27 m to 1.15e+03 m). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Southern mid-latitudes (65.0°S, 108.0°E) | 0.535 | 77% | Water and ice |
| 2 | Arctic (85.0°N, 60.0°W) | 0.500 | 58% | Water and ice |
| 3 | Arctic (85.0°N, 60.0°E) | 0.500 | 58% | Water and ice |
| 4 | Arctic (85.0°N, 180.0°W) | 0.500 | 57% | Water and ice |
| 5 | Antarctic (85.0°S, 60.0°E) | 0.500 | 57% | Water and ice |

Best candidates more than 500 km from any known analog: Southern mid-latitudes (65.0°S, 108.0°E) at 0.535; Arctic (85.0°N, 60.0°W) at 0.500; Arctic (85.0°N, 60.0°E) at 0.500.

Test plan: 4 requirements can be tested on Earth. The best single site passes 2. 3 site(s) together pass 4 (smallest possible set).

- Southern mid-latitudes (65.0°S, 108.0°E): relief within the site, share of the day above freezing
- Southern mid-latitudes (55.0°S, 128.6°W): terrain roughness, relief within the site
- Northern mid-latitudes (25.0°N, 38.2°E): annual maximum surface temperature

## Moon: Shackleton to de Gerlache ridge

Sunlit ridge between Shackleton and de Gerlache craters.

Earth can test 20% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-148 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (9.72°) is just beyond anything on Earth (0.0139° to 5.74°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (5.05°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (55.0°N, 128.6°E) | 0.546 | 39% | Water and ice |
| 2 | McMurdo Dry Valleys (77.5°S, 162.0°E) | 0.538 | 55% | Water and ice |
| 3 | Northern mid-latitudes (55.0°N, 111.4°E) | 0.534 | 53% | Water and ice |
| 4 | Southern mid-latitudes (65.0°S, 180.0°W) | 0.531 | 49% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 156.0°E) | 0.527 | 29% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (55.0°N, 128.6°E) at 0.546; Northern mid-latitudes (55.0°N, 111.4°E) at 0.534; Southern mid-latitudes (65.0°S, 180.0°W) at 0.531.

Test plan: 5 requirements can be tested on Earth. The best single site passes 2. 3 site(s) together pass 5 (smallest possible set).

- McMurdo Dry Valleys (77.5°S, 162.0°E): relief within the site, share of the day above freezing
- Northern mid-latitudes (25.0°N, 136.4°E): mean slope, terrain roughness
- Northern mid-latitudes (55.0°N, 94.3°E): annual maximum surface temperature, relief within the site

## Moon: Shackleton crater floor

Permanently shadowed crater floor.

Earth can test 17% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-221 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-169 °C) is far outside Earth’s range (-15.4 °C to 49.2 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (11.8 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (12.4°) is just beyond anything on Earth (0.0139° to 5.74°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (9.06°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Arctic (85.0°N, 60.0°E) | 1.000 | 45% | Water and ice |
| 2 | Antarctic (85.0°S, 180.0°W) | 1.000 | 45% | Water and ice |
| 3 | Antarctic (85.0°S, 60.0°E) | 1.000 | 45% | Water and ice |
| 4 | Arctic (85.0°N, 180.0°W) | 1.000 | 45% | Water and ice |
| 5 | Arctic (85.0°N, 60.0°W) | 1.000 | 45% | Water and ice |

Best candidates more than 500 km from any known analog: Arctic (85.0°N, 60.0°E) at 1.000; Antarctic (85.0°S, 180.0°W) at 1.000; Antarctic (85.0°S, 60.0°E) at 1.000.

Test plan: 4 requirements can be tested on Earth. The best single site passes 2. 2 site(s) together pass 4 (smallest possible set).

- McMurdo Dry Valleys (77.5°S, 162.0°E): relief within the site, share of the day above freezing
- Southern mid-latitudes (55.0°S, 128.6°W): mean slope, terrain roughness

## Moon: Malapert massif

High massif with long sunlight and Earth visibility.

Earth can test 14% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-129 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (64 °C) is far outside Earth’s range (-15.4 °C to 49.2 °C). No Earth site reproduces it.
- **Mean slope.** The target value (18°) is far outside Earth’s range (0.0139° to 5.74°). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (46.4% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (31.3 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (6.17°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Arctic (85.0°N, 60.0°E) | 1.000 | 52% | Water and ice |
| 2 | Antarctic (85.0°S, 60.0°E) | 1.000 | 52% | Water and ice |
| 3 | Antarctic (85.0°S, 60.0°W) | 1.000 | 52% | Water and ice |
| 4 | Antarctic (85.0°S, 180.0°W) | 1.000 | 52% | Water and ice |
| 5 | Arctic (85.0°N, 180.0°W) | 1.000 | 52% | Water and ice |

Best candidates more than 500 km from any known analog: Arctic (85.0°N, 60.0°E) at 1.000; Antarctic (85.0°S, 60.0°E) at 1.000; Antarctic (85.0°S, 60.0°W) at 1.000.

Test plan: 3 requirements can be tested on Earth. The best single site passes 2. 2 site(s) together pass 3 (smallest possible set).

- Southern mid-latitudes (65.0°S, 108.0°E): relief within the site, share of the day above freezing
- Southern mid-latitudes (55.0°S, 128.6°W): terrain roughness, relief within the site

## Moon: Haworth crater

Large permanently shadowed crater.

Earth can test 19% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-234 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-180 °C) is far outside Earth’s range (-15.4 °C to 49.2 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (21.1 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (4.3°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Arctic (85.0°N, 60.0°E) | 1.000 | 45% | Water and ice |
| 2 | Antarctic (85.0°S, 60.0°E) | 1.000 | 45% | Water and ice |
| 3 | Arctic (85.0°N, 60.0°W) | 1.000 | 45% | Water and ice |
| 4 | Arctic (85.0°N, 180.0°W) | 1.000 | 45% | Water and ice |
| 5 | Antarctic (85.0°S, 60.0°W) | 1.000 | 45% | Water and ice |

Best candidates more than 500 km from any known analog: Arctic (85.0°N, 60.0°E) at 1.000; Antarctic (85.0°S, 60.0°E) at 1.000; Arctic (85.0°N, 60.0°W) at 1.000.

Test plan: 4 requirements can be tested on Earth. The best single site passes 3. 2 site(s) together pass 4 (smallest possible set).

- McMurdo Dry Valleys (77.5°S, 162.0°E): mean slope, relief within the site, share of the day above freezing
- Southern mid-latitudes (65.0°S, 108.0°E): mean slope, terrain roughness, share of the day above freezing

## Moon: Cabeus crater

Shadowed crater where LCROSS detected water.

Earth can test 20% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-205 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (42.1% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (36.4 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (7.4°) is just beyond anything on Earth (0.0139° to 5.74°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (4.63°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (65.0°N, 132.0°W) | 0.789 | 99% | Water and ice |
| 2 | Northern mid-latitudes (35.0°N, 80.7°E) | 0.774 | 94% | Temperature extremes |
| 3 | Svalbard (78.2°N, 15.6°E) | 0.730 | 89% | Water and ice |
| 4 | Northern mid-latitudes (65.0°N, 84.0°W) | 0.695 | 69% | Water and ice |
| 5 | Haughton crater, Devon Island (75.4°N, 89.7°W) | 0.681 | 61% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (65.0°N, 132.0°W) at 0.789; Northern mid-latitudes (35.0°N, 80.7°E) at 0.774; Northern mid-latitudes (65.0°N, 84.0°W) at 0.695.

Test plan: 5 requirements can be tested on Earth. The best single site passes 4. 2 site(s) together pass 5 (smallest possible set).

- Southern mid-latitudes (45.0°S, 108.0°W): annual maximum surface temperature, mean slope, terrain roughness, relief within the site
- Northern mid-latitudes (65.0°N, 132.0°W): annual maximum surface temperature, relief within the site, share of the day above freezing

## Moon: Faustini crater

Permanently shadowed crater.

Earth can test 22% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-229 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-184 °C) is far outside Earth’s range (-15.4 °C to 49.2 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.1% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (22.8 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Arctic (85.0°N, 60.0°E) | 1.000 | 45% | Water and ice |
| 2 | Antarctic (85.0°S, 180.0°W) | 1.000 | 45% | Water and ice |
| 3 | Arctic (85.0°N, 60.0°W) | 1.000 | 45% | Water and ice |
| 4 | Arctic (85.0°N, 180.0°W) | 1.000 | 45% | Water and ice |
| 5 | Antarctic (85.0°S, 60.0°E) | 1.000 | 45% | Water and ice |

Best candidates more than 500 km from any known analog: Arctic (85.0°N, 60.0°E) at 1.000; Antarctic (85.0°S, 180.0°W) at 1.000; Arctic (85.0°N, 60.0°W) at 1.000.

Test plan: 4 requirements can be tested on Earth. The best single site passes 3. 2 site(s) together pass 4 (smallest possible set).

- McMurdo Dry Valleys (77.5°S, 162.0°E): mean slope, terrain roughness, share of the day above freezing
- Antarctic (75.0°S, 60.0°W): terrain roughness, relief within the site, share of the day above freezing

## Mars: Jezero crater (Perseverance)

Ancient river delta in an impact crater.

Earth can test 41% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (62.2 °C) is far outside Earth’s range (0.4 °C to 16.4 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-50 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.716 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-81.2 °C) is far outside Earth’s range (-53.7 °C to 29.2 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.2 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.
- **Wind force on surfaces.** The target value (0.0601 Pa) is far outside Earth’s range (0.445 Pa to 76 Pa). No Earth site reproduces it.

Only partly reproducible:

- **Mean solar energy flux.** The target value (170 W_per_m2) is just beyond anything on Earth (174 W_per_m2 to 414 W_per_m2). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (35.0°N, 80.7°E) | 0.624 | 85% | Terrain and topography |
| 2 | Arctic (75.0°N, 20.0°W) | 0.613 | 86% | Water and ice |
| 3 | McMurdo Dry Valleys (77.5°S, 162.0°E) | 0.609 | 83% | Water and ice |
| 4 | Antarctic (85.0°S, 60.0°E) | 0.606 | 67% | Water and ice |
| 5 | Antarctic (75.0°S, 140.0°W) | 0.578 | 71% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (35.0°N, 80.7°E) at 0.624; Arctic (75.0°N, 20.0°W) at 0.613; Antarctic (85.0°S, 60.0°E) at 0.606.

Test plan: 8 requirements can be tested on Earth. The best single site passes 6. 3 site(s) together pass 8 (smallest possible set).

- Arctic (75.0°N, 20.0°W): mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Northern mid-latitudes (35.0°N, 80.7°E): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon, share of the day above freezing
- Antarctic (85.0°S, 60.0°E): mean surface temperature, mean solar energy flux, share of the day above freezing

## Mars: Gale crater (Curiosity)

Crater floor at the foot of a layered mountain.

Earth can test 47% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (63.1 °C) is far outside Earth’s range (0.4 °C to 16.4 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-48 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.843 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-79.4 °C) is far outside Earth’s range (-53.7 °C to 29.2 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (4.52 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (4.54°) is just beyond anything on Earth (0.00747° to 4.2°). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.347 Pa) is just beyond anything on Earth (0.445 Pa to 76 Pa). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Southern mid-latitudes (65.0°S, 108.0°E) | 0.473 | 84% | Water and ice |
| 2 | Antarctic (85.0°S, 60.0°E) | 0.472 | 87% | Water and ice |
| 3 | McMurdo Dry Valleys (77.5°S, 162.0°E) | 0.467 | 90% | Water and ice |
| 4 | Antarctic (85.0°S, 60.0°W) | 0.452 | 80% | Water and ice |
| 5 | Antarctic (85.0°S, 180.0°W) | 0.445 | 75% | Water and ice |

Best candidates more than 500 km from any known analog: Southern mid-latitudes (65.0°S, 108.0°E) at 0.473; Antarctic (85.0°S, 60.0°E) at 0.472; Antarctic (85.0°S, 60.0°W) at 0.452.

Test plan: 9 requirements can be tested on Earth. The best single site passes 6. 3 site(s) together pass 9 (smallest possible set).

- Southern mid-latitudes (65.0°S, 108.0°E): mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Antarctic (85.0°S, 60.0°E): mean surface temperature, mean solar energy flux, share of the day above freezing
- Tropics (5.0°S, 140.0°E): terrain roughness, time with the sun low on the horizon, wind force on surfaces

## Mars: Elysium Planitia (InSight)

Smooth volcanic plain.

Earth can test 48% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (83.2 °C) is far outside Earth’s range (0.4 °C to 16.4 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-65 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.721 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-106 °C) is far outside Earth’s range (-53.7 °C to 29.2 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.31 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-64.8 °C) is just beyond anything on Earth (-50.6 °C to 29.8 °C). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.255 Pa) is just beyond anything on Earth (0.445 Pa to 76 Pa). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tropics (5.0°S, 70.0°W) | 0.504 | 60% | Dust and wind |
| 2 | Antarctic (75.0°S, 180.0°W) | 0.494 | 95% | Water and ice |
| 3 | Northern mid-latitudes (65.0°N, 108.0°W) | 0.484 | 80% | Water and ice |
| 4 | Arctic (75.0°N, 140.0°E) | 0.480 | 89% | Water and ice |
| 5 | Tropics (5.0°S, 20.0°E) | 0.477 | 56% | Terrain and topography |

Best candidates more than 500 km from any known analog: Tropics (5.0°S, 70.0°W) at 0.504; Antarctic (75.0°S, 180.0°W) at 0.494; Northern mid-latitudes (65.0°N, 108.0°W) at 0.484.

Test plan: 9 requirements can be tested on Earth. The best single site passes 5. 3 site(s) together pass 9 (smallest possible set).

- Tropics (5.0°S, 70.0°W): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon, wind force on surfaces
- Antarctic (75.0°S, 100.0°E): mean surface temperature, relief within the site, mean solar energy flux, share of the day above freezing
- Antarctic (75.0°S, 20.0°W): mean solar energy flux, typical daily high, share of the day above freezing

## Mars: Chryse Planitia (Viking 1)

Outflow-channel plain.

Earth can test 38% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-65.9 °C) is far outside Earth’s range (-50.6 °C to 29.8 °C). No Earth site reproduces it.
- **Day-night temperature swing.** The target value (48.4 °C) is far outside Earth’s range (0.4 °C to 16.4 °C). No Earth site reproduces it.
- **Dust optical depth.** The target value (1.05) is far outside Earth’s range (0 to 0.692). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-66 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-90 °C) is far outside Earth’s range (-53.7 °C to 29.2 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.
- **Wind force on surfaces.** The target value (0.151 Pa) is far outside Earth’s range (0.445 Pa to 76 Pa). No Earth site reproduces it.

Only partly reproducible:

- **Mean solar energy flux.** The target value (166 W_per_m2) is just beyond anything on Earth (174 W_per_m2 to 414 W_per_m2). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Antarctic (75.0°S, 140.0°E) | 0.695 | 92% | Water and ice |
| 2 | Antarctic (75.0°S, 60.0°E) | 0.687 | 90% | Water and ice |
| 3 | Antarctic (85.0°S, 60.0°W) | 0.648 | 85% | Water and ice |
| 4 | Antarctic (75.0°S, 20.0°E) | 0.644 | 84% | Water and ice |
| 5 | Antarctic (85.0°S, 180.0°W) | 0.636 | 84% | Water and ice |

Best candidates more than 500 km from any known analog: Antarctic (75.0°S, 140.0°E) at 0.695; Antarctic (75.0°S, 60.0°E) at 0.687; Antarctic (85.0°S, 60.0°W) at 0.648.

Test plan: 7 requirements can be tested on Earth. The best single site passes 5. 2 site(s) together pass 7 (smallest possible set).

- Antarctic (75.0°S, 140.0°E): mean slope, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Tropics (15.0°N, 77.1°E): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon

## Mars: Vastitas Borealis (Phoenix)

High-latitude plain with shallow ground ice.

Earth can test 36% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (56.5 °C) is far outside Earth’s range (0.4 °C to 16.4 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (90.4 W_per_m2) is far outside Earth’s range (174 W_per_m2 to 414 W_per_m2). No Earth site reproduces it.
- **Typical daily low.** The target value (-85.8 °C) is far outside Earth’s range (-53.7 °C to 29.2 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-57.5 °C) is just beyond anything on Earth (-50.6 °C to 29.8 °C). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (65.0°N, 108.0°E) | 0.735 | 100% | Water and ice |
| 2 | Northern mid-latitudes (65.0°N, 84.0°W) | 0.729 | 99% | Water and ice |
| 3 | Southern mid-latitudes (65.0°S, 12.0°E) | 0.729 | 97% | Water and ice |
| 4 | Southern mid-latitudes (65.0°S, 36.0°E) | 0.727 | 96% | Water and ice |
| 5 | Southern mid-latitudes (65.0°S, 60.0°E) | 0.725 | 98% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (65.0°N, 108.0°E) at 0.735; Northern mid-latitudes (65.0°N, 84.0°W) at 0.729; Southern mid-latitudes (65.0°S, 12.0°E) at 0.729.

Test plan: 7 requirements can be tested on Earth. The best single site passes 5. 3 site(s) together pass 7 (smallest possible set).

- Northern mid-latitudes (65.0°N, 108.0°E): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon, share of the day above freezing
- Antarctic (75.0°S, 60.0°E): mean slope, relief within the site, typical daily high, share of the day above freezing
- Antarctic (85.0°S, 60.0°E): mean surface temperature, share of the day above freezing

## Mars: Arcadia Planitia

Mid-latitude plain with shallow ice; candidate human landing zone.

Earth can test 32% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Surface pressure.** The target value (0.878 kPa) is far outside Earth’s range (62 kPa to 102 kPa). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (5.1 °C) is far outside Earth’s range (86.4 °C to 99.5 °C). No Earth site reproduces it.

Only partly reproducible:

- **Water in the shallow subsurface.** The target value (0.0484) is just beyond anything on Earth (0.091 to 1). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (141 W_per_m2) is just beyond anything on Earth (174 W_per_m2 to 414 W_per_m2). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (25.0°N, 27.3°E) | 0.788 | 98% | Water and ice |
| 2 | Northern mid-latitudes (25.0°N, 16.4°E) | 0.738 | 97% | Water and ice |
| 3 | Northern mid-latitudes (25.0°N, 49.1°E) | 0.701 | 96% | Terrain and topography |
| 4 | Northern mid-latitudes (25.0°N, 5.5°W) | 0.617 | 83% | Terrain and topography |
| 5 | Southern mid-latitudes (25.0°S, 125.5°E) | 0.608 | 62% | Terrain and topography |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (25.0°N, 27.3°E) at 0.788; Northern mid-latitudes (25.0°N, 16.4°E) at 0.738; Northern mid-latitudes (25.0°N, 49.1°E) at 0.701.

Test plan: 6 requirements can be tested on Earth. The best single site passes 4. 3 site(s) together pass 6 (smallest possible set).

- Arctic (75.0°N, 140.0°E): mean slope, terrain roughness, relief within the site, mean solar energy flux
- Northern mid-latitudes (35.0°N, 80.7°W): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon
- Northern mid-latitudes (25.0°N, 27.3°E): water in the shallow subsurface, mean slope, terrain roughness, relief within the site
