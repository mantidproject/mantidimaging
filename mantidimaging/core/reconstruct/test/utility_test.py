from unittest import TestCase

from mantidimaging.core.data import Images, const
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
    ]
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


TEST_PARAMS_3 = {
    'operation_history': [
        {
            'args': [],
            'kwargs': {'threshold': 0.22},
            'name': 'mantidimaging.core.filters.cut_off.cut_off.execute'
        },
        {
            'args': [],
            'kwargs': {
                'region_of_interest': [
                    72,
                    697,
                    2038,
                    1578
                ]
            },
            'name': 'mantidimaging.core.filters.crop_coords.crop_coords.execute_single'
        },
        {
            'args': [],
            'kwargs': {
                'region_of_interest': [
                    705,
                    22,
                    1944,
                    845
                ]
            },
            'name': 'mantidimaging.core.filters.crop_coords.crop_coords.execute_single'
        },
        {
            'args': [],
            'kwargs': {
                'fitted_gradient': 0.009657997234305727,
                'rotation_centre': 617.2297924368454,
                'rotation_centres': [
                    619.0,
                    620.171875,
                    624.078125
                ],
                'slice_indices': [
                    143,
                    376,
                    678
                ],
                'tilt_angle_rad': 0.009657696961729184
            },
            'name': 'cor_tilt_finding'
        },
        {
            'args': [],
            'kwargs': {
                'region_of_interest': [
                    14,
                    0,
                    1191,
                    249
                ]
            },
            'name': 'mantidimaging.core.filters.crop_coords.crop_coords.execute_single'
        }
    ]
}


TEST_PARAMS_4 = {
    'operation_history': [
        {
            'args': [],
            'kwargs': {
                'fitted_gradient': 1,
                'rotation_centre': 50,
                'tilt_angle_rad': 0
            },
            'name': 'cor_tilt_finding'
        },
        {
            'args': [],
            'kwargs': {
                'region_of_interest': [
                    0,
                    20,
                    100,
                    100
                ]
            },
            'name': 'mantidimaging.core.filters.crop_coords.crop_coords.execute_single'
        }
    ]
}


class UtilityTest(TestCase):

    def test_get_crop_multiple(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        roi_offset = utility.get_crop(imgs, 0)
        self.assertEquals(roi_offset, 821)

    def test_get_crop_multiple_select_1(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        roi_offset = utility.get_crop(imgs, 0, end=2)
        self.assertEquals(roi_offset, 61)

    def test_get_crop_multiple_select_2(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        roi_offset = utility.get_crop(imgs, 0, start=2, end=3)
        self.assertEquals(roi_offset, 760)

    def test_get_crop_multiple_select_2_top(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_1
        roi_offset = utility.get_crop(imgs, 1, start=2, end=3)
        self.assertEquals(roi_offset, 316)

    def test_get_crop_single(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_2
        roi_offset = utility.get_crop(imgs, 0)
        self.assertEquals(roi_offset, 61)

    def test_get_crop_no_hist(self):
        imgs = Images()
        imgs.properties = {"operation_history": []}
        roi_offset = utility.get_crop(imgs, 0)
        self.assertEquals(roi_offset, 0)

    def test_get_crop_empty(self):
        imgs = Images()
        roi_offset = utility.get_crop(imgs, 0)
        self.assertEquals(roi_offset, 0)

    def test_get_last_cor_tilt_find(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_3
        finding, idx = utility.get_last_cor_tilt_find(imgs)

        self.assertIsNotNone(finding)
        self.assertEquals(idx, 3)

        self.assertEquals(
            finding,
            imgs.properties[const.OPERATION_HISTORY][idx]['kwargs']
        )

    def test_get_last_cor_tilt_find_empty(self):
        imgs = Images()
        last_find, last_find_idx = utility.get_last_cor_tilt_find(imgs)
        self.assertIsNone(last_find)
        self.assertIsNone(last_find_idx)

    def test_get_cor_tilt_from_images(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_3
        cor, tilt, m = utility.get_cor_tilt_from_images(imgs)

        self.assertAlmostEqual(cor, 603.2297924368454)
        self.assertAlmostEqual(tilt, 0.009657696961729184)
        self.assertAlmostEqual(m, 0.009657997234305727)

    def test_get_cor_tilt_from_images_subsequent_top_crop(self):
        imgs = Images()
        imgs.properties = TEST_PARAMS_4
        cor, tilt, m = utility.get_cor_tilt_from_images(imgs)

        self.assertAlmostEqual(cor, 70)
        self.assertAlmostEqual(tilt, 0)
        self.assertAlmostEqual(m, 1)

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
