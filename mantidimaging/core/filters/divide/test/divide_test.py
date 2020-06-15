import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.filters.divide import DivideFilter


class DivideTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DivideTest, self).__init__(*args, **kwargs)

    def test_divide_with_zero_does_nothing(self):
        images = th.generate_images()
        copy = np.copy(images.sample)

        result = self.do_divide(images, 0.00)

        npt.assert_equal(result.sample, copy)

    def test_divide(self):
        images = th.generate_images()
        copy = np.copy(images.sample)

        result = self.do_divide(images, 0.005)

        th.assert_not_equals(result.sample, copy)

    def do_divide(self, images: Images, value: float) -> Images:
        return DivideFilter.filter_func(images, value)


if __name__ == '__main__':
    unittest.main()
