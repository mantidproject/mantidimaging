import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.cut_off import CutOffFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


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
        result = CutOffFilter.filter_func(images, threshold=threshold)
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

        result = CutOffFilter.filter_func(images, threshold=0.5)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        threshold_field = mock.Mock()
        threshold_field.value = mock.Mock(return_value=0)
        execute_func = CutOffFilter.execute_wrapper(threshold_field)

        images, _ = th.gen_img_shared_array_and_copy()
        execute_func(images)

        self.assertEqual(threshold_field.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
