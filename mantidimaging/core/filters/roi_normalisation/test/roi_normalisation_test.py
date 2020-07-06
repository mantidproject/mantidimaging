import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.roi_normalisation import RoiNormalisationFilter


class ROINormalisationTest(unittest.TestCase):
    """
    Test contrast ROI normalisation filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(ROINormalisationTest, self).__init__(*args, **kwargs)

    def test_not_executed_empty_params(self):
        images = th.generate_images()

        air = None

        original = np.copy(images.data[0])
        result = RoiNormalisationFilter.filter_func(images, air)
        npt.assert_equal(result.data[0], original)

    def test_not_executed_invalid_shape(self):
        images = np.arange(100).reshape(10, 10)
        air = [3, 3, 4, 4]
        npt.assert_raises(ValueError, RoiNormalisationFilter.filter_func, images, air)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        th.switch_mp_off()
        self.do_execute()
        th.switch_mp_on()

    def do_execute(self):
        images = th.generate_images()

        original = np.copy(images.data[0])
        air = [3, 3, 4, 4]
        result = RoiNormalisationFilter.filter_func(images, air)

        th.assert_not_equals(result.data[0], original)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images()
        RoiNormalisationFilter.execute_wrapper()(images)


if __name__ == '__main__':
    unittest.main()
