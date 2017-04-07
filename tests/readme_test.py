from __future__ import absolute_import, division, print_function

import os
import tempfile
import unittest

import tests.test_helper as th
from core.configs.recon_config import ReconstructionConfig
from core.imgdata import saver
from readme import Readme


class ReadmeTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ReadmeTest, self).__init__(*args, **kwargs)
        self.config = ReconstructionConfig.empty_init()
        self.saver = saver.Saver(self.config)
        self.readme_dir = "ReadmeTest"

    def setUp(self):
        self.config = ReconstructionConfig.empty_init()

    def tearDown(self):
        th.delete_folder_from_temp(self.readme_dir)

    def test_begin(self):
        with tempfile.NamedTemporaryFile() as f:
            self.config.func.output_path = os.path.join(
                os.path.dirname(f.name), self.readme_dir)
            self.saver = saver.Saver(self.config)
            saver.make_dirs_if_needed(self.saver.get_output_path())
            readme = Readme(self.config, self.saver)
            readme.begin("made up command line", self.config)

            # assert that the file exists and is not empty
            # get the full name, but CROP the .txt as the end
            full_name = os.path.join(self.config.func.output_path,
                                     readme._readme_file_name[:-4])
            th.assert_files_exist(self, full_name, "txt")

    def test_begin_fails_when_dir_doesnt_exist(self):
        with tempfile.NamedTemporaryFile() as f:
            self.config.func.output_path = os.path.join(
                os.path.dirname(f.name), self.readme_dir)
            self.saver = saver.Saver(self.config)
            readme = Readme(self.config, self.saver)
            # assert that the file doesn't exist
            self.assertRaises(IOError, readme.begin, "made up command line",
                              self.config)

    def test_end_fails_with_no_begin_call(self):
        with tempfile.NamedTemporaryFile() as f:
            self.config.func.output_path = os.path.join(
                os.path.dirname(f.name), self.readme_dir)
            self.saver = saver.Saver(self.config)
            readme = Readme(self.config, self.saver)

            # assert that the file doesn't exist
            self.assertRaises(IOError, readme.end)

    def test_append_without_begin(self):
        with tempfile.NamedTemporaryFile() as f:
            self.config.func.output_path = os.path.join(
                os.path.dirname(f.name), self.readme_dir)
            self.saver = saver.Saver(self.config)
            Readme.total_string = ""  # this doesnt work, might have to add .erase method in readme
            readme = Readme(self.config, self.saver)
            test_str = "Test str"
            readme.append(test_str)
            self.assertEqual(
                len(readme),
                len(test_str) + 1)  # +1 to account for new line char
            self.assertEqual(readme.lines(), 1)

    def test_append_len_and_lines(self):
        with tempfile.NamedTemporaryFile() as f:
            self.config.func.output_path = os.path.join(
                os.path.dirname(f.name), self.readme_dir)
            self.saver = saver.Saver(self.config)
            readme = Readme(self.config, self.saver)
            Readme.total_string = ""
            test_str = "Test str"
            readme.append(test_str)
            readme.append(test_str)
            readme.append(test_str)
            readme.append(test_str)
            self.assertEqual(len(readme), (len(test_str) + 1) * 4)
            self.assertEqual(readme.lines(), 4)


if __name__ == '__main__':
    unittest.main()
