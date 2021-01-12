# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from pathlib import Path

from mantidimaging.helper import initialise_logging
from mantidimaging.core.io import utility
from mantidimaging.test_helpers import FileOutputtingTestCase


class UtilityTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super(UtilityTest, self).__init__(*args, **kwargs)

        # force silent outputs
        initialise_logging()

    def test_get_candidate_file_extensions(self):
        self.assertEqual(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEqual(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEqual(['png'], utility.get_candidate_file_extensions('png'))

    def test_get_file_names(self):
        # Create test file with .tiff extension
        tiff_filename = os.path.join(self.output_directory, 'test.tiff')
        with open(tiff_filename, 'wb') as tf:
            tf.write(b'\0')

        # Search for files with .tif extension
        found_files = utility.get_file_names(self.output_directory, 'tif')

        # Expect to find the .tiff file
        self.assertEqual([tiff_filename], found_files)

    def test_find_log(self):
        with open(os.path.join(self.output_directory, "../sample_log.txt"), 'w') as f:
            f.write("sample logs")

        self.assertNotEqual("", utility.find_log(Path(self.output_directory), "sample"))
