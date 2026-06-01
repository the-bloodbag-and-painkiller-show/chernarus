import math
import unittest
import xml.etree.ElementTree as ET

import generate


class TestSlugify(unittest.TestCase):
    def test_single_word(self):
        self.assertEqual(generate.slugify("Balota"), "balota")

    def test_two_words(self):
        self.assertEqual(generate.slugify("Novy Sobor"), "novy-sobor")

    def test_belaya_polana(self):
        self.assertEqual(generate.slugify("Belaya Polana"), "belaya-polana")


class TestRingPoints(unittest.TestCase):
    def test_count(self):
        pts = generate.ring_points(0.0, 0.0, 100.0, 12)
        self.assertEqual(len(pts), 12)

    def test_positions_on_circle(self):
        pts = generate.ring_points(1000.0, 2000.0, 100.0, 4)
        # i=0 -> (1100, 2000), i=1 -> (1000, 2100)
        self.assertAlmostEqual(pts[0][0], 1100.0, places=4)
        self.assertAlmostEqual(pts[0][1], 2000.0, places=4)
        self.assertAlmostEqual(pts[1][0], 1000.0, places=4)
        self.assertAlmostEqual(pts[1][1], 2100.0, places=4)

    def test_all_at_radius(self):
        for x, z in generate.ring_points(500.0, 500.0, 80.0, 10):
            self.assertAlmostEqual(math.hypot(x - 500.0, z - 500.0), 80.0, places=4)


BUILDINGS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<map>
    <group name="Land_Shed_W2" pos="100.5 12.0 200.5" rpy="0 0 0" a="1" />
    <group name="Land_Tenement_Small" pos="300 5 400" rpy="0 0 0" a="2" />
</map>
"""

class TestLoadBuildings(unittest.TestCase):
    def test_parses_x_and_z(self):
        b = generate.load_buildings(BUILDINGS_XML)
        self.assertEqual(b, [
            (100.5, 200.5, "Land_Shed_W2"),
            (300.0, 400.0, "Land_Tenement_Small"),
        ])


class TestClearance(unittest.TestCase):
    def test_large_clearance_match(self):
        self.assertEqual(generate.large_clearance("Land_Tenement_Small"), 45.0)

    def test_large_clearance_none(self):
        self.assertEqual(generate.large_clearance("Land_Shed_W2"), 0.0)

    def test_required_default(self):
        self.assertEqual(generate.required_clearance("Land_Shed_W2", 30.0), 30.0)

    def test_required_uses_large_bump(self):
        # large type keeps its 45 even when base is relaxed to 22
        self.assertEqual(generate.required_clearance("Land_Tenement_Small", 22.0), 45.0)

    def test_is_clear_far_small_building(self):
        self.assertTrue(generate.is_clear((0.0, 0.0), [(40.0, 0.0, "Land_Shed_W2")], 30.0))

    def test_is_clear_too_close_small(self):
        self.assertFalse(generate.is_clear((0.0, 0.0), [(25.0, 0.0, "Land_Shed_W2")], 30.0))

    def test_is_clear_blocked_by_large(self):
        # 40m away but a Tenement needs 45m
        self.assertFalse(generate.is_clear((0.0, 0.0), [(40.0, 0.0, "Land_Tenement_Small")], 30.0))


class TestCandidates(unittest.TestCase):
    def test_grid_within_circle(self):
        pts = generate.grid_candidates((0.0, 0.0), 30.0, spacing=15.0)
        self.assertTrue(len(pts) > 0)
        for x, z in pts:
            self.assertLessEqual(math.hypot(x, z), 30.0 + 1e-9)

    def test_grid_includes_center(self):
        pts = generate.grid_candidates((100.0, 200.0), 30.0, spacing=15.0)
        self.assertIn((100.0, 200.0), pts)

    def test_fps_returns_k(self):
        cands = [(float(i), 0.0) for i in range(20)]
        sel = generate.farthest_point_sample(cands, 5, (0.0, 0.0))
        self.assertEqual(len(sel), 5)

    def test_fps_spreads_out(self):
        # On a line 0..19, FPS from seed 0 should include the far end (19)
        cands = [(float(i), 0.0) for i in range(20)]
        sel = generate.farthest_point_sample(cands, 5, (0.0, 0.0))
        self.assertIn((19.0, 0.0), sel)

    def test_fps_handles_fewer_than_k(self):
        cands = [(0.0, 0.0), (10.0, 0.0)]
        sel = generate.farthest_point_sample(cands, 5, (0.0, 0.0))
        self.assertEqual(len(sel), 2)

    def test_fps_deduplicates(self):
        result = generate.farthest_point_sample(
            [(0.0, 0.0), (0.0, 0.0), (10.0, 0.0)], 3, (0.0, 0.0))
        self.assertNotIn(None, result)
        self.assertEqual(len(result), len(set(result)))

    def test_fps_zero_k(self):
        result = generate.farthest_point_sample(
            [(1.0, 1.0), (2.0, 2.0)], 0, (0.0, 0.0))
        self.assertEqual(result, [])


class TestFindHeli(unittest.TestCase):
    def test_open_field_returns_count(self):
        positions, used_base = generate.find_heli_positions(
            (0.0, 0.0), footprint_r=100.0, buildings=[], count=9)
        self.assertEqual(len(positions), 9)
        self.assertEqual(used_base, generate.DEFAULT_CLEARANCE)
        for x, z in positions:
            self.assertLessEqual(math.hypot(x, z), 100.0 + 1e-9)

    def test_avoids_building(self):
        # One building at origin -> every chosen point must clear 30m from it
        positions, _ = generate.find_heli_positions(
            (0.0, 0.0), footprint_r=100.0,
            buildings=[(0.0, 0.0, "Land_Shed_W2")], count=9)
        for x, z in positions:
            self.assertGreaterEqual(math.hypot(x, z), 30.0)


EVENTS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<events>
    <event name="Loot"><active>1</active><nominal>0</nominal></event>
    <event name="VehicleCivilianSedan"><active>0</active></event>
    <event name="StaticHeliCrash"><active>1</active><nominal>3</nominal></event>
</events>
"""

