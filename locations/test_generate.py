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
