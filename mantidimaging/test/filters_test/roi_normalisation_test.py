from __future__ import (absolute_import, division, print_function)

import unittest

import numpy as np
import numpy.testing as npt

from mantidimaging.tests import test_helper as th

from mantidimaging.core.filters import roi_normalisation


class ROINormalisationTest(unittest.TestCase):
    """
    Test contrast ROI normalisation filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(ROINormalisationTest, self).__init__(*args, **kwargs)

    def test_not_executed_empty_params(self):
        images, control = th.gen_img_shared_array_and_copy()

        air = None
        result = roi_normalisation.execute(images, air)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_invalid_shape(self):
        images, control = th.gen_img_shared_array_and_copy()

        images = np.arange(100).reshape(10, 10)
        air = [3, 3, 4, 4]
        npt.assert_raises(ValueError, roi_normalisation.execute, images,
                          air)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        th.switch_mp_off()
        self.do_execute()
        th.switch_mp_on()

    def do_execute(self):
        images, control = th.gen_img_shared_array_and_copy()

        air = [3, 3, 4, 4]
        result = roi_normalisation.execute(images, air)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()
