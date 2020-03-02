import os

from mantidimaging.helper import initialise_logging
from mantidimaging.core.io import utility
from mantidimaging.test_helpers import FileOutputtingTestCase


class UtilityTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super(UtilityTest, self).__init__(*args, **kwargs)

        # force silent outputs
        initialise_logging()

    def test_get_candidate_file_extensions(self):
        self.assertEquals(['tif', 'tiff'], utility.get_candidate_file_extensions('tif'))

        self.assertEquals(['tiff', 'tif'], utility.get_candidate_file_extensions('tiff'))

        self.assertEquals(['png'], utility.get_candidate_file_extensions('png'))

    def test_get_file_names(self):
        # Create test file with .tiff extension
        tiff_filename = os.path.join(self.output_directory, 'test.tiff')
        with open(tiff_filename, 'wb') as tf:
            tf.write(b'\0')

        # Search for files with .tif extension
        found_files = utility.get_file_names(self.output_directory, 'tif')

        # Expect to find the .tiff file
        self.assertEquals([tiff_filename], found_files)
