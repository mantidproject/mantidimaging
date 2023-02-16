# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
import numpy as np
from unittest import mock
from parameterized import parameterized

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget
from mantidimaging.test_helpers import mock_versions, start_qapplication
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumROI


@mock_versions
@start_qapplication
class SpectrumWidgetTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.view = mock.create_autospec(SpectrumViewerWindowView)
        self.view.current_dataset_id = uuid.uuid4()
        self.view.parent = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.spectrum_widget = SpectrumWidget()
        self.sensible_roi = SensibleROI.from_list([0, 0, 0, 0])

    def test_WHEN_colour_generator_called_THEN_return_value_of_length_3(self):
        colour = self.spectrum_widget.random_colour_generator()
        self.assertEqual(len(colour), 3)

    def test_WHEN_colour_generator_called_THEN_valid_rgb_tuple_returned(self):
        colour = self.spectrum_widget.random_colour_generator()
        self.assertTrue(all([0 <= c <= 255 for c in colour]))

    def test_WHEN_colour_generator_called_THEN_different_colours_returned(self):
        colour_list = [self.spectrum_widget.random_colour_generator() for _ in range(10)]
        self.assertEqual(len(colour_list), len(set(tuple(c) for c in colour_list)))

    @parameterized.expand([("range_100", 0, 100), ("range_200", 100, 300), ("range_300", 200, 500)])
    def test_WHEN_add_range_called_THEN_region_and_label_set_correctly(self, _, range_min, range_max):
        self.spectrum_widget.add_range(range_min, range_max)
        self.assertEqual(self.spectrum_widget.range_control.getRegion(), (range_min, range_max))
        self.assertEqual(self.spectrum_widget._tof_range_label.text, f"ToF range: {range_min} - {range_max}")

    def test_WHEN_get_roi_called_THEN_SensibleROI_returned(self):
        spectrum_roi = SpectrumROI("roi",
                                   self.sensible_roi,
                                   pos=(0, 0),
                                   rotatable=False,
                                   scaleSnap=True,
                                   translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        roi = self.spectrum_widget.get_roi("roi")
        self.assertIsInstance(type(roi), type(SensibleROI))
        self.assertIn("roi", self.spectrum_widget.roi_dict)

    def test_WHEN_get_roi_called_with_invalid_roi_name_THEN_raise_key_error(self):
        with self.assertRaises(KeyError):
            self.spectrum_widget.get_roi("invalid_roi")

    def test_WHEN_remove_roi_called_THEN_roi_removed_from_roi_dict(self):
        spectrum_roi = SpectrumROI("roi_1",
                                   self.sensible_roi,
                                   pos=(0, 0),
                                   rotatable=False,
                                   scaleSnap=True,
                                   translateSnap=True)
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.assertIn("roi_1", self.spectrum_widget.roi_dict)
        self.spectrum_widget.remove_roi("roi_1")
        self.assertNotIn("roi_1", self.spectrum_widget.roi_dict.keys())
        self.assertNotIn(spectrum_roi, self.spectrum_widget.image.vb.addedItems)

    def test_WHEN_set_tof_range_called_THEN_range_control_set_correctly(self):
        self.spectrum_widget._set_tof_range_label(0, 100)
        self.assertEqual(self.spectrum_widget._tof_range_label.text, "ToF range: 0 - 100")

    def test_WHEN_rename_roi_called_THEN_roi_renamed(self):
        spectrum_roi = SpectrumROI("roi_1",
                                   self.sensible_roi,
                                   pos=(0, 0),
                                   rotatable=False,
                                   scaleSnap=True,
                                   translateSnap=True)
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi_1"] = np.array([0, 0, 0, 0])
        self.assertIn("roi_1", self.spectrum_widget.roi_dict.keys())
        self.spectrum_widget.rename_roi("roi_1", "roi_2")
        self.assertNotIn("roi_1", self.spectrum_widget.roi_dict)
        self.assertIn("roi_2", self.spectrum_widget.roi_dict)

    def test_WHEN_rename_roi_called_with_default_roi_THEN_roi_name_not_changed(self):
        spectrum_roi = SpectrumROI("roi_1",
                                   self.sensible_roi,
                                   pos=(0, 0),
                                   rotatable=False,
                                   scaleSnap=True,
                                   translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        self.spectrum_widget.roi_dict["roi_1"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi_1"] = np.array([0, 0, 0, 0])
        self.assertIn("roi_1", self.spectrum_widget.roi_dict.keys())
        self.spectrum_widget.rename_roi("roi_1", "roi")
        self.assertIn("roi_1", self.spectrum_widget.roi_dict)

    def test_WHEN_reset_size_called_THEN_roi_size_reset(self):
        image_shape = (100, 100)
        spectrum_roi = SpectrumROI("roi",
                                   self.sensible_roi,
                                   pos=(0, 0),
                                   rotatable=False,
                                   scaleSnap=True,
                                   translateSnap=True)
        self.spectrum_widget.roi_dict["roi"] = spectrum_roi
        self.spectrum_widget.spectrum_data_dict["roi"] = np.array([0, 0, 0, 0])
        self.spectrum_widget.reset_roi_size(image_shape)
        img_x, img_y = spectrum_roi.size()
        self.assertEqual((img_x, img_y), (100, 100))
