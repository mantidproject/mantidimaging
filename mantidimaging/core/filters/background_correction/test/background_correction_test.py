import unittest
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th

from mantidimaging.core.filters.background_correction import BackgroundCorrectionFilter


class BackgroundCorrectionTest(unittest.TestCase):
    """
    Test background correction filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(BackgroundCorrectionTest, self).__init__(*args, **kwargs)

    def test_not__filter_funcd_empty_params(self):
        images, control = th.gen_img_shared_array_and_copy()

        # empty params
        result = BackgroundCorrectionFilter._filter_func(images)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not__filter_funcd_no_dark(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]

        # no dark
        result = BackgroundCorrectionFilter._filter_func(images, flat[0])

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not__filter_funcd_no_flat(self):
        images, control = th.gen_img_shared_array_and_copy()
        dark = th.gen_img_shared_array()[0]

        # no flat
        result = BackgroundCorrectionFilter._filter_func(images, None, dark[0])

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not__filter_funcd_bad_flat(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]
        dark = th.gen_img_shared_array()[0]

        # bad flat
        npt.assert_raises(ValueError, BackgroundCorrectionFilter._filter_func, images,
                          flat[0], dark)

    def test_not__filter_funcd_bad_dark(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.gen_img_shared_array()[0]
        dark = th.gen_img_shared_array()[0]

        # bad dark
        npt.assert_raises(ValueError, BackgroundCorrectionFilter._filter_func, images,
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
        result = BackgroundCorrectionFilter._filter_func(sample, flat, dark, clip_max=20)

        npt.assert_almost_equal(result, expected, 7)
        npt.assert_almost_equal(sample, expected, 7)

        npt.assert_equal(result, sample)

    def test_clip_max_works(self):
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

        # the resulting values from the calculation are above 3,
        # but clip_max should make them all equal to 3
        result = BackgroundCorrectionFilter._filter_func(sample, flat, dark, clip_max=3)

        npt.assert_equal(result, expected)
        npt.assert_equal(sample, expected)

        npt.assert_equal(result, sample)

    def test_clip_min_works(self):
        sample = th.gen_img_shared_array()
        sample[:] = 846.
        flat = th.gen_img_shared_array()[0]
        flat[:] = 42.
        dark = th.gen_img_shared_array()[0]
        dark[:] = 6.
        expected = np.full(sample.shape, 300.)

        # the resulting values from above are below 300,
        # but clip min should make all values below 300, equal to 300
        result = BackgroundCorrectionFilter._filter_func(sample, flat, dark, clip_min=300)

        npt.assert_equal(result, expected)
        npt.assert_equal(sample, expected)

        npt.assert_equal(result, sample)

    @mock.patch(f'{BackgroundCorrectionFilter.__module__ + ".get_average_image"}', mock.MagicMock(return_value=None))
    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        execute_func = BackgroundCorrectionFilter.execute_wrapper(flat_path_widget=None, dark_path_widget=None)
        images, _ = th.gen_img_shared_array_and_copy()
        execute_func(images)


if __name__ == '__main__':
    unittest.main()
