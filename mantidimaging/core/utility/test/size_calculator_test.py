# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np

import unittest

from mantidimaging.core.utility import size_calculator


class SizeCalculatorTest(unittest.TestCase):

    def test_full_size_mb(self):
        shape = (40234079, 1, 13)
        dtype = np.int32

        res = size_calculator.full_size_MB(shape, dtype)

        self.assertAlmostEqual(res, 1995.2508, 4)

    def test_full_size(self):
        self.assertEqual(size_calculator.full_size([1]), 1)
        self.assertEqual(size_calculator.full_size([2, 3]), 6)
        self.assertEqual(size_calculator.full_size([2, 3, 4]), 24)
        self.assertEqual(size_calculator.full_size([10, 10, 10, 10]), 10000)

    def test_determine_dtype_size(self):
        self.assertEqual(size_calculator._determine_dtype_size(np.float16), 2)
        self.assertEqual(size_calculator._determine_dtype_size(np.float32), 4)
        self.assertEqual(size_calculator._determine_dtype_size(np.float64), 8)

        self.assertRaises(ValueError, size_calculator._determine_dtype_size, "")
