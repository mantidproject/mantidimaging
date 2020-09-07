import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.clip_values import ClipValuesFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class ClipValuesFilterTest(unittest.TestCase):
    """
    Test clip values filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(ClipValuesFilterTest, self).__init__(*args, **kwargs)

    def test_execute_min_only(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=None,
                                                clip_min_new_value=0.1,
                                                clip_max_new_value=None)

        npt.assert_approx_equal(result.data.min(), 0.1)

    def test_execute_max_only(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=None,
                                                clip_max=0.8,
                                                clip_min_new_value=None,
                                                clip_max_new_value=0.9)

        npt.assert_approx_equal(result.data.max(), 0.9)

    def test_execute_min_max(self):
        images = th.generate_images()

        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=0.8,
                                                clip_min_new_value=0.1,
                                                clip_max_new_value=0.9)

        npt.assert_approx_equal(result.data.min(), 0.1)
        npt.assert_approx_equal(result.data.max(), 0.9)

    def test_execute_min_max_no_new_values(self):
        images = th.generate_images()
        result = ClipValuesFilter().filter_func(images,
                                                clip_min=0.2,
                                                clip_max=0.8,
                                                clip_min_new_value=None,
                                                clip_max_new_value=None)

        npt.assert_approx_equal(result.data.min(), 0.2)
        npt.assert_approx_equal(result.data.max(), 0.8)

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
        images = th.generate_images()

        cached_memory = get_memory_usage_linux(kb=True)[0]

        ClipValuesFilter().filter_func(images,
                                       clip_min=0.2,
                                       clip_max=0.8,
                                       clip_min_new_value=0.1,
                                       clip_max_new_value=0.9)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        # All widget arguments can use identical mocks for this test
        mocks = [mock.Mock() for _ in range(4)]
        for mock_widget in mocks:
            mock_widget.value = mock.Mock(return_value=0)
        execute_func = ClipValuesFilter().execute_wrapper(*mocks)

        images = th.generate_images()
        execute_func(images)

        for mock_widget in mocks:
            self.assertEqual(mock_widget.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
