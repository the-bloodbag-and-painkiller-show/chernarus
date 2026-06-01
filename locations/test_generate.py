import math
import unittest

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
