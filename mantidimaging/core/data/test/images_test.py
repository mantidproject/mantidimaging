# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import io
import unittest

import numpy as np
from six import StringIO

from mantidimaging.core.data import Images
from mantidimaging.core.data.test.fake_logfile import generate_logfile
from mantidimaging.core.operations.crop_coords import CropCoordinatesFilter
from mantidimaging.core.operation_history import const
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.test_helpers.unit_test_helper import generate_images, assert_not_equals


class ImagesTest(unittest.TestCase):
    def test_parse_metadata_file(self):
        json_file = StringIO('{"a_int": 42, "a_string": "yes", "a_arr": ["one", "two", '
                             '"three"], "a_float": 3.65e-05, "a_bool": true}')

        imgs = Images(np.asarray([1]))
        imgs.load_metadata(json_file)

        def validate_prop(k, v):
            self.assertEqual(imgs.metadata[k], v)

        validate_prop('a_bool', True)
        validate_prop('a_string', 'yes')
        validate_prop('a_int', 42)
        validate_prop('a_arr', ['one', 'two', 'three'])

    def test_record_parameters_in_metadata(self):
        imgs = Images(np.asarray([1]))

        imgs.record_operation('test_func', 'A pretty name', this=765, that=495.0, roi=(1, 2, 3, 4))

        expected = {
            'operation_history': [{
                'name': 'test_func',
                'display_name': 'A pretty name',
                'kwargs': {
                    'this': 765,
                    'that': 495.0,
                    'roi': (1, 2, 3, 4)
                },
            }]
        }

        self.assertIn(const.TIMESTAMP, imgs.metadata[const.OPERATION_HISTORY][0])

        imgs.metadata[const.OPERATION_HISTORY][0].pop(const.TIMESTAMP)
        self.assertEqual(imgs.metadata, expected)

    def test_free_memory(self):
        images = generate_images(automatic_free=False)
        self.assertIsNotNone(images.memory_filename)
        self.assertIsNotNone(images.data)
        images.free_memory()
        self.assertIsNone(images.memory_filename)
        self.assertIsNone(images.data)

    def test_copy(self):
        images = generate_images(automatic_free=False)
        images.record_operation("Test", "Display", 123)
        self.assertFalse(images.is_sinograms)
        copy = images.copy()
        self.assertFalse(copy.is_sinograms)

        self.assertEqual(images, copy)

        copy.data[:] = 150

        self.assertEqual(images.metadata, copy.metadata)
        self.assertNotEqual(images.memory_filename, copy.memory_filename)
        self.assertNotEqual(images, copy)

    def test_copy_flip_axes(self):
        images = generate_images(automatic_free=False)
        images.record_operation("Test", "Display", 123)
        self.assertFalse(images.is_sinograms)
        copy = images.copy(flip_axes=True)
        self.assertTrue(copy.is_sinograms)

        self.assertEqual(images.sinograms, copy)

        copy.data[:] = 150

        self.assertEqual(images.metadata, copy.metadata)
        self.assertNotEqual(images.memory_filename, copy.memory_filename)
        self.assertNotEqual(images.sinograms, copy)

    def test_copy_roi(self):
        images = generate_images(automatic_free=False)
        images.record_operation("Test", "Display", 123)
        self.assertFalse(images.is_sinograms)
        cropped_copy = images.copy_roi(SensibleROI(0, 0, 5, 5))

        self.assertEqual(cropped_copy, images.data[:, 0:5, 0:5])

        self.assertEqual(len(cropped_copy.metadata[const.OPERATION_HISTORY]), 2)
        self.assertEqual(cropped_copy.metadata[const.OPERATION_HISTORY][-1][const.OPERATION_DISPLAY_NAME],
                         CropCoordinatesFilter.filter_name)

        # remove the extra crop operation
        cropped_copy.metadata[const.OPERATION_HISTORY].pop(-1)
        # the two metadatas show now be equal again
        self.assertEqual(images.metadata, cropped_copy.metadata)
        self.assertNotEqual(images.memory_filename, cropped_copy.memory_filename)
        self.assertNotEqual(images, cropped_copy)

    def test_filenames_set(self):
        images = generate_images()
        with self.assertRaises(AssertionError):
            images.filenames = ["filename"] * 5

    def test_filenames_get(self):
        images = generate_images()
        images.filenames = ["filename"] * images.num_projections
        self.assertIsNotNone(images.filenames)

    def test_load_metadata(self):
        meta = io.StringIO(f'{{"{const.SINOGRAMS}": true}}')
        images = generate_images()
        images.load_metadata(meta)
        self.assertTrue(images.is_sinograms)

    def test_save_metadata(self):
        images = generate_images()
        images._is_sinograms = True
        stream = io.StringIO()
        images.save_metadata(stream)
        self.assertEqual(stream.getvalue(), f'''{{
    "{const.SINOGRAMS}": true
}}''')

    def test_helper_properties(self):
        images = generate_images((42, 100, 350))
        self.assertEqual(images.height, 100)
        self.assertEqual(images.width, 350)
        self.assertEqual(images.v_middle, 50)
        self.assertEqual(images.h_middle, 350 / 2)
        self.assertEqual(images.num_images, 42)
        self.assertEqual(images.num_projections, 42)
        self.assertEqual(images.num_sinograms, 100)

    def test_data_accessors(self):
        images = generate_images((10, 100, 350))
        self.assertEqual(images.projection(0).shape, (100, 350))
        self.assertEqual(images.sino(0).shape, (10, 350))

        images._is_sinograms = True
        self.assertEqual(images.projection(0).shape, (10, 350))
        self.assertEqual(images.sino(0).shape, (100, 350))

    def test_proj180deg(self):
        images = generate_images((10, 100, 350))
        # expected without having a specific 180 deg projection
        self.assertIsNone(images._proj180deg)
        expected_projection = images.projection(images.num_projections // 2)

        # simulate a pre-loaded one
        np.array_equal(images.proj180deg.data, expected_projection)
        images._proj180deg = generate_images((1, 100, 350))
        assert_not_equals(images.proj180deg.data, expected_projection)

    def test_data_get(self):
        images = generate_images((10, 100, 350))
        self.assertIsNotNone(images.data)

    def test_create_empty_images(self):
        images = Images.create_empty_images((15, 10, 10), np.float32, {})
        self.assertEqual(images.data.shape, (15, 10, 10))

    def test_get_projection_angles_from_logfile(self):
        images = generate_images()
        images.log_file = generate_logfile()
        expected = np.deg2rad(np.asarray([0.0, 0.3152, 0.6304, 0.9456, 1.2608, 1.576, 1.8912, 2.2064, 2.5216, 2.8368]))
        actual: ProjectionAngles = images.projection_angles()
        self.assertEqual(len(actual.value), len(expected))
        np.testing.assert_equal(actual.value, expected)

    def test_get_projection_angles_no_logfile(self):
        images = generate_images()
        actual = images.projection_angles()
        self.assertEqual(10, len(actual.value))
