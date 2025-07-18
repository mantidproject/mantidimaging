# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path

from mantidimaging.core.io.utility import find_first_file_that_is_possibly_a_sample
from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase


class UtilityTest(FakeFSTestCase):

    def test_find_possible_sample(self):
        files = "a/a.txt a/flat_0.tif a/dark_1.tif a/a_0.tif a/a_1.tif".split()
        for f in files:
            self.fs.create_file(f)
        found = find_first_file_that_is_possibly_a_sample(Path("a"))
        self.assertIsNotNone(found)
        self._files_equal(found, "a/a_0.tif")

    def test_find_possible_sample_no_good_file(self):
        files = "a/a.txt a/flat_0.tif a/dark_1.tif".split()
        for f in files:
            self.fs.create_file(f)
        found = find_first_file_that_is_possibly_a_sample(Path("a"))
        self.assertIsNone(found)
