# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.core.io import utility

from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase


class UtilityTest(FakeFSTestCase):
    def test_get_candidate_file_extensions(self):
        self.assertEqual(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEqual(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEqual(['png'], utility.get_candidate_file_extensions('png'))
