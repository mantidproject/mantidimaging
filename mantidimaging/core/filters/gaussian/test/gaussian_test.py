import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.gaussian import GaussianFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class GaussianTest(unittest.TestCase):
    """
    Test gaussian filter.

    Tests return value and in-place modified data.

    Surprisingly sequential Gaussian seems to outperform parallel Gaussian on
    very small data.

    This does not scale and parallel execution is always faster on any
    reasonably sized data (e.g. 143,512,512)
    """

    def __init__(self, *args, **kwargs):
        super(GaussianTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = None
        mode = None
        order = None

        result = GaussianFilter()._filter_func(images, size, mode, order)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_parallel(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1

        result = GaussianFilter()._filter_func(images, size, mode, order)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

    def test_executed_no_helper_parallel(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1

        result = GaussianFilter()._filter_func(images, size, mode, order)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

    def test_executed_no_helper_seq(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1

        th.switch_mp_off()
        result = GaussianFilter()._filter_func(images, size, mode, order)
        th.switch_mp_on()

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

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
        order = 1

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = GaussianFilter()._filter_func(images, size, mode, order)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=0)
        order_field = mock.Mock()
        order_field.value = mock.Mock(return_value=0)
        execute_func = GaussianFilter().execute_wrapper(size_field, order_field, mode_field)

        images, _ = th.gen_img_shared_array_and_copy()
        execute_func(images)

        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)
        self.assertEqual(order_field.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
