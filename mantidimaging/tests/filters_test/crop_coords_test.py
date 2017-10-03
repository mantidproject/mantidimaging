from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

from mantidimaging import helper as h
from mantidimaging.tests import test_helper as th

from mantidimaging.core.filters import crop_coords


class CropCoordsTest(unittest.TestCase):
    """
    Test crop by coordinates filter.

    Tests return value only.
    """

    def __init__(self, *args, **kwargs):
        super(CropCoordsTest, self).__init__(*args, **kwargs)

    def test_executed_with_flat_and_dark(self):
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.shared_deepcopy(images)[0]
        dark = th.shared_deepcopy(images)[0]
        roi = [1, 1, 5, 5]

        r_sample, r_flat, r_dark = crop_coords.execute(images, roi, flat, dark)

        expected_shape_sample = (10, 4, 4)
        expected_shape_flat_dark = (4, 4)

        npt.assert_equal(r_sample.shape, expected_shape_sample)
        npt.assert_equal(r_flat.shape, expected_shape_flat_dark)
        npt.assert_equal(r_dark.shape, expected_shape_flat_dark)

        # TODO: in-place data test
        # npt.assert_equal(images.shape, expected_shape_sample)

    def test_executed_with_only_flat_and_no_dark(self):
        """
        The filter will execute but BOTH flat and dark will be None!
        """
        images, control = th.gen_img_shared_array_and_copy()
        flat = th.shared_deepcopy(images)[0]
        dark = None
        roi = [1, 1, 5, 5]

        r_sample, r_flat, r_dark = crop_coords.execute(images, roi, flat, dark)

        expected_shape_sample = (10, 4, 4)

        npt.assert_equal(r_sample.shape, expected_shape_sample)
        npt.assert_equal(r_flat, None)
        npt.assert_equal(r_dark, None)

        # TODO: in-place data test
        # npt.assert_equal(images.shape, expected_shape_sample)

    def test_executed_with_no_flat_and_only_dark(self):
        """
        The filter will execute but BOTH flat and dark will be None!
        """
        images, control = th.gen_img_shared_array_and_copy()
        flat = None
        dark = th.shared_deepcopy(images)[0]
        roi = [1, 1, 5, 5]

        r_sample, r_flat, r_dark = crop_coords.execute(images, roi, flat, dark)

        expected_shape_sample = (10, 4, 4)

        npt.assert_equal(r_sample.shape, expected_shape_sample)
        npt.assert_equal(r_flat, None)
        npt.assert_equal(r_dark, None)

        # TODO: in-place data test
        # npt.assert_equal(images.shape, expected_shape_sample)

    def test_executed_only_volume(self):
        # Check that the filter is  executed when:
        #   - valid Region of Interest is provided
        #   - no flat or dark images are provided

        images, control = th.gen_img_shared_array_and_copy()
        roi = [1, 1, 5, 5]
        result = crop_coords.execute(images, roi)[0]
        expected_shape = (10, 4, 4)

        npt.assert_equal(result.shape, expected_shape)

        # TODO: in-place data test
        # npt.assert_equal(images.shape, expected_shape)

    def test_not_executed_no_sample(self):
        # images that will be put through testing
        images, control = th.gen_img_shared_array_and_copy()

        # not executed because no Sample is provided
        roi = [1, 2, 5, 1]
        npt.assert_raises(ValueError, crop_coords.execute, None, roi)

    def test_not_executed_no_roi(self):
        # images that will be put through testing
        images, control = th.gen_img_shared_array_and_copy()

        # not executed because no Region of interest is provided
        roi = None

        result = crop_coords.execute(images, roi)[0]

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_memory_change_acceptable(self):
        """
        Expected behaviour for the filter is to be done in place
        without using more memory.

        In reality the memory is increased by about 40MB (4 April 2017),
        but this could change in the future.

        The reason why a 10% window is given on the expected size is
        to account for any library imports that may happen.

        This will still capture if the data is doubled, which is the main goal.
        """
        images, control = th.gen_img_shared_array_and_copy()
        roi = [1, 1, 5, 5]

        cached_memory = h.get_memory_usage_linux(mb=True)[0]

        result = crop_coords.execute(images, roi)[0]

        self.assertLess(
            h.get_memory_usage_linux(mb=True)[0], cached_memory * 1.1)

        expected_shape = (10, 4, 4)

        npt.assert_equal(result.shape, expected_shape)

        # TODO: in-place data test
        # npt.assert_equal(images.shape, expected_shape)


if __name__ == '__main__':
    unittest.main()
