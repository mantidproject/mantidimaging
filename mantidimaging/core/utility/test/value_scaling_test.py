import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.utility import value_scaling


class ValueScalingTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ValueScalingTest, self).__init__(*args, **kwargs)

        self.alg = value_scaling

    def test_create_factors_no_roi(self):
        images = th.gen_img_shared_array()
        expected_factors = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]

        # make then with increasing values
        for z in range(images.shape[0]):
            for y in range(images.shape[1]):
                images[z, y] = y

        # roi = [4, 4, 8, 8]
        result = self.alg.create_factors(images, cores=1)
        # unittest assert for len which is ints
        self.assertEqual(len(result), images.shape[0])
        # numpy assert for arrays
        npt.assert_equal(expected_factors, result)

    def test_create_factors(self):
        images = th.gen_img_shared_array()
        expected_factors = [5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5]
        # make then with increasing values
        for z in range(images.shape[0]):
            for y in range(images.shape[1]):
                images[z, y] = y

        roi = [4, 4, 8, 8]
        result = self.alg.create_factors(images, roi, cores=1)
        # unittest assert for len which is ints
        self.assertEqual(len(result), images.shape[0])
        # numpy assert for arrays
        npt.assert_equal(expected_factors, result)

    def test_apply_factors(self):
        images = th.gen_img_shared_array()
        images[:] = 2
        roi = [4, 4, 8, 8]
        result = self.alg.create_factors(images, roi, cores=1)
        result = self.alg.apply_factor(images, result, 1)
        npt.assert_equal(images, result)


if __name__ == '__main__':
    unittest.main()
