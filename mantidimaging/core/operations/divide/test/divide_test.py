# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from unittest import mock
import numpy as np
from typing import TYPE_CHECKING

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.divide import DivideFilter

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class DivideTest(unittest.TestCase):

    @parameterized.expand([("None", None), ("0", 0.00)])
    def test_divide_with_invalid_value_raises_exception(self, _, value):
        images = th.generate_images()

        self.assertRaises(ValueError, self.do_divide, images, value)

    def test_divide(self):
        images = th.generate_images()
        copy = np.copy(images.data)

        result = self.do_divide(images, 0.005)

        th.assert_not_equals(result.data, copy)

    def do_divide(self, images: ImageStack, value: float) -> ImageStack:
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
