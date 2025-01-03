# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from pathlib import Path, PurePath
from unittest import mock
import io
import math

import numpy as np
import numpy.testing as npt
from parameterized import parameterized

from mantidimaging.core.io.instrument_log import InstrumentLog, ShutterCount, ShutterCountColumn
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter, SpectrumViewerWindowModel
from mantidimaging.gui.windows.spectrum_viewer.model import SpecType, ErrorMode
from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


class CloseCheckStream(io.StringIO):
    is_closed: bool = False
    captured: list[str] = []

    def close(self) -> None:
        # On close capture value
        self.is_closed = True
        self.captured = self.getvalue().splitlines()
        super().close()


class SpectrumViewerWindowModelTest(unittest.TestCase):

    def setUp(self) -> None:
        self.presenter = mock.create_autospec(SpectrumViewerWindowPresenter, instance=True)
        self.model = SpectrumViewerWindowModel(self.presenter)

    def _set_sample_stack(self, with_tof=False, with_shuttercount=False):
        spectrum = np.arange(0, 10)
        stack = ImageStack(np.ones([10, 11, 12]) * spectrum.reshape((10, 1, 1)))
        if with_tof:
            mock_inst_log = mock.create_autospec(InstrumentLog, source_file="", instance=True)
            mock_inst_log.get_column.return_value = np.arange(0, 10) * 0.1
            stack.log_file = mock_inst_log
        if with_shuttercount:
            mock_shuttercounts = mock.create_autospec(ShutterCount, source_file="", instance=True)
            mock_shuttercounts.get_column.return_value = np.arange(5, 15)
            stack._shutter_count_file = mock_shuttercounts
        self.model.set_stack(stack)
        self.model.set_new_roi("roi")
        return stack, spectrum

    def _set_normalise_stack(self, with_shuttercount=False):
        spectrum = np.arange(10, 20)
        normalise_stack = ImageStack(np.ones([10, 11, 12]) * spectrum.reshape((10, 1, 1)))
        self.model.set_normalise_stack(normalise_stack)
        if with_shuttercount:
            mock_shuttercounts = mock.create_autospec(ShutterCount, source_file="", instance=True)
            mock_shuttercounts.get_column.return_value = np.arange(10, 20)
            normalise_stack._shutter_count_file = mock_shuttercounts
        return normalise_stack

    def _make_mock_path_stream(self):
        mock_stream = CloseCheckStream()
        mock_path = mock.create_autospec(Path, instance=True)
        mock_path.open.return_value = mock_stream
        return mock_stream, mock_path

    def test_set_stack(self):
        stack, _ = self._set_sample_stack()

        self.assertEqual(self.model._stack, stack)
        self.assertEqual(self.model.tof_range, (0, 9))
        self.assertEqual(self.model.get_image_shape(), (11, 12))

    def test_set_normalise_stack(self):
        normalise_stack = generate_images([10, 11, 12])
        self.model.set_normalise_stack(normalise_stack)

        self.assertEqual(self.model._normalise_stack, normalise_stack)

    def test_get_averaged_image(self):
        self._set_sample_stack()

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], 4.5)

    def test_get_averaged_image_range(self):
        self._set_sample_stack()
        self.model.tof_range = (6, 7)

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], 6.5)

    def test_get_spectrum(self):
        stack, spectrum = self._set_sample_stack()
        roi = SensibleROI(left=0, top=0, right=12, bottom=11)
        model_spec = self.model.get_spectrum(roi, SpecType.SAMPLE)
        self.assertEqual(model_spec.shape, (10, ))
        npt.assert_array_equal(model_spec, spectrum)

    def test_get_normalised_spectrum(self):
        stack, spectrum = self._set_sample_stack()
        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        self.model.set_normalise_stack(normalise_stack)
        roi = SensibleROI(left=0, top=0, right=12, bottom=11)
        model_open_spec = self.model.get_spectrum(roi, SpecType.OPEN)
        self.assertEqual(model_open_spec.shape, (10, ))
        self.assertTrue(np.all(model_open_spec == 2))
        model_norm_spec = self.model.get_spectrum(roi, SpecType.SAMPLE_NORMED)
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, spectrum / 2)

    def test_get_normalised_spectrum_zeros(self):
        stack, spectrum = self._set_sample_stack()

        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        normalise_stack.data[5] = 0
        self.model.set_normalise_stack(normalise_stack)
        roi = SensibleROI(left=0, top=0, right=12, bottom=11)
        model_norm_spec = self.model.get_spectrum(roi, SpecType.SAMPLE_NORMED)
        expected_spec = spectrum / 2
        expected_spec[5] = 0
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, expected_spec)

    def test_get_normalised_spectrum_different_size(self):
        self._set_sample_stack()

        normalise_stack = ImageStack(np.ones([10, 11, 13]))
        self.model.set_normalise_stack(normalise_stack)
        roi = SensibleROI(left=0, top=0, right=13, bottom=11)
        error_spectrum = self.model.get_spectrum(roi, SpecType.SAMPLE_NORMED)
        np.testing.assert_array_equal(error_spectrum, np.array([]))

    def test_normalise_issue(self):
        self.assertIn("selected", self.model.normalise_issue())

        stack, _ = self._set_sample_stack()
        self.model.set_normalise_stack(stack)
        self.assertIn("different", self.model.normalise_issue())

        self.model.set_normalise_stack(ImageStack(np.ones([10, 11, 13])))
        self.assertIn("shapes", self.model.normalise_issue())

        self.model.set_normalise_stack(ImageStack(np.ones([10, 11, 12])))
        self.assertEqual("", self.model.normalise_issue())

    def test_set_stack_sets_roi(self):
        self._set_sample_stack()
        roi_all = self.model._roi_ranges["all"]
        roi = self.model._roi_ranges["roi"]

        self.assertEqual(roi_all, roi)
        self.assertEqual(roi_all.top, 0)
        self.assertEqual(roi_all.left, 0)
        self.assertEqual(roi_all.right, 12)
        self.assertEqual(roi_all.bottom, 11)

    def test_if_set_stack_called_THEN_do_remove_roi_not_called(self):
        self.model.set_stack(generate_images())
        self.presenter.do_remove_roi.assert_not_called()

    def test_get_spectrum_roi(self):
        stack, spectrum = self._set_sample_stack()
        stack.data[:, :, 6:] *= 2

        roi = SensibleROI.from_list([0, 0, 3, 3])
        model_spec = self.model.get_spectrum(roi, SpecType.SAMPLE)
        npt.assert_array_equal(model_spec, spectrum)

        roi = SensibleROI.from_list([6, 0, 6 + 3, 3])
        model_spec = self.model.get_spectrum(roi, SpecType.SAMPLE)
        npt.assert_array_equal(model_spec, spectrum * 2)

    def test_get_stack_spectrum(self):
        stack, spectrum = self._set_sample_stack()
        calculated_spectrum = self.model.get_stack_spectrum(stack, SensibleROI.from_list([0, 0, 12, 11]))
        np.testing.assert_array_equal(spectrum, calculated_spectrum)

    def test_get_stack_spectrum_summed(self):
        stack, spectrum = self._set_sample_stack()
        calculated_spectrum = self.model.get_stack_spectrum_summed(stack, SensibleROI.from_list([0, 0, 12, 11]))
        np.testing.assert_array_equal(spectrum * 12 * 11, calculated_spectrum)

    def test_save_csv(self):
        stack, spectrum = self._set_sample_stack()
        stack.data *= 2
        self.model.set_normalise_stack(None)

        roi_all = SensibleROI.from_list([0, 0, 12, 11])
        roi_specific = SensibleROI.from_list([0, 0, 3, 3])
        rois = {"all": roi_all, "roi": roi_specific}

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_csv(mock_path, rois=rois, normalise=False)

        mock_path.open.assert_called_once_with("w")
        self.assertIn("# ToF_index,all,roi", mock_stream.captured[0])
        self.assertIn("# Index,Counts,Counts", mock_stream.captured[1])
        self.assertIn("0.0,0.0,0.0", mock_stream.captured[2])
        self.assertIn("1.0,2.0,2.0", mock_stream.captured[3])
        self.assertTrue(mock_stream.is_closed)

    def test_save_rits_dat(self):
        stack, spectrum = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :6] *= 2
        self.model.set_normalise_stack(norm)

        roi = SensibleROI.from_list([0, 0, 12, 11])
        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_rits_roi(mock_path, ErrorMode.STANDARD_DEVIATION, roi)

        mock_path.open.assert_called_once_with("w")
        self.assertIn("0.0\t0.0\t0.0", mock_stream.captured[0])
        self.assertIn("100000.0\t0.75\t0.25", mock_stream.captured[1])
        self.assertIn("200000.0\t1.5\t0.5", mock_stream.captured[2])
        self.assertTrue(mock_stream.is_closed)

    def test_save_rits_roi_dat(self):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :5] *= 2
        self.model.set_new_roi("rits_roi")
        self.model.set_roi("rits_roi", SensibleROI.from_list([0, 0, 10, 11]))
        self.model.set_normalise_stack(norm)

        self.model._roi_ranges["ROI_RITS"] = SensibleROI.from_list([0, 0, 10, 11])
        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_rits_roi(mock_path, ErrorMode.STANDARD_DEVIATION, self.model._roi_ranges["ROI_RITS"])

        mock_path.open.assert_called_once_with("w")
        self.assertIn("0.0\t0.0\t0.0", mock_stream.captured[0])
        self.assertIn("100000.0\t0.75\t0.25", mock_stream.captured[1])
        self.assertIn("200000.0\t1.5\t0.5", mock_stream.captured[2])
        self.assertTrue(mock_stream.is_closed)

    @parameterized.expand([
        ("std_dev", ErrorMode.STANDARD_DEVIATION, [0., 0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25]),
        ("std_dev", ErrorMode.PROPAGATED,
         [0.0000, 0.0772, 0.1306, 0.1823, 0.2335, 0.2845, 0.3354, 0.3862, 0.4369, 0.4876]),
    ])
    def test_save_rits_data_errors(self, _, error_mode, expected_error):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :5] *= 2
        self.model.set_normalise_stack(norm)

        self.model._roi_ranges["ROI_RITS"] = SensibleROI.from_list([0, 0, 10, 11])
        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            with mock.patch.object(self.model, "export_spectrum_to_rits") as mock_export:
                self.model.save_rits_roi(mock_path, error_mode, self.model._roi_ranges["ROI_RITS"])

        calculated_errors = mock_export.call_args[0][3]
        np.testing.assert_allclose(expected_error, calculated_errors, atol=1e-4)

    def test_invalid_error_mode_rits(self):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.ones([10, 11, 12]))
        self.model.set_normalise_stack(norm)
        roi = SensibleROI.from_list([0, 0, 12, 11])

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.assertRaises(ValueError, self.model.save_rits_roi, mock_path, None, roi)
        mock_path.open.assert_not_called()

    def test_save_rits_no_norm_err(self):
        stack, _ = self._set_sample_stack()
        self.model.set_normalise_stack(None)
        mock_inst_log = mock.create_autospec(InstrumentLog, source_file="", instance=True)
        stack.log_file = mock_inst_log
        roi = SensibleROI.from_list([0, 0, 12, 11])
        self.model._roi_ranges["ROI_RITS"] = roi

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.assertRaises(ValueError, self.model.save_rits_roi, mock_path, ErrorMode.STANDARD_DEVIATION, roi)
        mock_path.open.assert_not_called()

    def test_save_rits_no_tof_err(self):
        self._set_sample_stack()
        norm = ImageStack(np.ones([10, 11, 12]))
        self.model.set_normalise_stack(norm)
        roi = SensibleROI.from_list([0, 0, 12, 11])

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.assertRaises(ValueError, self.model.save_rits_roi, mock_path, ErrorMode.STANDARD_DEVIATION, roi)
        mock_path.open.assert_not_called()

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
        stack, _ = self._set_sample_stack()
        stack.data *= 2
        self.model.set_normalise_stack(None)

        roi_all = SensibleROI.from_list([0, 0, 12, 11])
        rois = {"all": roi_all}

        with self.assertRaises(RuntimeError):
            self.model.save_csv(mock.Mock(), rois=rois, normalise=True)

    def test_save_csv_norm(self):
        self._set_sample_stack()

        open_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        self.model.set_normalise_stack(open_stack)

        roi_all = SensibleROI.from_list([0, 0, 12, 11])
        roi_specific = SensibleROI.from_list([0, 0, 3, 3])
        rois = {"all": roi_all, "roi": roi_specific}

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_csv(path=mock_path, rois=rois, normalise=True, normalise_with_shuttercount=False)

        mock_path.open.assert_called_once_with("w")
        self.assertIn("# ToF_index,all,all_open,all_norm,roi,roi_open,roi_norm", mock_stream.captured[0])
        self.assertIn("# Index,Counts,Counts,Counts,Counts,Counts,Counts", mock_stream.captured[1])
        self.assertIn("0.0,0.0,2.0,0.0,0.0,2.0,0.0", mock_stream.captured[2])
        self.assertIn("1.0,1.0,2.0,0.5,1.0,2.0,0.5", mock_stream.captured[3])
        self.assertTrue(mock_stream.is_closed)

    def test_save_csv_norm_with_tof_loaded(self):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :5] *= 2
        self.model.set_normalise_stack(norm)

        roi_all = SensibleROI.from_list([0, 0, 12, 11])
        rois = {"all": roi_all, "roi": roi_all}

        mock_stream, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_csv(mock_path, rois=rois, normalise=True, normalise_with_shuttercount=False)

        mock_path.open.assert_called_once_with("w")
        self.assertIn("# ToF_index,Wavelength,ToF,Energy,all,all_open,all_norm,roi,roi_open,roi_norm",
                      mock_stream.captured[0])
        self.assertIn("# Index,Angstrom,Microseconds,MeV,Counts,Counts,Counts", mock_stream.captured[1])
        self.assertIn("0.0,0.0,0.0,inf,0.0,2.0,0.0,0.0,2.0,0.0", mock_stream.captured[2])
        self.assertIn(
            "1.0,7.064346392065392,100000.0,2.9271405738026552,1.4166666666666667,2.0,0.7083333333333334,1.4166666666666667,2.0,0.7083333333333334",
            mock_stream.captured[3])
        self.assertTrue(mock_stream.is_closed)

    def test_WHEN_roi_name_generator_called_THEN_correct_names_returned_visible_to_model(self):
        self.assertEqual(self.model.roi_name_generator(), "roi")
        self.assertEqual(self.model.roi_name_generator(), "roi_1")
        self.assertEqual(self.model.roi_name_generator(), "roi_2")
        self.assertEqual(self.model.roi_name_generator(), "roi_3")

    def test_WHEN_rois_deleted_THEN_name_generator_is_reset(self):
        self.assertEqual(self.model.roi_name_generator(), "roi")
        self.assertEqual(self.model.roi_name_generator(), "roi_1")
        self.assertEqual(self.model.roi_name_generator(), "roi_2")
        self.model.remove_all_roi()
        self.assertEqual(self.model.roi_name_generator(), "roi")
        self.assertEqual(self.model.roi_name_generator(), "roi_1")
        self.assertEqual(self.model.roi_name_generator(), "roi_2")

    def test_when_new_roi_set_THEN_roi_name_added_to_list_of_roi_names(self):
        self.model.set_stack(generate_images())
        self.model.set_new_roi("new_roi")
        self.assertIn("new_roi", self.model._roi_ranges)
        self.assertListEqual(list(self.model._roi_ranges.keys()), ["all", "new_roi"])

    @parameterized.expand([
        ("False", None, False),
        ("True", ImageStack(np.ones([10, 11, 12])), True),
    ])
    def test_WHEN_stack_value_set_THEN_can_export_returns_(self, _, image_stack, expected):
        self.model.set_stack(image_stack)
        self.assertEqual(self.model.has_stack(), expected)

    def test_WHEN_remove_all_rois_called_THEN_all_but_default_rois_removed(self):
        self.model.set_stack(generate_images())
        rois = ["new_roi", "new_roi_2"]
        for roi in rois:
            self.model.set_new_roi(roi)
        self.assertListEqual(list(self.model._roi_ranges.keys()), ["all"] + rois)
        self.model.remove_all_roi()
        self.assertListEqual(list(self.model._roi_ranges.keys()), [])

    def test_WHEN_no_stack_tof_THEN_time_of_flight_none(self):
        # No Stack
        self.model.set_stack(None)
        self.assertIsNone(self.model.get_stack_time_of_flight())

        # No Log
        stack, _ = self._set_sample_stack()
        self.assertIsNone(self.model.get_stack_time_of_flight())

        # Log but not tof
        mock_log = mock.create_autospec(InstrumentLog, source_file="foo.txt", instance=True)
        mock_log.get_column.side_effect = KeyError()
        stack.log_file = mock_log
        self.assertIsNone(self.model.get_stack_time_of_flight())

    def test_WHEN_stack_tof_THEN_tof_correct(self):
        stack, _ = self._set_sample_stack(with_tof=True)

        tof_result = self.model.get_stack_time_of_flight()
        self.assertIsInstance(tof_result, np.ndarray)
        npt.assert_array_equal(tof_result, np.arange(0, 10) * 0.1)

    def test_error_modes(self):
        self.assertEqual(ErrorMode.get_by_value("Standard Deviation"), ErrorMode.STANDARD_DEVIATION)
        self.assertEqual(ErrorMode.get_by_value("Propagated"), ErrorMode.PROPAGATED)
        self.assertRaises(ValueError, ErrorMode.get_by_value, "")

    @parameterized.expand([
        ("larger_than_1", 1, 0, ValueError),  # bin_size and step_size < 1
        ("bin_less_than_or_equal_to_step", 1, 2, ValueError),  # bin_size <= step_size
        ("less_than_roi", 10, 10, ValueError),  # bin_size and step_size > min(roi.width, roi.height)
        ("valid", 2, 1, None),  # valid case
    ])
    def test_validate_bin_and_step_size(self, _, bin_size, step_size, expected_exception):
        roi = SensibleROI.from_list([0, 0, 5, 5])
        if expected_exception:
            with self.assertRaises(expected_exception):
                self.model.validate_bin_and_step_size(roi, bin_size, step_size)
        else:
            try:
                self.model.validate_bin_and_step_size(roi, bin_size, step_size)
            except ValueError:
                self.fail("validate_bin_and_step_size() raised ValueError unexpectedly!")

    @parameterized.expand([
        (["5x5_bin_2_step_1", 5, 2, 1]),
        (["5x5_bin_2_step_2", 5, 3, 2]),
        (["7x7_bin_2_step_3", 7, 4, 1]),
    ])
    @mock.patch.object(SpectrumViewerWindowModel, "save_rits_roi")
    def test_save_rits_images_write_correct_number_of_files(self, _, roi_size, bin_size, step, mock_save_rits_roi):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :5] *= 2
        roi_name = "rits_roi"
        roi = SensibleROI.from_list([0, 0, roi_size, roi_size])
        self.model._roi_ranges[roi_name] = roi
        self.model.set_normalise_stack(norm)

        Mx, My = roi.width, roi.height
        x_iterations = min(math.ceil(Mx / step), math.ceil((Mx - bin_size) / step) + 1)
        y_iterations = min(math.ceil(My / step), math.ceil((My - bin_size) / step) + 1)
        expected_number_of_calls = x_iterations * y_iterations
        _, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_rits_images(mock_path, ErrorMode.STANDARD_DEVIATION, bin_size, step)
        self.assertEqual(mock_save_rits_roi.call_count, expected_number_of_calls)

    @mock.patch.object(SpectrumViewerWindowModel, "save_rits_roi")
    def test_save_single_rits_spectrum(self, mock_save_rits_roi):
        stack, _ = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        stack.data[:, :, :5] *= 2
        self.model.set_new_roi("rits_roi")
        self.model.set_roi("rits_roi", SensibleROI.from_list([0, 0, 5, 5]))
        self.model.set_normalise_stack(norm)
        self.model._roi_ranges["ROI_RITS"] = SensibleROI.from_list([0, 0, 5, 5])

        _, mock_path = self._make_mock_path_stream()
        with mock.patch.object(self.model, "save_roi_coords"):
            self.model.save_single_rits_spectrum(mock_path, ErrorMode.STANDARD_DEVIATION)

    @mock.patch.object(SpectrumViewerWindowModel, "export_spectrum_to_rits")
    def test_save_rits_correct_transmision(self, mock_save_rits_roi):
        stack, spectrum = self._set_sample_stack(with_tof=True)
        norm = ImageStack(np.full([10, 11, 12], 2))
        for i in range(10):
            stack.data[:, :, i] *= i
        self.model.set_new_roi("rits_roi")
        self.model.set_roi("rits_roi", SensibleROI.from_list([1, 0, 6, 4]))
        self.model.set_normalise_stack(norm)
        mock_path = mock.create_autospec(Path, instance=True)

        self.model.save_rits_images(mock_path, ErrorMode.STANDARD_DEVIATION, 3, 1)

        self.assertEqual(6, len(mock_save_rits_roi.call_args_list))
        expected_means = [1, 1.5, 2, 1, 1.5, 2]  # running average of [1, 2, 3, 4, 5], divided by 2 for normalisation
        for call, expected_mean in zip(mock_save_rits_roi.call_args_list, expected_means, strict=True):
            transmission = call[0][2]
            expected_transmission = spectrum * expected_mean
            npt.assert_array_equal(expected_transmission, transmission)

    def test_get_stack_shuttercounts_returns_none_if_no_stack(self):
        self.assertEqual(self.model.get_stack_shuttercounts(stack=None), None)

    def test_get_stack_shuttercounts_returns_shutter_count_if_stack(self):
        stack, _ = self._set_sample_stack(with_tof=True, with_shuttercount=True)
        normalise_stack = self._set_normalise_stack(with_shuttercount=True)

        self.assertTrue(
            np.array_equal(self.model.get_stack_shuttercounts(stack),
                           stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)))
        self.assertTrue(
            np.array_equal(self.model.get_stack_shuttercounts(normalise_stack),
                           normalise_stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)))

    def test_get_shuttercount_normalised_correction_parameter_returns_one_if_no_stack(self):
        with mock.patch.object(self.model, "get_stack_shuttercounts") as mock_get_stack_shuttercounts:
            mock_get_stack_shuttercounts.return_value = None
            self.assertEqual(self.model.get_shuttercount_normalised_correction_parameter(), 1.0)

    def test_get_shuttercount_normalised_correction_parameter_with_none_values(self):
        self.model.get_stack_shuttercounts = mock.MagicMock(return_value=None)
        expected_result = 1.0
        result = self.model.get_shuttercount_normalised_correction_parameter()
        self.assertEqual(result, expected_result)

    def test_get_shuttercount_normalised_correction_parameter_with_values(self):
        stack, _ = self._set_sample_stack(with_tof=True, with_shuttercount=True)
        normalise_stack = self._set_normalise_stack(with_shuttercount=True)

        stack_column = stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        normalise_stack_column = normalise_stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)

        with mock.patch.object(self.model, "get_stack_shuttercounts") as mock_get_stack_shuttercounts:
            mock_get_stack_shuttercounts.side_effect = [stack_column, normalise_stack_column]
            expected_result = stack_column[0] / normalise_stack_column[0]

            result = self.model.get_shuttercount_normalised_correction_parameter()
            self.assertEqual(result, expected_result)

    def test_get_transmission_error_standard_dev(self):
        stack, _ = self._set_sample_stack(with_tof=True, with_shuttercount=True)
        normalise_stack = self._set_normalise_stack(with_shuttercount=True)
        sample_shutter_counts = stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        open_shutter_counts = normalise_stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        average_shutter_counts = sample_shutter_counts[0] / open_shutter_counts[0]
        roi = SensibleROI.from_list([0, 0, 5, 5])
        self.model._roi_ranges["roi"] = roi

        left, top, right, bottom = roi
        sample = stack.data[:, top:bottom, left:right]
        open = normalise_stack.data[:, top:bottom, left:right]
        expected = np.divide(sample, open, out=np.zeros_like(sample), where=open != 0) / average_shutter_counts
        expected = np.std(expected, axis=(1, 2))

        with (mock.patch.object(self.model,
                                "get_shuttercount_normalised_correction_parameter",
                                return_value=average_shutter_counts) as
              mock_get_shuttercount_normalised_correction_parameter):
            result = self.model.get_transmission_error_standard_dev(roi, normalise_with_shuttercount=True)
            mock_get_shuttercount_normalised_correction_parameter.assert_called_once()
        self.assertEqual(len(expected), len(result))
        np.testing.assert_allclose(expected, result)

    def test_get_transmission_error_standard_dev_raises_runtimeerror_if_no_stack(self):
        with self.assertRaises(RuntimeError):
            self.model.get_transmission_error_standard_dev("roi")

    def test_get_transmission_error_propogated(self):
        stack, _ = self._set_sample_stack(with_tof=True, with_shuttercount=True)
        normalise_stack = self._set_normalise_stack(with_shuttercount=True)
        sample_shutter_counts = stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        open_shutter_counts = normalise_stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        average_shutter_counts = sample_shutter_counts[0] / open_shutter_counts[0]

        roi = SensibleROI.from_list([0, 0, 5, 5])
        sample = self.model.get_stack_spectrum_summed(stack, roi)
        open = self.model.get_stack_spectrum_summed(normalise_stack, roi)
        expected = np.sqrt(sample / open**2 + sample**2 / open**3) / average_shutter_counts

        with mock.patch.object(
                self.model, "get_shuttercount_normalised_correction_parameter",
                return_value=average_shutter_counts) as mock_get_shuttercount_normalised_correction_parameter:
            result = self.model.get_transmission_error_propagated(roi, normalise_with_shuttercount=True)
            mock_get_shuttercount_normalised_correction_parameter.assert_called_once()
        np.testing.assert_allclose(result, expected)

    def test_get_transmission_error_propogated_raises_runtimeerror_if_no_stack(self):
        with self.assertRaises(RuntimeError):
            self.model.get_transmission_error_propagated("roi")
