import shutil
import tempfile
import unittest


class FileOutputtingTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FileOutputtingTestCase, self).__init__(*args, **kwargs)

        self.output_directory = None

    def setUp(self):
        self.output_directory = tempfile.mkdtemp(prefix='mantidimaging_test_tmp_')

    def tearDown(self):
        shutil.rmtree(path=self.output_directory, ignore_errors=True)
