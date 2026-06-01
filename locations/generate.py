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


def ring_points(cx, cz, radius, n):
    """n points evenly spaced on a circle of `radius` about (cx, cz)."""
    out = []
    for i in range(n):
        ang = 2.0 * math.pi * i / n
        out.append((cx + radius * math.cos(ang), cz + radius * math.sin(ang)))
    return out


def load_buildings(xml_text):
    """Parse mapgrouppos XML text -> list of (x, z, type_name)."""
    out = []
    pat = re.compile(r'<group name="([^"]+)" pos="([0-9.\-]+) [0-9.\-]+ ([0-9.\-]+)"')
    for m in pat.finditer(xml_text):
        out.append((float(m.group(2)), float(m.group(3)), m.group(1)))
    return out


def large_clearance(type_name):
    """Extra clearance for big-footprint building types; 0.0 if not large."""
    best = 0.0
    for key, val in LARGE_BUILDING_CLEARANCE.items():
        if key in type_name and val > best:
            best = val
    return best


def required_clearance(type_name, base):
    """Clearance a heli must keep from this building: max(base, large bump)."""
    return max(base, large_clearance(type_name))


def is_clear(point, buildings, base):
    """True if `point` is at least required_clearance from every building."""
    px, pz = point
    for bx, bz, bt in buildings:
        rc = required_clearance(bt, base)
        if (px - bx) ** 2 + (pz - bz) ** 2 < rc * rc:
            return False
    return True


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def grid_candidates(center, radius, spacing=GRID_SPACING):
    """Grid-sampled points within `radius` of center (center point included)."""
    cx, cz = center
    out = []
    steps = int(radius // spacing)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            x, z = cx + i * spacing, cz + j * spacing
            if (x - cx) ** 2 + (z - cz) ** 2 <= radius * radius:
                out.append((x, z))
    return out


def farthest_point_sample(candidates, k, seed):
    """Pick up to k candidates spread apart, starting nearest to `seed`."""
    if not candidates:
        return []
    chosen = [min(candidates, key=lambda c: _dist2(c, seed))]
    while len(chosen) < k and len(chosen) < len(candidates):
        best, best_d = None, -1.0
        for c in candidates:
            if c in chosen:
                continue
            d = min(_dist2(c, ch) for ch in chosen)
            if d > best_d:
                best_d, best = d, c
        chosen.append(best)
    return chosen
