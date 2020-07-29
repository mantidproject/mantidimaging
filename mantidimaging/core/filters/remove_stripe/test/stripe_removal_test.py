import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.remove_stripe import StripeRemovalFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class StripeRemovalTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """
    def __init__(self, *args, **kwargs):
        super(StripeRemovalTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = None
        sf = None

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_wf(self):
        images, control = th.generate_shared_array_and_copy()
        wf = ["level=1"]
        ti = None
        sf = None

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        th.assert_not_equals(result, control)

    def test_executed_wf_dict(self):
        images, control = th.generate_shared_array_and_copy()
        wf = {"level": 1}
        ti = None
        sf = None
        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_executed_ti(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = ['nblock=2']
        sf = None

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        th.assert_not_equals(result, control)

    def test_executed_ti_dict(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = {"nblock": 2}
        sf = None
        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_executed_sf(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = None
        sf = ['size=5']

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        th.assert_not_equals(result, control)

    def test_executed_sf_dict(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = None
        sf = {"size": 5}
        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_memory_executed_wf(self):
        images, control = th.generate_shared_array_and_copy()
        wf = ["level=1"]
        ti = None
        sf = None

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)

    def test_memory_executed_ti(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = ['nblock=2']
        sf = None

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)

    def test_memory_executed_sf(self):
        images, control = th.generate_shared_array_and_copy()
        wf = None
        ti = None
        sf = ['size=5']

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        value_filter_type = mock.Mock()
        value_filter_type.currentText = mock.Mock(return_value="type")
        execute_func = StripeRemovalFilter.execute_wrapper(value_filter_type)

        images = th.generate_shared_array()
        execute_func(images)

        self.assertEqual(value_filter_type.currentText.call_count, 1)


if __name__ == '__main__':
    unittest.main()
