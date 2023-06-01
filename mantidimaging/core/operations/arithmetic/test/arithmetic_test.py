# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.arithmetic import ArithmeticFilter


class ArithmeticTest(unittest.TestCase):
    """
    Test arithmetic filter.
    """

    def test_div_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), div_val=2.0)

        npt.assert_array_equal(images.data * 0.5, result.data)

    def test_mult_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), mult_val=2.0)

        npt.assert_array_equal(images.data * 2.0, result.data)

    def test_cant_multiply_by_zero(self):
        images = th.generate_images()

        self.assertRaises(ValueError, ArithmeticFilter.filter_func, images, mult_val=0.0)

    def test_cant_divide_by_zero(self):
        images = th.generate_images()

        self.assertRaises(ValueError, ArithmeticFilter.filter_func, images, div_val=0.0)

    def test_add_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), add_val=2.0)

        npt.assert_array_equal(images.data + 2.0, result.data)

    def test_subtract_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), sub_val=2.0)

        npt.assert_array_equal(images.data - 2.0, result.data)
