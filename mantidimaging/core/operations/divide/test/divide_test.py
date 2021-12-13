# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock
import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.operations.divide import DivideFilter


class DivideTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_divide_with_zero_does_nothing(self):
        images = th.generate_images()
        copy = np.copy(images.data)

        result = self.do_divide(images, 0.00)

        npt.assert_equal(result.data, copy)

    def test_divide(self):
        images = th.generate_images()
        copy = np.copy(images.data)

        result = self.do_divide(images, 0.005)

        th.assert_not_equals(result.data, copy)

    def do_divide(self, images: Images, value: float) -> Images:
        return DivideFilter.filter_func(images, value)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        value_widget = mock.Mock()
        value_widget.value.return_value = 10
        unit_widget = mock.Mock()
        unit_widget.currentText.return_value = "cm"

        execute_func = DivideFilter.execute_wrapper(value_widget, unit_widget)

        images = th.generate_images()
        execute_func(images)


if __name__ == '__main__':
    unittest.main()
