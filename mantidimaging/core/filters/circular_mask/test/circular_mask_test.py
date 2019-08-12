import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.filters import circular_mask


class CircularMaskTest(unittest.TestCase):
    """
    Test circular mask filter.

    Tests return value and in-place modified data.
    """

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
        npt.assert_equal(images, control)

        ratio = 1
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

        ratio = -1
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

        ratio = None
        result = circular_mask.execute(images, ratio, mask_val)
        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        ratio = 0.001

        result = circular_mask.execute(images, ratio)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        # reset the input images
        images, control = th.gen_img_shared_array_and_copy()
        ratio = 0.994

        result = circular_mask.execute(images, ratio)

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
        ratio = 0.001

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = circular_mask.execute(images, ratio)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()
