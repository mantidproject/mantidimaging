from __future__ import absolute_import, division, print_function

import unittest

import numpy as np

from mantidimaging.core.algorithms import shape_splitter
from mantidimaging.tests import test_helper as th


class ShapeSplitterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ShapeSplitterTest, self).__init__(*args, **kwargs)

    def test_ratio_reconstruction_false(self):
        current_size = 2
        max_memory = 1

        self.assertEqual(shape_splitter._calculate_ratio(
            current_size, max_memory, reconstruction=False), 2)

    def test_ratio_reconstruction_true(self):
        current_size = 2
        max_memory = 1
        self.assertEqual(shape_splitter._calculate_ratio(
            current_size, max_memory, reconstruction=True), 4)

    def test_execute(self):
        shape = (1000, 1000, 1000)
        axis = 0
        dtype = '32'
        max_memory = 2000
        max_ratio = 1
        reconstruction = False

        res_split, res_step = shape_splitter.execute(
            shape, axis, dtype, max_memory, max_ratio, reconstruction)

        # convert to numpy arrays to use the numpy.testing equals
        th.assert_equals(np.array(res_split), np.array([0, 500, 1000]))
        self.assertEqual(res_step, 500)
