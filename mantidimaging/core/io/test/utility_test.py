# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path

from mantidimaging.core.io import utility
from pyfakefs.fake_filesystem_unittest import TestCase


class UtilityTest(TestCase):
    def setUp(self) -> None:
        self.setUpPyfakefs()

    def test_get_candidate_file_extensions(self):
        self.assertEqual(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEqual(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEqual(['png'], utility.get_candidate_file_extensions('png'))

    def test_get_file_names(self):
        # Create test file with .tiff extension
        tiff_filename = '/dirname/test.tiff'
        self.fs.create_file(tiff_filename)

        # Search for files with .tif extension
        found_files = utility.get_file_names("/dirname", 'tif')

        # Expect to find the .tiff file
        self.assertEqual([tiff_filename], found_files)

    def test_find_log(self):
        log_name = "/a/sample_log.txt"
        self.fs.create_file(log_name)

        self.assertEqual(log_name, utility.find_log(Path("/a/b"), "sample"))
