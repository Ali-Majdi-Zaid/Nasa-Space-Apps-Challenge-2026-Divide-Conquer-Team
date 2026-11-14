"""Mission presets.

"Analog" only means something relative to a purpose: a good place to test
a rover is not necessarily a good place to study habitability. Each preset
is a set of dimension weights (0 = ignore, 3 = critical). Users can adjust
them in the dashboard.
"""
from .schema import DIMENSIONS

PRESETS = {
    "balanced": dict(
        label="Balanced",
        about="Every dimension counts equally.",
        weights={d: 1.0 for d in DIMENSIONS}),
    "rover": dict(
        label="Rover and mobility testing",
        about="Ground a vehicle has to cross: slopes, roughness, dust, loose material.",
        weights=dict(terrain=3, dust=2, geology=2, thermal=1, illumination=1, water=0.5, habitability=0, physics=0.5)),
    "astrobiology": dict(
        label="Astrobiology and habitability",
        about="Where life would struggle in the same ways: water, radiation, chemistry.",
        weights=dict(water=3, habitability=3, geology=2, thermal=1.5, dust=1, terrain=0.5, illumination=0.5, physics=0.5)),
    "crew": dict(
        label="Crew and habitat operations",
        about="What people and habitats must endure: cold, darkness, isolation, dust.",
        weights=dict(thermal=3, illumination=3, terrain=1.5, dust=1.5, water=1, geology=0.5, habitability=0.5, physics=1)),
    "resources": dict(
        label="Resource extraction",
        about="Ice and regolith to dig, process and build with.",
        weights=dict(water=3, geology=3, terrain=1.5, thermal=1, illumination=1, dust=0.5, habitability=0, physics=0)),
}
