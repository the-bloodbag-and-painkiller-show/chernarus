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
