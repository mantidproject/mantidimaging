# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
import numpy as np
from unittest import mock

from PyQt5.QtGui import QColor
from parameterized import parameterized

from pyqtgraph import Point

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget, SpectrumPlotWidget
from mantidimaging.test_helpers import mock_versions, start_qapplication
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumROI


@start_qapplication
class SpectrumROITest(unittest.TestCase):

    def setUp(self) -> None:
        self.roi = SensibleROI(10, 20, 30, 40)
        self.spectrum_roi = SpectrumROI("test_roi", self.roi)

    def test_WHEN_initialise_THEN_pos_and_size_correct(self):
        self.assertEqual(self.spectrum_roi.getState()["pos"], Point(10, 20))
        self.assertEqual(self.spectrum_roi.getState()["size"], Point(20, 20))

    def test_WHEN_colour_changed_THEN_roi_colour_is_set(self):
        colour = (1, 2, 58, 255)
        self.spectrum_roi.openColorDialog = mock.Mock(return_value=QColor(*colour))
        self.spectrum_roi.onChangeColor()
        self.assertEqual(self.spectrum_roi.colour, colour)

    def test_WHEN_colour_is_not_valid_THEN_roi_colour_is_unchanged(self):
        colour = (10, 20, 480, 255)
        self.spectrum_roi.openColorDialog = mock.Mock(return_value=QColor(*colour))
        self.spectrum_roi.onChangeColor()
        self.assertEqual(self.spectrum_roi.colour, (0, 0, 0, 255))

    def test_WHEN_as_sensible_roi_called_THEN_correct_sensible_roi_returned(self):
        sensible_roi = self.spectrum_roi.as_sensible_roi()
        self.assertEqual((sensible_roi.left, sensible_roi.top, sensible_roi.right, sensible_roi.bottom),
                         (10, 20, 30, 40))


