import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.remove_stripe_sorting_fitting import RemoveStripeSortingFittingFilter


class RemoveStripeSortingFittingTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """
    def __init__(self, *args, **kwargs):
        super(RemoveStripeSortingFittingTest, self).__init__(*args, **kwargs)

    def test_executed(self):
        images = th.generate_images()
        control = images.copy()

        result = RemoveStripeSortingFittingFilter.filter_func(images)

        th.assert_not_equals(result.data, control.data)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        order = mock.Mock()
        order.value = mock.Mock(return_value=1)
        sigmax = mock.Mock()
        sigmax.value = mock.Mock(return_value=2)
        sigmay = mock.Mock()
        sigmay.value = mock.Mock(return_value=2)

        execute_func = RemoveStripeSortingFittingFilter.execute_wrapper(order, sigmax, sigmay)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(order.value.call_count, 1)
        self.assertEqual(sigmax.value.call_count, 1)
        self.assertEqual(sigmay.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
