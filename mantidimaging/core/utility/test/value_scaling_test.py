import unittest

import numpy as np
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
        images, control = th.gen_img_shared_array_and_copy()
        for z in range(images.shape[0]):
            for y in range(images.shape[1]):
                images[z, y] = y * 10

                # expected output will be a multiple of 60, after applying the
                # factors
                control[z, y] = y * 60

        our_factors = np.array([6., 6., 6., 6., 6., 6., 6., 6., 6., 6.])
        result = self.alg.apply_factor(images, our_factors, 1)
        npt.assert_equal(result, control)
        npt.assert_equal(images, control)
        npt.assert_equal(images, result)

    def test_apply_factors_array(self):
        images, control = th.gen_img_shared_array_and_copy()
        for z in range(images.shape[0]):
            for y in range(images.shape[1]):
                images[z, y] = y * 10
                control[z, y] = y * 10 * z

        our_factors = np.arange(0, images.shape[0])
        result = self.alg.apply_factors(images, our_factors)
        npt.assert_equal(result, control)
        npt.assert_equal(images, control)
        npt.assert_equal(images, result)

    def test_apply_factors_array_2(self):
        images = th.gen_img_shared_array()
        images.fill(1)
        our_factors = np.array([1.0, 1.1, 1.5, 1.2, 1.1, 1.05, 1.11, 1.12, 1.09, 1.0])
        result = self.alg.apply_factors(images, our_factors)
        npt.assert_equal(images, result)
        for i in range(images.shape[0]):
            npt.assert_almost_equal(images[i].sum(), images[i].size * our_factors[i], decimal=5)


if __name__ == '__main__':
    unittest.main()
