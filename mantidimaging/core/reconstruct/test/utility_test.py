from unittest import TestCase

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct import utility


TEST_PARAMS_1 = {
    "operation_history": [
        {
            "args": [],
            "kwargs": {
                "region_of_interest": [
                    61,
                    31,
                    2025,
                    1730
                ]
            },
            "name":
            "mantidimaging.core.filters.crop_coords.crop_coords.execute_single"
        },
        {
            "args": [],
            "kwargs": {
                "threshold": 0.75
            },
            "name": "mantidimaging.core.filters.cut_off.cut_off.execute"
        },
        {
            "args": [],
            "kwargs": {
                "region_of_interest": [
                    760,
                    316,
                    1939,
                    1687
                ]
            },
            "name":
            "mantidimaging.core.filters.crop_coords.crop_coords.execute_single"
        }
    ],
    "auto_cor_tilt": {
        "fitted_gradient": -0.012,
        "rotation_centre": 1427.6,
        "rotation_centres": [
            1428,
            1425,
            1427,
            1426,
            1424,
            1423,
            1422,
            1421,
            1422,
            1420,
            1419,
            1418,
            1416
        ],
        "slice_indices": [
            1,
            71,
            141,
            211,
            281,
            351,
            421,
            491,
            561,
            631,
            701,
            771,
            841
        ],
        "tilt_angle_rad": -0.01238
    }
}


TEST_PARAMS_2 = {
    "operation_history": [
        {
            "args": [],
            "kwargs": {
                "region_of_interest": [
                    61,
                    31,
                    2025,
                    1730
                ]
            },
            "name":
            "mantidimaging.core.filters.crop_coords.crop_coords.execute_single"
        }
    ]
}


class UtilityTest(TestCase):

    def test_get_roi_left_shift_multiple(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        roi_offset = utility.get_roi_left_shift(imgs)
        self.assertEquals(roi_offset, 821)

    def test_get_roi_left_shift_single(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_2
        roi_offset = utility.get_roi_left_shift(imgs)
        self.assertEquals(roi_offset, 61)

    def test_get_roi_left_shift_no_hist(self):
        imgs = Images()
        imgs.properties = {"operation_history": []}
        roi_offset = utility.get_roi_left_shift(imgs)
        self.assertEquals(roi_offset, 0)

    def test_get_roi_left_shift_empty(self):
        imgs = Images()
        roi_offset = utility.get_roi_left_shift(imgs)
        self.assertEquals(roi_offset, 0)

    def test_get_cor_tilt_from_images(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        cor, tilt, m = utility.get_cor_tilt_from_images(imgs)
        self.assertEquals(cor, 1427.6 - 821)
        self.assertAlmostEqual(tilt, -0.01238)
        self.assertAlmostEqual(m, -0.012)

    def test_get_cor_tilt_from_images_empty(self):
        imgs = Images()
        cor, tilt, m = utility.get_cor_tilt_from_images(imgs)
        self.assertEquals(cor, 0)
        self.assertEquals(tilt, 0.0)
        self.assertEquals(m, 0.0)

    def test_get_cor_tilt_from_images_none(self):
        cor, tilt, m = utility.get_cor_tilt_from_images(None)
        self.assertEquals(cor, 0)
        self.assertEquals(tilt, 0.0)
        self.assertEquals(m, 0.0)
