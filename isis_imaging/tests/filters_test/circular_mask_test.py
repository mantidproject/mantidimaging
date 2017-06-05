from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from isis_imaging import helper as h
from isis_imaging.tests import test_helper as th
from isis_imaging.core.filters import circular_mask


class CircularMaskTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CircularMaskTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        # Check that the filter is not executed when:
        #     - no ratio is provided
        #     - 0 < ratio < 1 is false
        images, control = th.gen_img_shared_array_and_copy()

        ratio = 0
        mask_val = 0.
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)

        ratio = 1
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)

        ratio = -1
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)

        ratio = None
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)

    def test_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        ratio = 0.001
        result = circular_mask.execute(images, ratio)
        th.assert_not_equals(result, control)

        # reset the input images
        images, control = th.gen_img_shared_array_and_copy()
        ratio = 0.994
        result = circular_mask.execute(images, ratio)
        th.assert_not_equals(result, control)

    def test_memory_change_acceptable(self):
        """
        Expected behaviour for the filter is to be done in place
        without using more memory.
        In reality the memory is increased by about 40MB (4 April 2017),
        but this could change in the future.
        The reason why a 10% window is given on the expected size is
        to account for any library imports that may happen.
        This will still capture if the data is doubled, which is the main goal.
        """
        images, control = th.gen_img_shared_array_and_copy()

        ratio = 0.001
        cached_memory = h.get_memory_usage_linux(kb=True)[0]
        result = circular_mask.execute(images, ratio)
        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        th.assert_not_equals(result, control)


if __name__ == '__main__':
    unittest.main()
