import unittest

import numpy.testing as npt

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.filters import cut_off


class CutOffTest(unittest.TestCase):
    """
    Test cut-off filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(CutOffTest, self).__init__(*args, **kwargs)

    def test_execute(self):
        images, control = th.gen_img_shared_array_and_copy()
        threshold = 0.5

        previous_max = images.max()
        result = cut_off.execute(images, threshold=threshold)
        new_max = images.max()

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

        self.assertTrue(new_max < previous_max,
                        "New maximum value should be less than maximum value "
                        "before processing")

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

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = cut_off.execute(images, threshold=0.5)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()
