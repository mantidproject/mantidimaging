# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path

from mantidimaging.core.io import utility

from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase


class UtilityTest(FakeFSTestCase):
    def test_get_candidate_file_extensions(self):
        self.assertEqual(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEqual(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEqual(['png'], utility.get_candidate_file_extensions('png'))

    def test_WHEN_tif_file_exists_THEN_tif_file_found_in_list(self):
        tiff_filename = Path('/dirname/test.tiff')
        self.fs.create_file(tiff_filename)

        found_files = utility.get_file_names("/dirname", 'tif')

        self._file_list_count_equal([tiff_filename], found_files)
