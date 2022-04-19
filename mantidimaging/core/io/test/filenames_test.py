# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from parameterized import parameterized

from ..filenames import FilenamePattern


class FilenamePatternTest(unittest.TestCase):
    @parameterized.expand([
        ("foo", "foo", 0, ""),
        ("foo_0001.txt", "foo_", 4, ".txt"),
        # The 180 here is not an index
        ("IMAT00006388_PSI_cylinder_Sample_180deg.tif", "IMAT00006388_PSI_cylinder_Sample_180deg.tif", 0, ""),
        ("IMAT00006388_PSI_cylinder_Sample_000.tif", "IMAT00006388_PSI_cylinder_Sample_", 3, ".tif"),
        ("IMAT_Flower_Dark_Before_000000.tif", "IMAT_Flower_Dark_Before_", 6, ".tif"),
        ("IMAT_Flower_Dark_Before.json", "IMAT_Flower_Dark_Before.json", 0, ""),
    ])
    def test_pattern_from_name(self, filename, prefix, count, suffix):
        p1 = FilenamePattern.from_name(filename)
        self.assertEqual(p1.prefix, prefix)
        self.assertEqual(p1.digit_count, count)
        self.assertEqual(p1.suffix, suffix)

    def test_pattern_generate(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertEqual(p1.generate(23), "IMAT_Flower_Tomo_000023.tif")
        self.assertEqual(p1.generate(0), "IMAT_Flower_Tomo_000000.tif")

    def test_pattern_match(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertTrue(p1.match("IMAT_Flower_Tomo_000023.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo_0000.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo_000007.tiff"))

    def test_pattern_dont_match_180(self):
        p1 = FilenamePattern.from_name("IMAT00006388_PSI_cylinder_Sample_000.tif")
        self.assertTrue(p1.match("IMAT00006388_PSI_cylinder_Sample_943.tif"))
        self.assertFalse(p1.match("IMAT00006388_PSI_cylinder_Sample_180deg.tif"))
        self.assertFalse(p1.match("IMAT00006388_PSI_cylinder_Sample_360deg.tif"))

    def test_pattern_match_different_digits(self):
        # Allow cases where index has grown above padding
        p1 = FilenamePattern.from_name("img_000.tif")
        self.assertTrue(p1.match("img_000.tif"))
        self.assertTrue(p1.match("img_001.tif"))
        self.assertTrue(p1.match("img_999.tif"))
        self.assertTrue(p1.match("img_1000.tif"))
        self.assertFalse(p1.match("img_0000.tif"))

    def test_pattern_get_value(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertEqual(p1.get_value("IMAT_Flower_Tomo_000023.tif"), 23)
        self.assertRaises(ValueError, p1.get_value, "foo")
        self.assertRaises(ValueError, p1.get_value, "IMAT_Flower_Tomo_00002x.tif")

    def test_unindexed(self):
        p1 = FilenamePattern.from_name("IMAT00006388_PSI_cylinder_Sample_180deg.tif")
        self.assertEqual(p1.get_value("IMAT00006388_PSI_cylinder_Sample_180deg.tif"), 0)
        self.assertEqual(p1.generate(0), "IMAT00006388_PSI_cylinder_Sample_180deg.tif")
