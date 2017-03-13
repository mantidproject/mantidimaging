from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from tests import test_helper as th


class OutliersTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OutliersTest, self).__init__(*args, **kwargs)

        # force silent outputs
        from configs.recon_config import ReconstructionConfig
        r = ReconstructionConfig.empty_init()
        r.func.verbosity = 0
        from helper import Helper

        from filters import outliers
        self.alg = outliers

        self.h = Helper(r)

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()
        # invalid thresholds
        threshold = None
        radius = 8
        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        npt.assert_equal(result, control)

        threshold = 0
        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        npt.assert_equal(result, control)

        threshold = -42
        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        npt.assert_equal(result, control)

        # no radius
        threshold = 42
        radius = 8
        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        npt.assert_equal(result, control)

    def test_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        threshold = 0.1
        radius = 8

        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        th.assert_not_equals(result, control)

        images, control = th.gen_img_shared_array_and_copy()
        threshold = 0.1
        result = self.alg.execute(images, threshold, radius, cores=1, h=self.h)
        th.assert_not_equals(result, control)

    def test_executed_no_helper(self):
        images, control = th.gen_img_shared_array_and_copy()

        threshold = 0.1
        radius = 8
        result = self.alg.execute(images, threshold, radius, cores=1)
        npt.assert_raises(AssertionError, npt.assert_equal, result, control)

        images, control = th.gen_img_shared_array_and_copy()
        threshold = 0.1
        result = self.alg.execute(images, threshold, radius, cores=1)
        npt.assert_raises(AssertionError, npt.assert_equal, result, control)


if __name__ == '__main__':
    unittest.main()
