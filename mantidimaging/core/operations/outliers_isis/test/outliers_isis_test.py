import unittest
from unittest import mock

import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.outliers_isis import OutliersISISFilter


class OutliersISISTest(unittest.TestCase):
    """
    Test outliers filter.

    Tests return value only.
    """
    def __init__(self, *args, **kwargs):
        super(OutliersISISTest, self).__init__(*args, **kwargs)

    def test_executed(self):
        images = th.generate_images()

        radius = 8
        threshold = 0.1

        sample = np.copy(images.data)
        result = OutliersISISFilter.filter_func(images, threshold, radius, cores=1)

        th.assert_not_equals(result.data, sample)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        diff_field = mock.Mock()
        diff_field.value = mock.Mock(return_value=0)
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        apply_to_field = mock.Mock()
        apply_to_field.currentText = mock.Mock(return_value="Projections")
        execute_func = OutliersISISFilter.execute_wrapper(diff_field, size_field, apply_to_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(diff_field.value.call_count, 1)
        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(apply_to_field.currentText.call_count, 1)

    def test_apply_to_field_accepts_projections(self):
        diff_field = mock.Mock()
        diff_field.value = mock.Mock(return_value=0)
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        apply_to_field = mock.Mock()
        apply_to_field.currentText = mock.Mock(return_value="Projections")
        execute_func = OutliersISISFilter.execute_wrapper(diff_field, size_field, apply_to_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(diff_field.value.call_count, 1)
        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(apply_to_field.currentText.call_count, 1)

    def test_apply_to_field_accepts_sinograms(self):
        diff_field = mock.Mock()
        diff_field.value = mock.Mock(return_value=0)
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        apply_to_field = mock.Mock()
        apply_to_field.currentText = mock.Mock(return_value="Sinograms")
        execute_func = OutliersISISFilter.execute_wrapper(diff_field, size_field, apply_to_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(diff_field.value.call_count, 1)
        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(apply_to_field.currentText.call_count, 2)

    def test_apply_to_field_throws_attribute_error(self):
        apply_to_field = mock.Mock()
        apply_to_field.currentText = mock.Mock(return_value="AbsoluteRandomRubbish")

        error_called = False
        try:
            OutliersISISFilter.execute_wrapper(None, None, apply_to_field)
        except AttributeError as error:
            error_called = True
            self.assertEqual(str(error), "apply_to_field not given a valid input.")

        self.assertEqual(apply_to_field.currentText.call_count, 2)
        self.assertTrue(error_called)


if __name__ == '__main__':
    unittest.main()
