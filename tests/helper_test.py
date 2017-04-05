from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

import helper as h
from core.configs.recon_config import ReconstructionConfig


class HelperTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HelperTest, self).__init__(*args, **kwargs)

    def test_readme_caching(self):
        config = ReconstructionConfig.empty_init()

        from core.imgdata.saver import Saver
        saver = Saver(config)

        from readme import Readme
        readme = Readme(config, saver)
        h.set_readme(readme)
        h.tomo_print("Testing verbosity at 0")
        # cache output even when verbosity is 0
        self.assertGreater(len(h._readme), 0)

    def test_pstop_raises_if_no_pstart(self):
        npt.assert_raises(ValueError, h.pstop, "dwad")


if __name__ == '__main__':
    unittest.main()
