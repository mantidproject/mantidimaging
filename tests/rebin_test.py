from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from tests import test_helper as th


class RebinTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RebinTest, self).__init__(*args, **kwargs)

        # force silent outputs
        from configs.recon_config import ReconstructionConfig
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = 0

        from filters import rebin
        self.alg = rebin

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        # bad params
        rebin = None
        mode = 'nearest'
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result, control)

        rebin = -1
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result, control)

        rebin = 0
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result, control)

        rebin = -0
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result, control)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        th.switch_mp_off()
        self.do_execute()
        th.switch_mp_on()

    def do_execute(self):
        images = th.gen_img_numpy_rand()

        rebin = 2.  # twice the size
        expected_shape = int(images.shape[1] * rebin)
        mode = 'nearest'
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result.shape[1], expected_shape)
        npt.assert_equal(result.shape[2], expected_shape)

        rebin = 5.  # five times the size
        expected_shape = int(images.shape[1] * rebin)
        result = self.alg.execute(images, rebin, mode)
        npt.assert_equal(result.shape[1], expected_shape)
        npt.assert_equal(result.shape[2], expected_shape)


if __name__ == '__main__':
    unittest.main()