@mock_versions
@start_qapplication
class SpectrumWidgetTest(unittest.TestCase):

    def setUp(self) -> None:
        self.main_window = mock.create_autospec(MainWindowView)
        self.view = mock.create_autospec(SpectrumViewerWindowView)
        self.view.current_dataset_id = uuid.uuid4()
        self.view.parent = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.spectrum_widget = SpectrumWidget(self.main_window)
        self.spectrum_plot_widget = SpectrumPlotWidget()
        self.sensible_roi = SensibleROI.from_list([0, 0, 0, 0])

    def tearDown(self):
        self.spectrum_widget.cleanup()
        del self.spectrum_widget

    def test_WHEN_colour_generator_called_THEN_return_value_of_length_3(self):
        colour = self.spectrum_widget.colour_generator()
        self.assertEqual(len(colour), 4)

    def test_WHEN_colour_generator_called_THEN_valid_rgb_tuple_returned(self):
        colour = self.spectrum_widget.colour_generator()
        self.assertTrue(all(0 <= c <= 255 for c in colour))

    def test_WHEN_colour_generator_called_THEN_different_colours_returned(self):
        colour_list = [self.spectrum_widget.colour_generator() for _ in range(10)]
        self.assertEqual(len(colour_list), len({tuple(c) for c in colour_list}))

    def test_WHEN_change_roi_colour_called_THEN_roi_colour_changed(self):
        spectrum_roi = SpectrumROI("roi", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi"] = np.array([0, 0, 0, 0])
        roi_colour = self.spectrum_widget.roi_dict["roi"].pen.color().getRgb()
        self.spectrum_widget.change_roi_colour("roi", (255, 0, 0, 255))
        self.assertEqual(self.spectrum_widget.roi_dict["roi"].pen.color().getRgb(), (255, 0, 0, 255))
        self.assertNotEqual(self.spectrum_widget.roi_dict["roi"].pen.color().getRgb(), roi_colour)

    @parameterized.expand([("Visible", "visible_roi", 1), ("Invisible", "invisible_roi", 0)])
    def test_WHEN_set_roi_visibility_flags_called_THEN_roi_Visibility_flags_toggled(self, _, name, alpha):
        spectrum_roi = SpectrumROI(name, self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict[name] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict[name] = np.array([0, 0, 0, 0])
        self.spectrum_widget.set_roi_visibility_flags(name, alpha)
        self.assertEqual(bool(alpha), self.spectrum_widget.roi_dict[name].isVisible())

    @parameterized.expand([("range_100", 0, 100), ("range_200", 100, 300), ("range_300", 200, 500)])
    def test_WHEN_add_range_called_THEN_region_and_label_set_correctly(self, _, range_min, range_max):
        self.spectrum_plot_widget.add_range(range_min, range_max)
        self.assertEqual(self.spectrum_plot_widget.range_control.getRegion(), (range_min, range_max))
        self.assertEqual(self.spectrum_plot_widget._tof_range_label.text, f"Range: {range_min:.3f} - {range_max:.3f}")

    def test_WHEN_get_roi_called_THEN_SensibleROI_returned(self):
        spectrum_roi = SpectrumROI("roi", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        roi = self.spectrum_widget.get_roi("roi")
        self.assertIsInstance(type(roi), type(SensibleROI))
        self.assertIn("roi", self.spectrum_widget.roi_dict)

    def test_WHEN_get_roi_called_with_invalid_roi_name_THEN_raise_key_error(self):
        with self.assertRaises(KeyError):
            self.spectrum_widget.get_roi("invalid_roi")

    def test_WHEN_remove_roi_called_THEN_roi_removed_from_roi_dict(self):
        spectrum_roi = SpectrumROI("roi_1", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.assertIn("roi_1", self.spectrum_widget.roi_dict)
        self.spectrum_widget.remove_roi("roi_1")
        self.assertNotIn("roi_1", self.spectrum_widget.roi_dict.keys())
        self.assertNotIn(spectrum_roi, self.spectrum_widget.image.vb.addedItems)

    def test_WHEN_set_tof_range_called_THEN_range_control_set_correctly(self):
        self.spectrum_plot_widget.set_tof_range_label(0, 100)
        self.assertEqual(self.spectrum_plot_widget._tof_range_label.text, "Range: 0.000 - 100.000")

    def test_WHEN_rename_roi_called_THEN_roi_renamed(self):
        spectrum_roi = SpectrumROI("roi_1", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi_1"] = np.array([0, 0, 0, 0])
        self.assertIn("roi_1", self.spectrum_widget.roi_dict.keys())
        self.spectrum_widget.rename_roi("roi_1", "roi_2")
        self.assertNotIn("roi_1", self.spectrum_widget.roi_dict)
        self.assertIn("roi_2", self.spectrum_widget.roi_dict)

    def test_WHEN_rename_roi_called_with_default_roi_THEN_keyerror_is_raised(self):
        spectrum_roi = SpectrumROI("roi_1", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi_1"] = np.array([0, 0, 0, 0])
        with self.assertRaises(KeyError):
            self.spectrum_widget.rename_roi("roi_1", "roi")

    def test_WHEN_tof_axis_label_changed_THEN_axis_label_set(self):
        self.spectrum_plot_widget.set_tof_axis_label("test")
        self.assertEqual(self.spectrum_plot_widget.spectrum.getAxis('bottom').labelText, "test")

    def test_WHEN_roi_removed_THEN_roi_name_removed_from_list_of_roi_names(self):
        spectrum_roi = SpectrumROI("new_roi", self.sensible_roi, rotatable=False, scaleSnap=True, translateSnap=True)
        self.spectrum_widget.roi_dict = {"all": mock.Mock(), "roi": mock.Mock(), "new_roi": spectrum_roi}
        self.spectrum_widget.image.vb = mock.Mock()

        self.spectrum_widget.remove_roi("new_roi")
        self.assertListEqual(list(self.spectrum_widget.roi_dict.keys()), ["all", "roi"])

    def test_WHEN_remove_roi_called_with_default_roi_THEN_raise_runtime_error(self):
        self.spectrum_widget.roi_dict = {"all": mock.Mock(), "roi": mock.Mock()}
        with self.assertRaises(RuntimeError):
            self.spectrum_widget.remove_roi("all")

    def test_WHEN_invalid_roi_removed_THEN_keyerror_raised(self):
        self.spectrum_widget.roi_dict = {"all": mock.Mock(), "roi": mock.Mock()}
        with self.assertRaises(KeyError):
            self.spectrum_widget.remove_roi("non_existent_roi")

    def test_WHEN_rename_non_existent_roi_THEN_runtime_error(self):
        self.spectrum_widget.roi_dict = {"roi_1": mock.Mock(), "roi_2": mock.Mock()}
        self.spectrum_widget.spectrum_data_dict = {"roi_1": mock.Mock(), "roi_2": mock.Mock()}

        with self.assertRaises(RuntimeError):
            self.spectrum_widget.rename_roi("roi_invalid", "roi_new")

    def test_WHEN_rename_to_existing_roi_name_THEN_key_error(self):
        self.spectrum_widget.roi_dict = {"roi_1": mock.Mock(), "roi_2": mock.Mock()}
        self.spectrum_widget.spectrum_data_dict = {"roi_1": mock.Mock(), "roi_2": mock.Mock()}

        with self.assertRaises(KeyError):
            self.spectrum_widget.rename_roi("roi_1", "roi_2")
