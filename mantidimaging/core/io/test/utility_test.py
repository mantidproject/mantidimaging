# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path

from mantidimaging.core.io import utility
from pyfakefs.fake_filesystem_unittest import TestCase


class UtilityTest(TestCase):
    def setUp(self) -> None:
        self.setUpPyfakefs()

    def _file_list_count_equal(self, list1, list2):
        """Check that 2 lists of paths refer to the same files. Order independent"""
        self.assertCountEqual((Path(s).absolute() for s in list1), (Path(s).absolute() for s in list2))

    def test_get_candidate_file_extensions(self):
        self.assertEqual(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEqual(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEqual(['png'], utility.get_candidate_file_extensions('png'))

    def test_WHEN_tif_file_exists_THEN_tif_file_found_in_list(self):
        tiff_filename = Path('/dirname/test.tiff')
        self.fs.create_file(tiff_filename)

        found_files = utility.get_file_names("/dirname", 'tif')

        self._file_list_count_equal([tiff_filename], found_files)

    def test_WHEN_image_has_logfile_THEN_logfile_found_(self):
        log_name = Path("/a/b/TomoIMAT00010675_FlowerFine_log.txt")
        image_name = Path("/a/b/Tomo/IMAT_Flower_Tomo_000000.tif")
        self.fs.create_file(log_name)
        self.fs.create_file(image_name)

        log_found = utility.find_log_for_image(image_name)

        self.assertEqual(log_name, log_found)
