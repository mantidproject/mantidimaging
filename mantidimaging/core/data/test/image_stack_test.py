# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import io
from pathlib import Path
from unittest import mock

from mantidimaging.core.io.instrument_log import InstrumentLog
from mantidimaging.core.utility.data_containers import ProjectionAngles
import unittest

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.test.fake_logfile import generate_csv_logfile, generate_txt_logfile
from mantidimaging.core.operations.crop_coords import CropCoordinatesFilter
from mantidimaging.core.operation_history import const
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.test_helpers.unit_test_helper import generate_images


class ImageStackTest(unittest.TestCase):

    def test_parse_metadata_file(self):
        json_file = io.StringIO('{"a_int": 42, "a_string": "yes", "a_arr": ["one", "two", '
                                '"three"], "a_float": 3.65e-05, "a_bool": true}')

        imgs = ImageStack(np.asarray([1]))
        imgs.load_metadata(json_file)

        def validate_prop(k, v):
            self.assertEqual(imgs.metadata[k], v)

        validate_prop('a_bool', True)
        validate_prop('a_string', 'yes')
        validate_prop('a_int', 42)
        validate_prop('a_arr', ['one', 'two', 'three'])

    def test_record_parameters_in_metadata(self):
        imgs = ImageStack(np.asarray([1]))

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

    def test_loading_metadata_preserves_existing(self):
        json_file = io.StringIO('{"a": 30.0, "b": 2}')

        imgs = ImageStack(np.asarray([1]), metadata={'b': 1, 'c': 5})
        self.assertEqual({'b': 1, 'c': 5}, imgs.metadata)

        imgs.load_metadata(json_file)
        self.assertEqual(30.0, imgs.metadata['a'])
        self.assertEqual(1, imgs.metadata['b'])
        self.assertEqual(5, imgs.metadata['c'])

    def test_loading_metadata_preserves_existing_log(self):
        json_file = io.StringIO('{"pixel_size": 30.0, "log_file": "/old/logfile"}')
        mock_log_path = Path("/aaa/bbb")
        mock_log_file = mock.create_autospec(InstrumentLog, source_file=mock_log_path)

        imgs = ImageStack(np.asarray([1]))
        self.assertEqual({}, imgs.metadata)

        imgs.log_file = mock_log_file
        self.assertEqual(str(mock_log_path), imgs.metadata['log_file'])

        imgs.load_metadata(json_file)
        self.assertEqual(30.0, imgs.metadata['pixel_size'])
        self.assertEqual(str(mock_log_path), imgs.metadata['log_file'])

    def test_copy(self):
        images = generate_images()
        images.record_operation("Test", "Display", 123)
        self.assertFalse(images.is_sinograms)
        copy = images.copy()
        self.assertFalse(copy.is_sinograms)

        self.assertEqual(images, copy)

        copy.data[:] = 150

        self.assertEqual(images.metadata, copy.metadata)
        self.assertNotEqual(images, copy)

    def test_copy_flip_axes(self):
        images = generate_images()
        images.record_operation("Test", "Display", 123)
        self.assertFalse(images.is_sinograms)
        copy = images.copy(flip_axes=True)
        self.assertTrue(copy.is_sinograms)

        self.assertEqual(copy, images.sinograms)

        copy.data[:] = 150

        self.assertEqual(images.metadata, copy.metadata)
        self.assertNotEqual(copy, images.sinograms)

    def test_copy_roi(self):
        images = generate_images()
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

    def test_clear_proj180deg(self):
        images = generate_images((10, 100, 350))
        # expected without having a specific 180 deg projection
        self.assertIsNone(images._proj180deg)
        images._proj180deg = generate_images((1, 100, 350))
        images.clear_proj180deg()
        self.assertIsNone(images._proj180deg)

    def test_data_get(self):
        images = generate_images((10, 100, 350))
        self.assertIsNotNone(images.data)

    def test_create_empty_image_stack(self):
        images = ImageStack.create_empty_image_stack((15, 10, 10), np.float32, {})
        self.assertEqual(images.data.shape, (15, 10, 10))

    def test_get_projection_angles_from_logfile(self):
        images = generate_images()
        images.log_file = generate_txt_logfile()
        expected = np.deg2rad(np.asarray([0.0, 0.3152, 0.6304, 0.9456, 1.2608, 1.576, 1.8912, 2.2064, 2.5216, 2.8368]))
        actual = images.projection_angles(360.0)
        self.assertEqual(len(actual.value), len(expected))
        np.testing.assert_equal(actual.value, expected)

    def test_get_projection_angles_from_logfile_csv(self):
        images = generate_images()
        images.log_file = generate_csv_logfile()
        expected = np.deg2rad(np.asarray([0.0, 0.3152, 0.6304, 0.9456, 1.2608, 1.576, 1.8912, 2.2064, 2.5216, 2.8368]))
        actual = images.projection_angles(360.0)
        self.assertEqual(len(actual.value), len(expected))
        np.testing.assert_equal(actual.value, expected)

    def test_get_projection_angles_no_logfile(self):
        images = generate_images()
        actual = images.projection_angles(360.0)
        self.assertEqual(10, len(actual.value))
        self.assertAlmostEqual(np.deg2rad(360), actual.value[-1], places=4)

        actual = images.projection_angles(275.69)
        self.assertEqual(10, len(actual.value))
        self.assertAlmostEqual(np.deg2rad(275.69), actual.value[-1], places=4)

    def test_metadata_gets_updated_with_logfile(self):
        images = generate_images()
        images.log_file = generate_txt_logfile()
        self.assertEqual(str(images.log_file.source_file), images.metadata[const.LOG_FILE])

    def test_set_projection_angles(self):
        images = generate_images()
        pangles = ProjectionAngles(list(range(0, 10)))
        images.set_projection_angles(pangles)

        actual = images.projection_angles()
        self.assertEqual(10, len(actual.value))
        self.assertAlmostEqual(images.projection_angles().value, pangles.value, places=4)

    def test_image_eq_method(self):
        data_array = np.arange(64, dtype=float).reshape([4, 4, 4])
        data_images = ImageStack(data_array.copy())
        data_images2 = ImageStack(data_array.copy())

        self.assertEqual(data_images, data_array)
        self.assertEqual(data_images, data_images2)

        data_array[1, 1, 1] *= 2
        self.assertNotEqual(data_images, data_array)

        self.assertRaises(ValueError, lambda a, b: a == b, data_images, 1.0)

    def test_cant_change_id(self):
        with self.assertRaisesRegex(Exception, "can't set attribute"):
            generate_images().id = "id"

    def test_default_name(self):
        imgs = ImageStack(np.asarray([1]))
        self.assertEqual(imgs.name, "untitled")

    def test_name_from_filenames(self):
        filenames = ["/path/tomo_0000.tiff", "/path/tomo_0001.tiff"]
        imgs = ImageStack(np.asarray([1]), filenames=filenames)
        self.assertEqual(imgs.name, "tomo_0000")

    def test_name_from_argument(self):
        filenames = ["/path/tomo_0000.tiff", "/path/tomo_0001.tiff"]
        imgs = ImageStack(np.asarray([1]), filenames=filenames, name="given")
        self.assertEqual(imgs.name, "given")

    def test_name_unique_new(self):
        existing = []
        imgs = ImageStack(np.asarray([1]), name="tomo")
        imgs.make_name_unique(existing)
        self.assertEqual(imgs.name, "tomo")

    def test_name_unique_exists(self):
        existing = ["tomo"]
        imgs = ImageStack(np.asarray([1]), name="tomo")
        imgs.make_name_unique(existing)
        self.assertEqual(imgs.name, "tomo_2")

    def test_slice_as_stack(self):
        raw_pixels = np.arange(60, dtype=np.float32).reshape((3, 4, 5))
        image = ImageStack(raw_pixels.copy(), name="tomo", sinograms=False)

        np.testing.assert_array_equal(raw_pixels[[0], :, :], image.slice_as_image_stack(0).data)
        np.testing.assert_array_equal(raw_pixels[[2], :, :], image.slice_as_image_stack(2).data)
        self.assertRaises(IndexError, image.slice_as_image_stack, 3)

        slice = image.slice_as_image_stack(0)
        self.assertEqual(slice.height, image.height)
        self.assertEqual(slice.width, image.width)
        self.assertEqual(slice.num_projections, 1)

        # check that modification do not affect original
        copy = image.slice_as_image_stack(0)
        copy.data += 1
        np.testing.assert_array_equal(raw_pixels, image.data)

        image = ImageStack(raw_pixels.copy(), name="tomo", sinograms=True)
        slice = image.slice_as_image_stack(0)
        self.assertEqual(slice.height, 1)
        self.assertEqual(slice.width, image.width)
        self.assertEqual(slice.num_projections, image.num_projections)
        np.testing.assert_array_equal(raw_pixels[[0], :, :], slice.data)

    def test_sino_as_stack(self):
        raw_pixels = np.arange(60, dtype=np.float32).reshape((3, 4, 5))
        image = ImageStack(raw_pixels.copy(), name="tomo", sinograms=False)

        np.testing.assert_array_equal(raw_pixels[:, [0], :], image.sino_as_image_stack(0).data)
        np.testing.assert_array_equal(raw_pixels[:, [3], :], image.sino_as_image_stack(3).data)
        self.assertRaises(IndexError, image.sino_as_image_stack, 4)

        slice = image.sino_as_image_stack(0)
        self.assertEqual(slice.height, 1)
        self.assertEqual(slice.width, image.width)
        self.assertEqual(slice.num_projections, image.num_projections)

        # check that modification do not affect original
        copy = image.sino_as_image_stack(0)
        copy.data += 1
        np.testing.assert_array_equal(raw_pixels, image.data)

        image = ImageStack(raw_pixels.copy(), name="tomo", sinograms=True)
        np.testing.assert_array_equal(raw_pixels[[0], :, :].swapaxes(0, 1), image.sino_as_image_stack(0).data)

    def test_processed_is_true(self):
        images = generate_images()
        images.record_operation("", "")
        self.assertTrue(images.is_processed)

    def test_processed_is_false(self):
        images = generate_images()
        self.assertFalse(images.is_processed)
