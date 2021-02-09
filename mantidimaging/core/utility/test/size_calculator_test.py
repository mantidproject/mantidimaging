# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np

import unittest

from mantidimaging.core.utility import size_calculator


class SizeCalculatorTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SizeCalculatorTest, self).__init__(*args, **kwargs)

    def test_full_size(self):
        shape = (40234079, 1, 13)
        axis = 0
        dtype = '32'

        res = size_calculator.full_size_MB(shape, axis, dtype)

        self.assertAlmostEqual(res, 1995.2508, 4)

    def test_single_size(self):
        self.assertEqual(size_calculator.single_size((14, 15, 16), 1), 224)

    def test_determine_dtype_size(self):
        self.assertEqual(size_calculator._determine_dtype_size('16'), 16)
        self.assertEqual(size_calculator._determine_dtype_size('32'), 32)
        self.assertEqual(size_calculator._determine_dtype_size('64'), 64)
        self.assertEqual(size_calculator._determine_dtype_size(), 1)

        self.assertEqual(size_calculator._determine_dtype_size(np.float16), 16)
        self.assertEqual(size_calculator._determine_dtype_size(np.float32), 32)
        self.assertEqual(size_calculator._determine_dtype_size(np.float64), 64)
