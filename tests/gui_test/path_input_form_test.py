from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
import mock
from tests import test_helper as th


class PathInputFormTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PathInputFormTest, self).__init__(*args, **kwargs)

        # force silent outputs
        from configs.recon_config import ReconstructionConfig
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = 0

        from gui import path_input_form
        self.form = path_input_form.PathInputForm(test=True)

    def test_proper_path_setting(self):
        f = self.form

        # test the properties
        expected_path_sample = '~/test/path/data'
        expected_path_flat = '~/test/path/flat'
        expected_path_dark = '~/test/path/dark'

        f.path_sample = expected_path_sample
        f.path_flat = expected_path_flat
        f.path_dark = expected_path_dark

        self.assertEqual(f.path_sample, expected_path_sample)
        self.assertEqual(f.path_flat, expected_path_flat)
        self.assertEqual(f.path_dark, expected_path_dark)


if __name__ == '__main__':
    unittest.main()
