from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

from mantidimaging import helper as h
from mantidimaging.tests import test_helper as th


class RingRemovalTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RingRemovalTest, self).__init__(*args, **kwargs)

        from mantidimaging.core.filters import ring_removal
        self.alg = ring_removal

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        # invalid threshold
        run_ring_removal = False
        result = self.alg.execute(images, run_ring_removal, cores=1)
        npt.assert_equal(result, control)

    def test_memory_change_acceptable(self):
        images, control = th.gen_img_shared_array_and_copy()
        # invalid threshold

        run_ring_removal = False
        cached_memory = h.get_memory_usage_linux(kb=True)[0]
        result = self.alg.execute(images, run_ring_removal, cores=1)
        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        npt.assert_equal(result, control)


if __name__ == '__main__':
    unittest.main()
