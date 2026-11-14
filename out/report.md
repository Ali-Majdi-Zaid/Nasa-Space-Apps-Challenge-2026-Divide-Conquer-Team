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

- Run 1: 13 of 15 tool calls used.
- Run 2: 5 of 15 tool calls used.

| Target column | Earth column | Status | Confidence | Deciding check |
|---|---|---|---|---|
| shallow_ice_share | - | denied | 0.00 | No Earth column was proposed as a counterpart. |
| surf_temp_mean_K | temp_mean_c | accepted | 1.00 | All checks passed. |
| temp_swing_K | temp_swing_c | accepted | 1.00 | All checks passed. |
| wind_ms | wind_ms | accepted (input only) | 1.00 | Wind speed alone ignores how thin the air is, so the same speed means very different forces on different worlds. Sites are compared on wind force instead. |
| dust_tau | dust_aod | accepted | 1.00 | All checks passed. |
| surf_temp_max_K | warm_month_high_c | accepted | 0.60 | Related but not identical concepts; confidence starts at 0.60. |
| subsurface_h2o_share | soil_wetness | accepted | 0.50 | Related but not identical concepts; confidence starts at 0.50. |
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

2 of 10 known analogs rank in the top 5% of Earth cells (random ranking would give about 0.5). Median percentile: 90.8.

| Known analog | Best target | Rank | Percentile |
|---|---|---|---|
| Atacama Desert | Gale crater (Curiosity) | 41 | 91.9 |
| McMurdo Dry Valleys | Jezero crater (Perseverance) | 31 | 93.9 |
| Haughton crater, Devon Island | Vastitas Borealis (Phoenix) | 52 | 89.7 |
| Askja, Iceland | Shackleton crater floor | 6 | 99.0 |
| Mauna Kea, Hawaii | Gale crater (Curiosity) | 144 | 71.1 |
| Rio Tinto, Spain | Jezero crater (Perseverance) | 147 | 70.4 |
| Utah desert (MDRS) | Arcadia Planitia | 126 | 74.7 |
| Dallol, Ethiopia | Jezero crater (Perseverance) | 37 | 92.7 |
| Svalbard | Jezero crater (Perseverance) | 112 | 77.5 |
| Qaidam Basin | Arcadia Planitia | 8 | 98.6 |

## Moon: Shackleton crater rim

Rim of Shackleton crater near the south pole.

