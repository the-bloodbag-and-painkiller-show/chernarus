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
    if k <= 0:
        return []
    candidates = list(dict.fromkeys(candidates))
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


def active_event_names(events_xml_text):
    """Names of events with <active>1</active> in db/events.xml.

    Note: the returned set may include Infected* variants that have no
    matching <event> in the cfgeventspawns template.  Those names are simply
    never emitted (intersection semantics) — that's expected, not a bug.
    """
    root = ET.fromstring(events_xml_text)
    out = set()
    for ev in root.findall("event"):
        active = ev.findtext("active", default="0").strip()
        if active == "1" and ev.get("name"):
            out.add(ev.get("name"))
    return out


def _fmt(v):
    """Format a coordinate float the way DayZ configs do."""
    return f"{v:.6f}"


def render_playerspawnpoints(template_text, ring, group_name):
    """Replace every section's pos-bubbles with one ring group; tighten distances."""
    root = ET.fromstring(template_text)
    for section in ("fresh", "hop", "travel"):
        sec = root.find(section)
        if sec is None:
            continue
        sp = sec.find("spawn_params")
        if sp is not None:
            for tag, val in (("min_dist_player", MIN_DIST_PLAYER),
                             ("max_dist_player", MAX_DIST_PLAYER)):
                el = sp.find(tag)
                if el is not None:
                    el.text = str(int(val))
        bubbles = sec.find("generator_posbubbles")
        if bubbles is None:
            continue
        for child in list(bubbles):
            bubbles.remove(child)
        grp = ET.SubElement(bubbles, "group", {"name": group_name})
        for x, z in ring:
            ET.SubElement(grp, "pos", {"x": _fmt(x), "z": _fmt(z)})
    ET.indent(root)
    return XML_DECL + ET.tostring(root, encoding="unicode")


def render_eventspawns(template_text, heli_positions, keep_names):
    """Strip dead events; relocate StaticHeliCrash; keep the rest of keep_names."""
    root = ET.fromstring(template_text)
    for ev in list(root.findall("event")):
        name = ev.get("name")
        if name not in keep_names:
            root.remove(ev)
            continue
        if name == "StaticHeliCrash":
            for pos in ev.findall("pos"):
                ev.remove(pos)  # keep <zone>, drop old <pos>
            for x, z in heli_positions:
                ET.SubElement(ev, "pos", {"x": _fmt(x), "z": _fmt(z), "a": "-1"})
    ET.indent(root)
    return XML_DECL + ET.tostring(root, encoding="unicode")


def find_heli_positions(center, footprint_r, buildings, count=HELI_COUNT):
    """Return (positions, used_base): open heli spots scattered in the footprint.

    Relaxes the clearance base from DEFAULT_CLEARANCE down to CLEARANCE_FLOOR
    until at least `count` open candidates exist. Large building types keep
    their bumped clearance regardless of base (see required_clearance).
    """
    cands = grid_candidates(center, footprint_r)
    # Only buildings near the footprint can matter (footprint + biggest bump).
    reach = footprint_r + max([DEFAULT_CLEARANCE] + list(LARGE_BUILDING_CLEARANCE.values()))
    nearby = [b for b in buildings if _dist2((b[0], b[1]), center) <= reach * reach]

    base = DEFAULT_CLEARANCE
    clear = []
    while True:
        clear = [c for c in cands if is_clear(c, nearby, base)]
        if len(clear) >= count or base <= CLEARANCE_FLOOR:
            break
        base -= CLEARANCE_STEP
    return farthest_point_sample(clear, count, center), base


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCATIONS_DIR = Path(__file__).resolve().parent


def build_town(town, buildings, spawn_template, event_template, keep_names):
    """Produce one town's slug, params, and both rendered XML strings."""
    params = CATEGORY_PARAMS[town["cat"]]
    cx, cz = float(town["cx"]), float(town["cz"])
    slug = slugify(town["name"])
    ring = ring_points(cx, cz, params["radius"], params["points"])
    footprint_r = params["radius"] + FOOTPRINT_MARGIN
    heli, used_base = find_heli_positions((cx, cz), footprint_r, buildings)
    return {
        "name": town["name"],
        "slug": slug,
        "category": town["cat"],
        "center_x": round(cx),
        "center_z": round(cz),
        "spawn_radius": params["radius"],
        "spawn_points": params["points"],
        "heli_count": len(heli),
        "heli_clearance": used_base,
        "spawn_xml": render_playerspawnpoints(spawn_template, ring, slug),
        "event_xml": render_eventspawns(event_template, heli, keep_names),
    }


def _xmllint_ok(path):
    r = subprocess.run(["xmllint", "--noout", str(path)],
                       capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def main():
    towns = json.loads((REPO_ROOT / "docs" / "town-centers.json").read_text())
    buildings = load_buildings((REPO_ROOT / "mapgrouppos.xml").read_text())
    spawn_template = (REPO_ROOT / "cfgplayerspawnpoints.xml").read_text()
    event_template = (REPO_ROOT / "cfgeventspawns.xml").read_text()
    keep_names = active_event_names((REPO_ROOT / "db" / "events.xml").read_text())

    index = []
    warnings = []
    for town in towns:
        r = build_town(town, buildings, spawn_template, event_template, keep_names)
        dest = LOCATIONS_DIR / r["slug"]
        dest.mkdir(exist_ok=True)
        (dest / "cfgplayerspawnpoints.xml").write_text(r["spawn_xml"])
        (dest / "cfgeventspawns.xml").write_text(r["event_xml"])
        for fname in ("cfgplayerspawnpoints.xml", "cfgeventspawns.xml"):
            ok, detail = _xmllint_ok(dest / fname)
            if not ok:
                warnings.append(f"INVALID XML: {r['slug']}/{fname} :: {detail}")
        if r["heli_count"] < HELI_COUNT:
            warnings.append(
                f"{r['slug']}: only {r['heli_count']} heli spots "
                f"(clearance relaxed to {r['heli_clearance']}m)")
        index.append({k: r[k] for k in (
            "name", "slug", "category", "center_x", "center_z",
            "spawn_radius", "spawn_points", "heli_count")})

    (LOCATIONS_DIR / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"Generated {len(index)} towns.")
    for w in warnings:
        print("  WARN:", w)


if __name__ == "__main__":
    main()
