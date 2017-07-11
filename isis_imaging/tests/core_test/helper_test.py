from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

from isis_imaging import helper as h
from isis_imaging.core.configs.recon_config import ReconstructionConfig
from isis_imaging.core.io.saver import Saver
from isis_imaging.readme_creator import Readme


class HelperTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HelperTest, self).__init__(*args, **kwargs)

    def setUp(self):
        config = ReconstructionConfig.empty_init()
        saver = Saver(config)
        readme = Readme(config, saver)
        h.set_readme(readme)

    def test_readme_caching(self):
        h.tomo_print("Testing verbosity at 0")
        self.assertGreater(len(h._readme), 0)

    def test_print_single_arg(self):
        h.tomo_print("Testing verbosity at 0")
        self.assertGreater(len(h._readme), 0)

    def test_pstop_raises_if_no_pstart(self):
        npt.assert_raises(ValueError, h.pstop, "dwad")


if __name__ == '__main__':
    unittest.main()
