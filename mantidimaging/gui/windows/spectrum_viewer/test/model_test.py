# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from pathlib import Path, PurePath
from unittest import mock
import io

import numpy as np
import numpy.testing as npt
from parameterized import parameterized

from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter, SpectrumViewerWindowModel
from mantidimaging.gui.windows.spectrum_viewer.model import SpecType
from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


class CloseCheckStream(io.StringIO):
    is_closed: bool = False

    def close(self) -> None:
        # don't call real close as it clears buffer
        self.is_closed = True


class SpectrumViewerWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.presenter = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.model = SpectrumViewerWindowModel(self.presenter)

    def test_set_stack(self):
        stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)

        self.assertEqual(self.model._stack, stack)
        self.assertEqual(self.model.tof_range, (0, 9))

    def test_set_normalise_stack(self):
        normalise_stack = generate_images([10, 11, 12])
        self.model.set_normalise_stack(normalise_stack)

        self.assertEqual(self.model._normalise_stack, normalise_stack)

    def test_get_image_shape(self):
        stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)

        self.assertEqual(self.model.get_image_shape(), (11, 12))

    def test_get_averaged_image(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        stack.data[:5, :, :] = 2
        self.model.set_stack(stack)

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], (1.5))

    def test_get_averaged_image_range(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        stack.data[:, :, :] = np.arange(0, 10).reshape((10, 1, 1))
        self.model.set_stack(stack)
        self.model.tof_range = (6, 7)

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], 6.5)

    def test_get_spectrum(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        model_spec = self.model.get_spectrum("roi", SpecType.SAMPLE)
        self.assertEqual(model_spec.shape, (10, ))
        npt.assert_array_equal(model_spec, spectrum)

    def test_get_normalised_spectrum(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        self.model.set_normalise_stack(normalise_stack)

        model_open_spec = self.model.get_spectrum("roi", SpecType.OPEN)
        self.assertEqual(model_open_spec.shape, (10, ))
        self.assertTrue(np.all(model_open_spec == 2))

        model_norm_spec = self.model.get_spectrum("roi", SpecType.SAMPLE_NORMED)
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, spectrum / 2)

    def test_get_normalised_spectrum_zeros(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        normalise_stack.data[5] = 0
        self.model.set_normalise_stack(normalise_stack)

        model_norm_spec = self.model.get_spectrum("roi", SpecType.SAMPLE_NORMED)
        expected_spec = spectrum / 2
        expected_spec[5] = 0
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, expected_spec)

    def test_get_normalised_spectrum_different_size(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        self.model.set_stack(stack)

        normalise_stack = ImageStack(np.ones([10, 11, 13]))
        self.model.set_normalise_stack(normalise_stack)

        error_spectrum = self.model.get_spectrum("roi", SpecType.SAMPLE_NORMED)
        np.testing.assert_array_equal(error_spectrum, np.array([]))

    def test_normalise_issue(self):
        self.assertIn("selected", self.model.normalise_issue())

        stack = ImageStack(np.ones([10, 11, 12]))
        self.model.set_stack(stack)
        self.model.set_normalise_stack(stack)
        self.assertIn("different", self.model.normalise_issue())

        self.model.set_normalise_stack(ImageStack(np.ones([10, 11, 13])))
        self.assertIn("shapes", self.model.normalise_issue())

        self.model.set_normalise_stack(ImageStack(np.ones([10, 11, 12])))
        self.assertEqual("", self.model.normalise_issue())

    def test_set_stack_sets_roi(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        self.model.set_stack(stack)
        self.assertEqual(self.model.get_roi("all"), self.model.get_roi('roi'))
        npt.assert_array_equal(self.model.get_roi("all").top, 0)
        npt.assert_array_equal(self.model.get_roi("all").left, 0)
        npt.assert_array_equal(self.model.get_roi("all").right, 12)
        npt.assert_array_equal(self.model.get_roi("all").bottom, 11)

    def test_if_set_stack_called_with_additional_rois_present_THEN_do_remove_roi_called(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.model.set_new_roi("new_roi_2")

        self.assertListEqual(self.model.get_list_of_roi_names(), ['all', 'roi', 'new_roi', 'new_roi_2'])
        self.model.set_stack(generate_images())
        self.presenter.do_remove_roi.assert_called_once()

    def test_if_set_stack_called_with_no_additional_rois_present_THEN_do_remove_roi_not_called(self):
        self.model.set_stack(generate_images())

        self.assertListEqual(self.model.get_list_of_roi_names(), ['all', 'roi'])
        self.model.set_stack(generate_images())
        self.presenter.do_remove_roi.assert_not_called()

    def test_get_spectrum_roi(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        stack.data[:, :, 6:] *= 2
        self.model.set_stack(stack)

        self.model.set_roi('roi', SensibleROI.from_list([0, 0, 3, 3]))
        model_spec = self.model.get_spectrum("roi", SpecType.SAMPLE)
        npt.assert_array_equal(model_spec, spectrum)

        self.model.set_roi('roi', SensibleROI.from_list([6, 0, 6 + 3, 3]))
        model_spec = self.model.get_spectrum("roi", SpecType.SAMPLE)
        npt.assert_array_equal(model_spec, spectrum * 2)

    def test_save_csv(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10) * 2
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)
        self.model.set_normalise_stack(None)

        mock_stream = CloseCheckStream()
        mock_path = mock.create_autospec(Path)
        mock_path.open.return_value = mock_stream

        self.model.save_csv(mock_path, False)
        mock_path.open.assert_called_once_with("w")
        self.assertIn("# tof_index,all,roi", mock_stream.getvalue())
        self.assertIn("0.0,0.0,0.0", mock_stream.getvalue())
        self.assertIn("1.0,2.0,2.0", mock_stream.getvalue())
        self.assertTrue(mock_stream.is_closed)

    def test_WHEN_save_csv_called_THEN_save_roi_coords_called_WITH_correct_args(self):
        path = Path("test_file.csv")
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            self.model.save_roi_coords(path)
        mock_open.assert_called_once_with(path, encoding='utf-8', mode='w')

    def test_WHEN_get_roi_coords_filename_called_THEN_correct_filename_returned(self):
        path = PurePath("test_file.csv")
        expected_path = PurePath("test_file_roi_coords.csv")
        self.assertEqual(expected_path, self.model.get_roi_coords_filename(path))

    def test_save_csv_norm_missing_stack(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10) * 2
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)
        self.model.set_normalise_stack(None)
        with self.assertRaises(RuntimeError):
            self.model.save_csv(mock.Mock(), True)

    def test_save_csv_norm(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))

        open_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        self.model.set_stack(stack)
        self.model.set_normalise_stack(open_stack)

        mock_stream = CloseCheckStream()
        mock_path = mock.create_autospec(Path)
        mock_path.open.return_value = mock_stream

        self.model.save_csv(mock_path, True)
        mock_path.open.assert_called_once_with("w")
        self.assertIn("# tof_index,all,all_open,all_norm,roi,roi_open,roi_norm", mock_stream.getvalue())
        self.assertIn("0.0,0.0,2.0,0.0,0.0,2.0,0.0", mock_stream.getvalue())
        self.assertIn("1.0,1.0,2.0,0.5,1.0,2.0,0.5", mock_stream.getvalue())
        self.assertTrue(mock_stream.is_closed)

    def test_WHEN_roi_name_generator_called_THEN_correct_names_returned_visible_to_model(self):
        self.assertEqual(self.model.roi_name_generator(), "roi_1")
        self.assertEqual(self.model.roi_name_generator(), "roi_2")
        self.assertEqual(self.model.roi_name_generator(), "roi_3")

    def test_WHEN_get_list_of_roi_names_called_THEN_correct_list_returned(self):
        self.model.set_stack(generate_images())
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi"])

    def test_when_new_roi_set_THEN_roi_name_added_to_list_of_roi_names(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.assertTrue(self.model.get_roi("new_roi"))
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi", "new_roi"])

    def test_WHEN_get_roi_called_with_non_existent_name_THEN_error_raised(self):
        self.model.set_stack(generate_images())
        with self.assertRaises(KeyError):
            self.model.get_roi("non_existent_roi")

    @parameterized.expand([
        ("False", None, False),
        ("True", ImageStack(np.ones([10, 11, 12])), True),
    ])
    def test_WHEN_stack_value_set_THEN_can_export_returns_(self, _, image_stack, expected):
        self.model.set_stack(image_stack)
        self.assertEqual(self.model.can_export(), expected)

    def test_WHEN_roi_removed_THEN_roi_name_removed_from_list_of_roi_names(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi", "new_roi"])
        self.model.remove_roi("new_roi")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi"])

    def test_WHEN_remove_roi_called_with_default_roi_THEN_raise_runtime_error(self):
        self.model.set_stack(generate_images())
        with self.assertRaises(RuntimeError):
            self.model.remove_roi("all")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi"])

    def test_WHEN_invalid_roi_removed_THEN_keyerror_raised(self):
        self.model.set_stack(generate_images())
        with self.assertRaises(KeyError):
            self.model.remove_roi("non_existent_roi")

    def test_WHEN_remove_all_rois_called_THEN_all_but_default_rois_removed(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.model.set_new_roi("new_roi_2")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi", "new_roi", "new_roi_2"])
        self.model.remove_all_roi()
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi"])

    def test_WHEN_roi_renamed_THEN_roi_name_changed_in_list_of_roi_names(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi", "new_roi"])
        self.model.rename_roi("new_roi", "imaging_is_the_coolest")
        self.assertListEqual(self.model.get_list_of_roi_names(), ["all", "roi", "imaging_is_the_coolest"])

    def test_WHEN_invalid_roi_renamed_THEN_keyerror_raised(self):
        self.model.set_stack(generate_images())
        with self.assertRaises(KeyError):
            self.model.rename_roi("non_existent_roi", "imaging_is_the_coolest")

    @parameterized.expand([
        ("all"),
        ("roi"),
    ])
    def test_WHEN_default_roi_renamed_THEN_runtime_error_raised(self, roi_name):
        self.model.set_stack(generate_images())
        with self.assertRaises(RuntimeError):
            self.model.rename_roi(roi_name, "imaging_is_the_coolest")
