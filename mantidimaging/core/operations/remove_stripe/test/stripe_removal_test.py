# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.remove_stripe import StripeRemovalFilter


class StripeRemovalTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_stripe_removal(self, wf=None, ti=None, sf=None):
        images = th.generate_images()
        control = images.copy()

        result = StripeRemovalFilter.filter_func(images, wf, ti, sf)

        th.assert_not_equals(result.data, control.data)
        th.assert_not_equals(result.data, control.data)

    def test_executed_wf(self):
        wf = ["level=1"]
        self.do_stripe_removal(wf=wf)

    def test_executed_sf(self):
        sf = ['size=5']
        self.do_stripe_removal(sf=sf)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        value_filter_type = mock.Mock()
        value_filter_type.currentText = mock.Mock(return_value="fourier-wavelet")
        value_wf_level = mock.Mock()
        value_wf_level.value = mock.Mock(return_value=1)
        value_wf_wname = mock.Mock()
        value_wf_wname.currentText = mock.Mock(return_value="haar")
        value_wf_sigma = mock.Mock()
        value_wf_sigma.value = mock.Mock(return_value=2.0)
        execute_func = StripeRemovalFilter.execute_wrapper(value_filter_type, value_wf_level, value_wf_wname,
                                                           value_wf_sigma)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(value_filter_type.currentText.call_count, 1)


if __name__ == '__main__':
    unittest.main()
