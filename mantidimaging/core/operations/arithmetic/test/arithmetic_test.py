import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.arithmetic import ArithmeticFilter


class ArithmeticTest(unittest.TestCase):
    """
    Test arithmetic filter.
    """
    def __init__(self, *args, **kwargs):
        super(ArithmeticTest, self).__init__(*args, **kwargs)

    def test_execute_div_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), div_val=2.0)

        npt.assert_array_equal(images.data * 0.5, result.data)

    def test_execute_mult_only(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), mult_val=2.0)

        npt.assert_array_equal(images.data * 2.0, result.data)

    def test_cant_divide_or_multiply_by_zero(self):
        images = th.generate_images()

        result = ArithmeticFilter().filter_func(images.copy(), mult_val=0.0)
        npt.assert_array_equal(images.data, result.data)

        result = ArithmeticFilter().filter_func(images.copy(), div_val=0.0)
        npt.assert_array_equal(images.data, result.data)