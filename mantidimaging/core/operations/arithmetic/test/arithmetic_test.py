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

        result = ArithmeticFilter().filter_func(images.copy(), div_val = 2.0)

        npt.assert_array_equal(images.data * 0.5, result.data)