class TestActiveEvents(unittest.TestCase):
    def test_only_active(self):
        names = generate.active_event_names(EVENTS_XML)
        self.assertEqual(names, {"Loot", "StaticHeliCrash"})


SPAWN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<playerspawnpoints>
    <fresh>
        <spawn_params>
            <min_dist_player>65</min_dist_player>
            <max_dist_player>150</max_dist_player>
        </spawn_params>
        <generator_posbubbles>
            <group name="OldTown">
                <pos x="1.0" z="2.0" />
                <pos x="3.0" z="4.0" />
            </group>
        </generator_posbubbles>
    </fresh>
    <hop>
        <spawn_params>
            <min_dist_player>25</min_dist_player>
            <max_dist_player>70</max_dist_player>
        </spawn_params>
        <generator_posbubbles>
            <group name="OldHop"><pos x="9.0" z="9.0" /></group>
        </generator_posbubbles>
    </hop>
</playerspawnpoints>
"""

EVENTSPAWNS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<eventposdef>
    <event name="VehicleCivilianSedan">
        <pos x="1.0" z="1.0" a="0" />
    </event>
    <event name="Loot">
        <pos x="2.0" z="2.0" a="0" />
    </event>
    <event name="StaticHeliCrash">
        <zone smin="1" smax="3" dmin="3" dmax="5" r="45" />
        <pos x="500.0" z="500.0" a="-1" />
        <pos x="600.0" z="600.0" a="-1" />
    </event>
</eventposdef>
"""

class TestRenderEvents(unittest.TestCase):
    def setUp(self):
        self.keep = {"Loot", "StaticHeliCrash"}
        self.heli = [(10.0, 20.0), (30.0, 40.0)]
        self.out = generate.render_eventspawns(EVENTSPAWNS_TEMPLATE, self.heli, self.keep)
        self.root = ET.fromstring(self.out)

    def _event(self, name):
        for ev in self.root.findall("event"):
            if ev.get("name") == name:
                return ev
        return None

    def test_dead_event_removed(self):
        self.assertIsNone(self._event("VehicleCivilianSedan"))

    def test_loot_kept(self):
        self.assertIsNotNone(self._event("Loot"))

    def test_heli_positions_replaced(self):
        heli = self._event("StaticHeliCrash")
        self.assertIsNotNone(heli.find("zone"))  # zone preserved
        positions = heli.findall("pos")
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions[0].get("a"), "-1")
        coords = {(p.get("x"), p.get("z")) for p in positions}
        self.assertIn((generate._fmt(10.0), generate._fmt(20.0)), coords)
        self.assertNotIn(("500.0", "500.0"), coords)  # old positions gone


class TestRenderSpawns(unittest.TestCase):
    def test_replaces_groups_and_distances(self):
        ring = [(100.0, 200.0), (300.0, 400.0)]
        out = generate.render_playerspawnpoints(SPAWN_TEMPLATE, ring, "novy-sobor")
        root = ET.fromstring(out)
        for section in ("fresh", "hop"):
            sec = root.find(section)
            bubbles = sec.find("generator_posbubbles")
            groups = bubbles.findall("group")
            self.assertEqual(len(groups), 1)
            self.assertEqual(len(groups[0].findall("pos")), 2)
            self.assertEqual(sec.findtext("spawn_params/min_dist_player"), str(int(generate.MIN_DIST_PLAYER)))
            self.assertEqual(sec.findtext("spawn_params/max_dist_player"), str(int(generate.MAX_DIST_PLAYER)))

    def test_starts_with_xml_declaration(self):
        out = generate.render_playerspawnpoints(SPAWN_TEMPLATE, [(1.0, 2.0)], "x")
        self.assertTrue(out.startswith("<?xml"))


class TestBuildTown(unittest.TestCase):
    def test_build_town_outputs(self):
        town = {"name": "Novy Sobor", "cat": "Village", "cx": 7100, "cz": 7700}
        result = generate.build_town(
            town,
            buildings=[],
            spawn_template=SPAWN_TEMPLATE,
            event_template=EVENTSPAWNS_TEMPLATE,
            keep_names={"Loot", "StaticHeliCrash"},
        )
        self.assertEqual(result["slug"], "novy-sobor")
        self.assertEqual(result["spawn_points"], 12)   # Village -> 12
        self.assertEqual(result["spawn_radius"], 110)
        # spawn XML well-formed and has 12 ring pos in fresh
        sroot = ET.fromstring(result["spawn_xml"])
        self.assertEqual(
            len(sroot.find("fresh/generator_posbubbles/group").findall("pos")), 12)
        # event XML well-formed with 9 heli positions
        eroot = ET.fromstring(result["event_xml"])
        heli = [e for e in eroot.findall("event") if e.get("name") == "StaticHeliCrash"][0]
        self.assertEqual(len(heli.findall("pos")), 9)
        self.assertEqual(result["heli_count"], 9)
