import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.outliers import OutliersFilter


class OutliersTest(unittest.TestCase):
    """
    Test outliers filter.

    Tests return value only.
    """
    def __init__(self, *args, **kwargs):
        super(OutliersTest, self).__init__(*args, **kwargs)

    def test_not_executed_no_threshold(self):
        images, control = th.gen_img_shared_array_and_copy()

        # invalid thresholds
        threshold = None
        radius = 8

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_bad_threshold(self):
        images, control = th.gen_img_shared_array_and_copy()

        radius = 8
        threshold = 0

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_bad_threshold2(self):
        images, control = th.gen_img_shared_array_and_copy()

        radius = 8
        threshold = -42

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_no_radius(self):
        images, control = th.gen_img_shared_array_and_copy()

        radius = 8
        threshold = 42
        radius = None

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        radius = 8
        threshold = 0.1

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        th.assert_not_equals(result, control)

        # TODO: in-place data test
        # th.assert_not_equals(images, control)

    def test_executed_no_helper(self):
        images, control = th.gen_img_shared_array_and_copy()

        threshold = 0.1
        radius = 8

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        npt.assert_raises(AssertionError, npt.assert_equal, result, control)

        # TODO: in-place data test
        # npt.assert_raises(AssertionError, npt.assert_equal, images, control)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        diff_field = mock.Mock()
        diff_field.value = mock.Mock(return_value=0)
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=0)
        execute_func = OutliersFilter.execute_wrapper(diff_field, size_field, mode_field)

        images, _ = th.gen_img_shared_array_and_copy()
        execute_func(images)

        self.assertEqual(diff_field.value.call_count, 1)
        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)


if __name__ == '__main__':
    unittest.main()
