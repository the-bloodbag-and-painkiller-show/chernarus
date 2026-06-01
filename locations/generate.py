"""Generate per-town drop-in cfgplayerspawnpoints.xml and cfgeventspawns.xml.

Run from the repo root:  python3 locations/generate.py
Or run tests from locations/:  python3 -m unittest test_generate -v
"""
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# --- Spawn ring tuning, by town category ------------------------------------
CATEGORY_PARAMS = {
    "Hamlet":     {"radius": 80,  "points": 10},
    "Village":    {"radius": 110, "points": 12},
    "Town":       {"radius": 150, "points": 14},
    "Small City": {"radius": 180, "points": 16},
    "Large City": {"radius": 220, "points": 18},
}
MIN_DIST_PLAYER = 20.0   # was 65 in the stock fresh section
MAX_DIST_PLAYER = 60.0   # was 150

# --- Heli-crash placement tuning --------------------------------------------
HELI_COUNT = 9           # target candidate positions per town (spec: 8-10)
DEFAULT_CLEARANCE = 30.0 # min metres from any building origin
CLEARANCE_FLOOR = 22.0   # relax no further than this
CLEARANCE_STEP = 2.0
GRID_SPACING = 15.0      # metres between sampled candidate points
FOOTPRINT_MARGIN = 50.0  # footprint radius = ring radius + this

# Building types whose footprint is large enough to need extra clearance.
# Matched by substring against the mapgrouppos `name` attribute.
LARGE_BUILDING_CLEARANCE = {
    "Tenement": 45.0,
    "Land_House_2": 40.0,
    "Apartment": 45.0,
    "Hangar": 50.0,
    "Warehouse": 45.0,
    "Industrial": 45.0,
    "Factory": 50.0,
    "Castle": 50.0,
}

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'


def slugify(name):
    """Town display name -> kebab-case folder slug (matches custom/ naming)."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
