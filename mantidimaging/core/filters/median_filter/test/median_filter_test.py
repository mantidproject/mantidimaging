from __future__ import (absolute_import, division, print_function)

import unittest

import numpy.testing as npt

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux
from mantidimaging.test import test_helper as th

from mantidimaging.core.filters import median_filter


class MedianTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(MedianTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = None
        mode = None

        result = median_filter.execute(images, size, mode)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_no_helper_parallel(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'

        result = median_filter.execute(images, size, mode)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_executed_no_helper_seq(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'

        th.switch_mp_off()
        result = median_filter.execute(images, size, mode)
        th.switch_mp_on()

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

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
        size = 3
        mode = 'reflect'

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = median_filter.execute(images, size, mode)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()