Earth can test 27% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-209 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Relief within the site.** The target value (1.21e+03 m) is far outside Earth’s range (1.94 m to 753 m). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (24.7°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (8.77°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.616 | 78% | Water and ice |
| 2 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.542 | 60% | Water and ice |
| 3 | St. Elias Mountains, Alaska (60.5°N, 139.5°W) | 0.521 | 45% | Water and ice |
| 4 | Northern mid-latitudes (60.0°N, 150.0°E) | 0.517 | 52% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 144.0°E) | 0.515 | 51% | Water and ice |

Best candidates more than 500 km from any known analog: Karakoram, Baltoro (35.7°N, 76.5°E) at 0.616; Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.542; St. Elias Mountains, Alaska (60.5°N, 139.5°W) at 0.521.

Test plan: 5 requirements can be tested on Earth. The best single site passes 3. 2 site(s) together pass 4 (smallest possible set).

- Karakoram, Baltoro (35.7°N, 76.5°E): terrain roughness, surface albedo, share of the day above freezing
- Tropics (20.0°N, 52.9°E): annual maximum surface temperature, surface albedo

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 3 of 5 | 0 | Karakoram, Baltoro (35.7°N, 76.5°E) |
| 2 | 4 of 5 | 2,867 | Northern mid-latitudes (30.0°N, 46.5°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |

## Moon: Shackleton to de Gerlache ridge

Sunlit ridge between Shackleton and de Gerlache craters.

Earth can test 31% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-148 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (12 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (9.72°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (5.05°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.688 | 75% | Water and ice |
| 2 | Northern mid-latitudes (60.0°N, 150.0°E) | 0.680 | 83% | Water and ice |
| 3 | Northern mid-latitudes (65.0°N, 156.0°E) | 0.649 | 81% | Water and ice |
| 4 | Northern mid-latitudes (65.0°N, 132.0°W) | 0.637 | 54% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 132.0°E) | 0.630 | 59% | Water and ice |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.688; Northern mid-latitudes (60.0°N, 150.0°E) at 0.680; Northern mid-latitudes (65.0°N, 156.0°E) at 0.649.

Test plan: 6 requirements can be tested on Earth. The best single site passes 4. 2 site(s) together pass 6 (smallest possible set).

- Karakoram, Baltoro (35.7°N, 76.5°E): mean slope, terrain roughness, surface albedo, share of the day above freezing
- Northern mid-latitudes (40.0°N, 42.5°E): annual maximum surface temperature, relief within the site, surface albedo

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 4 of 6 | 0 | Eureka, Ellesmere Island (80.0°N, 85.9°W) |
| 2 | 6 of 6 | 2,346 | Northern mid-latitudes (30.0°N, 52.3°E) -> Karakoram, Baltoro (35.7°N, 76.5°E) |

## Moon: Shackleton crater floor

Permanently shadowed crater floor.

Earth can test 29% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-221 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-169 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (11.8 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (12.4°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (9.06°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.830 | 100% | Water and ice |
| 2 | Northern mid-latitudes (60.0°N, 150.0°E) | 0.815 | 100% | Water and ice |
| 3 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.803 | 100% | Water and ice |
| 4 | Northern mid-latitudes (65.0°N, 144.0°E) | 0.796 | 100% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 132.0°E) | 0.770 | 99% | Water and ice |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.830; Northern mid-latitudes (60.0°N, 150.0°E) at 0.815; Karakoram, Baltoro (35.7°N, 76.5°E) at 0.803.

Test plan: 5 requirements can be tested on Earth. The best single site passes 4. 2 site(s) together pass 5 (smallest possible set).

- St. Elias Mountains, Alaska (60.5°N, 139.5°W): mean slope, terrain roughness, surface albedo, share of the day above freezing
- Eureka, Ellesmere Island (80.0°N, 85.9°W): relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 4 of 5 | 0 | St. Elias Mountains, Alaska (60.5°N, 139.5°W) |
| 2 | 5 of 5 | 629 | Northern mid-latitudes (65.0°N, 132.0°W) -> St. Elias Mountains, Alaska (60.5°N, 139.5°W) |

## Moon: Malapert massif

High massif with long sunlight and Earth visibility.

Earth can test 26% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-129 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (64 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (46.4% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (31.3 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (18°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (6.17°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.
- **Relief within the site.** The target value (785 m) is just beyond anything on Earth (1.94 m to 753 m). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tien Shan (42.0°N, 80.0°E) | 0.792 | 100% | Water and ice |
| 2 | Northern mid-latitudes (60.0°N, 150.0°W) | 0.757 | 99% | Water and ice |
| 3 | Northern mid-latitudes (65.0°N, 132.0°W) | 0.748 | 99% | Water and ice |
| 4 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.703 | 66% | Water and ice |
| 5 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.697 | 70% | Water and ice |

Best candidates more than 500 km from any known analog: Tien Shan (42.0°N, 80.0°E) at 0.792; Northern mid-latitudes (60.0°N, 150.0°W) at 0.757; Northern mid-latitudes (65.0°N, 132.0°W) at 0.748.

Test plan: 5 requirements can be tested on Earth. The best single site passes 4. 2 site(s) together pass 5 (smallest possible set).

- Northern mid-latitudes (35.0°N, 70.2°E): mean slope, terrain roughness, relief within the site, surface albedo
- Tien Shan (42.0°N, 80.0°E): terrain roughness, surface albedo, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 4 of 5 | 0 | Northern mid-latitudes (35.0°N, 70.2°E) |
| 2 | 5 of 5 | 1,155 | Tien Shan (42.0°N, 80.0°E) -> Northern mid-latitudes (35.0°N, 70.2°E) |

## Moon: Haworth crater

Large permanently shadowed crater.

Earth can test 31% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-234 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-180 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (21.1 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (4.3°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.930 | 100% | Water and ice |
| 2 | Northern mid-latitudes (65.0°N, 132.0°W) | 0.905 | 99% | Water and ice |
| 3 | Northern mid-latitudes (65.0°N, 144.0°E) | 0.904 | 100% | Water and ice |
| 4 | Northern mid-latitudes (65.0°N, 132.0°E) | 0.901 | 100% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 168.0°E) | 0.887 | 99% | Water and ice |

Best candidates more than 500 km from any known analog: Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.930; Northern mid-latitudes (65.0°N, 132.0°W) at 0.905; Northern mid-latitudes (65.0°N, 144.0°E) at 0.904.

Test plan: 5 requirements can be tested on Earth. The best single site passes 5. 1 site(s) together pass 5 (smallest possible set).

- Northern mid-latitudes (65.0°N, 132.0°W): mean slope, terrain roughness, relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 5 of 5 | 0 | Northern mid-latitudes (65.0°N, 132.0°W) |

## Moon: Cabeus crater

Shadowed crater where LCROSS detected water.

Earth can test 31% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-205 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (42.1% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (36.4 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean slope.** The target value (7.4°) is just beyond anything on Earth (0.0121° to 5.81°). The most extreme Earth sites count at half weight.
- **Terrain roughness.** The target value (4.63°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (60.0°N, 150.0°W) | 0.924 | 100% | Water and ice |
| 2 | Tien Shan (42.0°N, 80.0°E) | 0.877 | 100% | Water and ice |
| 3 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.863 | 100% | Water and ice |
| 4 | Northern mid-latitudes (65.0°N, 132.0°W) | 0.843 | 100% | Water and ice |
| 5 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.816 | 99% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (60.0°N, 150.0°W) at 0.924; Tien Shan (42.0°N, 80.0°E) at 0.877; Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.863.

Test plan: 6 requirements can be tested on Earth. The best single site passes 6. 1 site(s) together pass 6 (smallest possible set).

- Northern mid-latitudes (60.0°N, 150.0°W): annual maximum surface temperature, mean slope, terrain roughness, relief within the site, surface albedo, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 6 | 0 | Northern mid-latitudes (60.0°N, 150.0°W) |

## Moon: Faustini crater

Permanently shadowed crater.

Earth can test 31% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Mean surface temperature.** The target value (-229 °C) is far outside Earth’s range (-57.5 °C to 30.6 °C). No Earth site reproduces it.
- **Annual maximum surface temperature.** The target value (-184 °C) is far outside Earth’s range (-19.1 °C to 49.9 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Time with the Sun low on the horizon.** The target value (50% of the year) is far outside Earth’s range (2.9% of the year to 10.4% of the year). No Earth site reproduces it.
- **Mean solar energy flux.** The target value (22.8 W/m²) is far outside Earth’s range (178 W/m² to 416 W/m²). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (0 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (3.67°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (65.0°N, 144.0°E) | 0.901 | 100% | Water and ice |
| 2 | Eureka, Ellesmere Island (80.0°N, 85.9°W) | 0.894 | 100% | Water and ice |
| 3 | Oymyakon, Siberia (63.5°N, 142.8°E) | 0.885 | 99% | Water and ice |
| 4 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.882 | 99% | Water and ice |
| 5 | Arctic (70.0°N, 136.8°E) | 0.878 | 99% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (65.0°N, 144.0°E) at 0.901; Eureka, Ellesmere Island (80.0°N, 85.9°W) at 0.894; Oymyakon, Siberia (63.5°N, 142.8°E) at 0.885.

Test plan: 5 requirements can be tested on Earth. The best single site passes 4. 2 site(s) together pass 5 (smallest possible set).

- Oymyakon, Siberia (63.5°N, 142.8°E): mean slope, relief within the site, surface albedo, share of the day above freezing
- Eureka, Ellesmere Island (80.0°N, 85.9°W): mean slope, terrain roughness, surface albedo, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 4 of 5 | 0 | Oymyakon, Siberia (63.5°N, 142.8°E) |
| 2 | 5 of 5 | 555 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Arctic (75.0°N, 85.3°W) |

## Mars: Jezero crater (Perseverance)

Ancient river delta in an impact crater.

Earth can test 50% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (62.2 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-50 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.716 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-81.2 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.2 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.
- **Wind force on surfaces.** The target value (0.0601 Pa) is far outside Earth’s range (0.258 Pa to 95.3 Pa). No Earth site reproduces it.

Only partly reproducible:

- **Mean solar energy flux.** The target value (170 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (35.0°N, 82.4°E) | 0.624 | 76% | Terrain and topography |
| 2 | Changtang, Tibetan Plateau (34.5°N, 88.0°E) | 0.612 | 61% | Geology and surface materials |
| 3 | Northern mid-latitudes (60.0°N, 130.0°W) | 0.605 | 58% | Water and ice |
| 4 | Northern mid-latitudes (30.0°N, 87.1°E) | 0.600 | 57% | Geology and surface materials |
| 5 | Northern mid-latitudes (35.0°N, 88.5°E) | 0.591 | 44% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (35.0°N, 82.4°E) at 0.624; Changtang, Tibetan Plateau (34.5°N, 88.0°E) at 0.612; Northern mid-latitudes (60.0°N, 130.0°W) at 0.605.

Test plan: 9 requirements can be tested on Earth. The best single site passes 6. 2 site(s) together pass 9 (smallest possible set).

- Northern mid-latitudes (30.0°N, 98.7°E): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon
- Antarctic (75.0°S, 66.3°E): mean surface temperature, mean solar energy flux, typical daily high, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 9 | 0 | McMurdo Dry Valleys (77.5°S, 162.0°E) |
| 2 | 9 of 9 | 11,907 | Antarctic (75.0°S, 66.3°E) -> Northern mid-latitudes (30.0°N, 98.7°E) |

## Mars: Gale crater (Curiosity)

Crater floor at the foot of a layered mountain.

Earth can test 50% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (63.1 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-48 °C), so soil moisture is not a valid stand-in.
- **Relief within the site.** The target value (1.03e+03 m) is far outside Earth’s range (1.94 m to 753 m). No Earth site reproduces it.
- **Surface pressure.** The target value (0.843 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-79.4 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (4.52 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Terrain roughness.** The target value (4.54°) is just beyond anything on Earth (0.00582° to 2.97°). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (177 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tien Shan (42.0°N, 80.0°E) | 0.620 | 93% | Water and ice |
| 2 | Northern mid-latitudes (50.0°N, 86.1°E) | 0.565 | 80% | Geology and surface materials |
| 3 | Karakoram, Baltoro (35.7°N, 76.5°E) | 0.561 | 68% | Water and ice |
| 4 | Northern mid-latitudes (55.0°N, 109.8°E) | 0.535 | 65% | Water and ice |
| 5 | Valais Alps, Switzerland (46.0°N, 7.8°E) | 0.532 | 63% | Terrain and topography |

Best candidates more than 500 km from any known analog: Tien Shan (42.0°N, 80.0°E) at 0.620; Northern mid-latitudes (50.0°N, 86.1°E) at 0.565; Karakoram, Baltoro (35.7°N, 76.5°E) at 0.561.

Test plan: 9 requirements can be tested on Earth. The best single site passes 6. 3 site(s) together pass 9 (smallest possible set).

- Karakoram, Baltoro (35.7°N, 76.5°E): mean slope, terrain roughness, time with the sun low on the horizon, typical daily high, share of the day above freezing
- Antarctic (80.0°S, 152.3°E): mean surface temperature, mean solar energy flux, share of the day above freezing
- Tropics (5.0°N, 65.0°W): surface albedo, time with the sun low on the horizon, wind force on surfaces

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 9 | 0 | Northern mid-latitudes (65.0°N, 132.0°W) |
| 2 | 8 of 9 | 8,414 | Eureka, Ellesmere Island (80.0°N, 85.9°W) -> Tropics (5.0°N, 65.0°W) |
| 3 | 9 of 9 | 15,596 | Antarctic (80.0°S, 152.3°E) -> Tropics (5.0°S, 140.0°E) -> Northern mid-latitudes (55.0°N, 109.8°E) |

## Mars: Elysium Planitia (InSight)

Smooth volcanic plain.

Earth can test 52% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (83.2 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-65 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.721 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-106 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (2.31 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-64.8 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (177 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.255 Pa) is just beyond anything on Earth (0.258 Pa to 95.3 Pa). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Tropics (10.0°S, 63.4°W) | 0.567 | 62% | Terrain and topography |
| 2 | Tropics (0.0°N, 110.0°E) | 0.565 | 60% | Dust and wind |
| 3 | Tropics (0.0°N, 15.0°E) | 0.558 | 54% | Terrain and topography |
| 4 | Tropics (5.0°S, 55.0°W) | 0.555 | 54% | Terrain and topography |
| 5 | Tropics (5.0°S, 70.0°W) | 0.553 | 48% | Dust and wind |

Best candidates more than 500 km from any known analog: Tropics (10.0°S, 63.4°W) at 0.567; Tropics (0.0°N, 110.0°E) at 0.565; Tropics (0.0°N, 15.0°E) at 0.558.

Test plan: 10 requirements can be tested on Earth. The best single site passes 6. 3 site(s) together pass 10 (smallest possible set).

- Arctic (70.0°N, 122.4°E): mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Antarctic (80.0°S, 69.2°E): mean surface temperature, mean slope, terrain roughness, relief within the site, mean solar energy flux, share of the day above freezing
- Tropics (10.0°S, 63.4°W): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, wind force on surfaces

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 10 | 0 | Arctic (70.0°N, 122.4°E) |
| 2 | 9 of 10 | 6,672 | Antarctic (70.0°S, 64.8°W) -> Tropics (10.0°S, 63.4°W) |
| 3 | 10 of 10 | 9,575 | Dome Fuji, Antarctica (77.3°S, 39.7°E) -> Antarctic (70.0°S, 64.8°W) -> Tropics (10.0°S, 63.4°W) |

## Mars: Chryse Planitia (Viking 1)

Outflow-channel plain.

Earth can test 55% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (48.4 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Water in the shallow subsurface.** Liquid soil water cannot persist at the target’s mean temperature (-66 °C), so soil moisture is not a valid stand-in.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-90 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-65.9 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Dust optical depth.** The target value (1.05) is just beyond anything on Earth (0 to 0.926). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (166 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.
- **Wind force on surfaces.** The target value (0.151 Pa) is just beyond anything on Earth (0.258 Pa to 95.3 Pa). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (60.0°N, 110.0°E) | 0.525 | 49% | Water and ice |
| 2 | Northern mid-latitudes (60.0°N, 100.0°E) | 0.524 | 46% | Water and ice |
| 3 | Northern mid-latitudes (60.0°N, 110.0°W) | 0.508 | 38% | Water and ice |
| 4 | Northern mid-latitudes (60.0°N, 130.0°E) | 0.507 | 36% | Water and ice |
| 5 | Northern mid-latitudes (55.0°N, 74.6°W) | 0.499 | 31% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (60.0°N, 110.0°E) at 0.525; Northern mid-latitudes (60.0°N, 100.0°E) at 0.524; Northern mid-latitudes (60.0°N, 110.0°W) at 0.508.

Test plan: 11 requirements can be tested on Earth. The best single site passes 7. 3 site(s) together pass 11 (smallest possible set).

- Antarctic (80.0°S, 69.2°E): mean surface temperature, mean slope, terrain roughness, relief within the site, mean solar energy flux, typical daily high, share of the day above freezing
- Tropics (0.0°N, 110.0°E): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, wind force on surfaces
- Northern mid-latitudes (30.0°N, 104.5°E): dust optical depth, mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 7 of 11 | 0 | Antarctic (80.0°S, 69.2°E) |
| 2 | 10 of 11 | 8,348 | Antarctic (75.0°S, 104.2°E) -> Tropics (0.0°N, 110.0°E) |
| 3 | 11 of 11 | 11,684 | Antarctic (75.0°S, 104.2°E) -> Tropics (0.0°N, 110.0°E) -> Northern mid-latitudes (30.0°N, 110.3°E) |

## Mars: Vastitas Borealis (Phoenix)

High-latitude plain with shallow ground ice.

Earth can test 48% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Day-night temperature swing.** The target value (56.5 °C) is far outside Earth’s range (2.75 °C to 16.7 °C). No Earth site reproduces it.
- **Surface pressure.** The target value (0.778 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Typical daily low.** The target value (-85.8 °C) is far outside Earth’s range (-59.9 °C to 24.5 °C). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (3.39 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean surface temperature.** The target value (-57.5 °C) is just beyond anything on Earth (-57.5 °C to 30.6 °C). The most extreme Earth sites count at half weight.
- **Mean solar energy flux.** The target value (90.4 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (65.0°N, 96.0°E) | 0.740 | 94% | Water and ice |
| 2 | Northern mid-latitudes (65.0°N, 156.0°W) | 0.708 | 78% | Water and ice |
| 3 | Northern mid-latitudes (65.0°N, 144.0°W) | 0.686 | 57% | Water and ice |
| 4 | Arctic (70.0°N, 108.0°E) | 0.675 | 66% | Water and ice |
| 5 | Northern mid-latitudes (65.0°N, 120.0°W) | 0.670 | 55% | Water and ice |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (65.0°N, 96.0°E) at 0.740; Northern mid-latitudes (65.0°N, 156.0°W) at 0.708; Northern mid-latitudes (65.0°N, 144.0°W) at 0.686.

Test plan: 9 requirements can be tested on Earth. The best single site passes 6. 3 site(s) together pass 8 (smallest possible set).

- Antarctic (70.0°S, 64.8°W): mean slope, terrain roughness, relief within the site, time with the sun low on the horizon, typical daily high, share of the day above freezing
- Northern mid-latitudes (65.0°N, 96.0°E): mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon, share of the day above freezing
- Antarctic (75.0°S, 28.4°E): mean surface temperature, relief within the site, share of the day above freezing

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 9 | 0 | Antarctic (70.0°S, 64.8°W) |
| 2 | 7 of 9 | 1,310 | Antarctic (75.0°S, 28.4°E) -> Antarctic (70.0°S, 64.8°E) |
| 3 | 8 of 9 | 10,868 | Antarctic (70.0°S, 64.8°E) -> Antarctic (75.0°S, 28.4°E) -> Tropics (10.0°N, 7.6°E) |

## Mars: Arcadia Planitia

Mid-latitude plain with shallow ice; candidate human landing zone.

Earth can test 44% of this site's properties (balanced weights).

Where the analogy breaks down:

- **Surface pressure.** The target value (0.878 kPa) is far outside Earth’s range (55 kPa to 102 kPa). No Earth site reproduces it.
- **Liquid-water temperature window.** The target value (5.1 °C) is far outside Earth’s range (83.3 °C to 99.3 °C). No Earth site reproduces it.

Only partly reproducible:

- **Mean solar energy flux.** The target value (141 W/m²) is just beyond anything on Earth (178 W/m² to 416 W/m²). The most extreme Earth sites count at half weight.

| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |
|---|---|---|---|---|
| 1 | Northern mid-latitudes (40.0°N, 101.5°E) | 0.920 | 100% | Geology and surface materials |
| 2 | Northern mid-latitudes (25.0°N, 41.5°E) | 0.912 | 100% | Geology and surface materials |
| 3 | Northern mid-latitudes (45.0°N, 88.2°E) | 0.880 | 87% | Geology and surface materials |
| 4 | Northern mid-latitudes (40.0°N, 62.2°E) | 0.874 | 94% | Geology and surface materials |
| 5 | Southern mid-latitudes (25.0°S, 135.7°E) | 0.871 | 94% | Geology and surface materials |

Best candidates more than 500 km from any known analog: Northern mid-latitudes (40.0°N, 101.5°E) at 0.920; Northern mid-latitudes (25.0°N, 41.5°E) at 0.912; Northern mid-latitudes (45.0°N, 88.2°E) at 0.880.

Test plan: 7 requirements can be tested on Earth. The best single site passes 6. 2 site(s) together pass 7 (smallest possible set).

- Northern mid-latitudes (40.0°N, 101.5°E): water in the shallow subsurface, mean slope, terrain roughness, relief within the site, surface albedo, time with the sun low on the horizon
- Northern mid-latitudes (65.0°N, 120.0°E): mean slope, terrain roughness, relief within the site, surface albedo, mean solar energy flux

Field campaign (free-floating route): best coverage and shortest route per number of sites. Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.

| Sites | Requirements covered | Route km | Stops in order |
|---|---|---|---|
| 1 | 6 of 7 | 0 | Northern mid-latitudes (40.0°N, 101.5°E) |
| 2 | 7 of 7 | 2,802 | Northern mid-latitudes (40.0°N, 101.5°E) -> Northern mid-latitudes (65.0°N, 96.0°E) |
