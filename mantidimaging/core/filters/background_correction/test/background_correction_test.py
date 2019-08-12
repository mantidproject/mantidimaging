import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th

from mantidimaging.core.filters import background_correction


class BackgroundCorrectionTest(unittest.TestCase):
    """
    Test background correction filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(BackgroundCorrectionTest, self).__init__(*args, **kwargs)

    def test_not_executed_empty_params(self):
        images, control = th.gen_img_shared_array_and_copy()

        # empty params
        result = background_correction.execute(images)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_no_dark(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]

        # no dark
        result = background_correction.execute(images, flat[0])

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_no_flat(self):
        images, control = th.gen_img_shared_array_and_copy()
        dark = th.gen_img_shared_array()[0]

        # no flat
        result = background_correction.execute(images, None, dark[0])

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_bad_flat(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]
        dark = th.gen_img_shared_array()[0]

        # bad flat
        npt.assert_raises(ValueError, background_correction.execute, images,
                          flat[0], dark)

    def test_not_executed_bad_dark(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]
        dark = th.gen_img_shared_array()[0]

        # bad dark
        npt.assert_raises(ValueError, background_correction.execute, images,
                          flat, dark[0])

    def test_real_result(self):
        th.switch_mp_off()
        self.do_real_result()
        th.switch_mp_on()

    def do_real_result(self):
        # the calculation here was designed on purpose to have a value
        # below the np.clip in background_correction
        # the operation is (sample - dark) / (flat - dark)
        sample = th.gen_img_shared_array_with_val(26.)
        flat = th.gen_img_shared_array_with_val(
            7., shape=(1, sample.shape[1], sample.shape[2]))[0]
        dark = th.gen_img_shared_array_with_val(
            6., shape=(1, sample.shape[1], sample.shape[2]))[0]

        expected = np.full(sample.shape, 20.)

        # we dont want anything to be cropped out
        result = background_correction.execute(sample, flat, dark, clip_max=20)

        npt.assert_almost_equal(result, expected, 7)
        npt.assert_almost_equal(sample, expected, 7)

        npt.assert_equal(result, sample)

    def test_clip_works(self):
        # the calculation here was designed on purpose to have a value
        # ABOVE the np.clip in background_correction
        # the operation is (sample - dark) / (flat - dark)
        sample = th.gen_img_shared_array()
        sample[:] = 846.
        flat = th.gen_img_shared_array()[0]
        flat[:] = 42.
        dark = th.gen_img_shared_array()[0]
        dark[:] = 6.
        expected = np.full(sample.shape, 3.)

        # we dont want anything to be cropped out
        result = background_correction.execute(sample, flat, dark)

        npt.assert_equal(result, expected)
        npt.assert_equal(sample, expected)

        npt.assert_equal(result, sample)


if __name__ == '__main__':
    unittest.main()
