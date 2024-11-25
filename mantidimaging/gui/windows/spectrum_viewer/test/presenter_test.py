# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
from pathlib import Path
from unittest import mock

import numpy as np
from PyQt5.QtWidgets import QPushButton, QGroupBox, QCheckBox, QTabWidget
from parameterized import parameterized

from mantidimaging.core.data.dataset import StrictDataset, Dataset
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.model import ToFUnitMode, ROI_RITS, SpecType
from mantidimaging.gui.windows.spectrum_viewer.presenter import ExportMode
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget, SpectrumPlotWidget, SpectrumROI
from mantidimaging.test_helpers import mock_versions, start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images


@mock_versions
@start_qapplication
class SpectrumViewerWindowPresenterTest(unittest.TestCase):

    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.view = mock.create_autospec(SpectrumViewerWindowView)
        self.view.current_dataset_id = uuid.uuid4()
        mock_spectrum_roi_dict = mock.create_autospec(dict)
        self.view.spectrum_widget = mock.create_autospec(SpectrumWidget, roi_dict=mock_spectrum_roi_dict)
        self.view.spectrum_widget.spectrum_plot_widget = mock.create_autospec(SpectrumPlotWidget,
                                                                              roi_dict=mock_spectrum_roi_dict)
        self.view.exportButton = mock.create_autospec(QPushButton)
        self.view.exportButtonRITS = mock.create_autospec(QPushButton)
        self.view.normalise_ShutterCount_CheckBox = mock.create_autospec(QCheckBox)
        self.view.addBtn = mock.create_autospec(QPushButton)
        self.view.exportTabs = mock.create_autospec(QTabWidget)
        self.view.tof_mode_select_group = mock.create_autospec(QActionGroup)
        self.view.tofPropertiesGroupBox = mock.create_autospec(QGroupBox)
        self.presenter = SpectrumViewerWindowPresenter(self.view, self.main_window)

    def test_get_dataset_id_for_stack_no_stack_id(self):
        self.assertIsNone(self.presenter.get_dataset_id_for_stack(None))

    def test_get_dataset_id_for_stack(self):
        self.main_window.get_dataset_id_from_stack_uuid = mock.Mock()

        self.presenter.get_dataset_id_for_stack(uuid.uuid4())
        self.main_window.get_dataset_id_from_stack_uuid.assert_called_once()

    def test_handle_sample_change_has_flat_before(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(sample=generate_images([10, 11, 12]), flat_before=generate_images())
        new_dataset.flat_before.name = 'Flat_before'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()
        self.presenter.handle_tof_unit_change = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.view.try_to_select_relevant_normalise_stack.assert_called_once_with('Flat_before')
        self.presenter.show_new_sample.assert_called_once()

    def test_handle_sample_change_has_flat_after(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(sample=generate_images(), flat_after=generate_images())
        new_dataset.flat_after.name = 'Flat_after'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_tof_unit_change = mock.Mock()
        self.presenter.handle_sample_change(uuid.uuid4())
        self.view.try_to_select_relevant_normalise_stack.assert_called_once_with('Flat_after')
        self.presenter.show_new_sample.assert_called_once()

    def test_handle_sample_change_no_new_stack(self):
        self.presenter.current_stack_uuid = uuid.uuid4()
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=None)
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()
        self.presenter.show_new_sample = mock.Mock()

        self.presenter.handle_sample_change(None)
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()
        self.assertIsNone(self.view.current_dataset_id)
        self.presenter.show_new_sample.assert_not_called()

    def test_handle_sample_change_dataset_unchanged(self):
        initial_dataset_id = self.view.current_dataset_id
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=initial_dataset_id)
        self.presenter.main_window.get_dataset = mock.Mock()
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.presenter.handle_tof_unit_change = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_not_called()
        self.assertEqual(self.view.current_dataset_id, initial_dataset_id)

    def test_handle_sample_change_to_dataset_no_sample(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = Dataset(stacks=[generate_images()])
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()
        self.presenter.handle_tof_unit_change = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_called_once()
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()

    def test_handle_sample_change_no_flat(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(sample=generate_images())
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()
        self.presenter.handle_tof_unit_change = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_called_once()
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    def test_WHEN_no_stack_THEN_buttons_disabled(self, has_stack):
        has_stack.return_value = False
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(False)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(False)
        self.view.addBtn.setEnabled.assert_called_once_with(False)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(False)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    def test_WHEN_has_stack_no_norm_THEN_buttons_set(self, has_stack):
        has_stack.return_value = True
        self.view.normalisation_enabled.return_value = False
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(True)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(False)  # RITS export needs norm
        self.view.addBtn.setEnabled.assert_called_once_with(True)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(False)  # Shuttercount needs norm

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.normalise_issue")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.shuttercount_issue")
    def test_WHEN_has_stack_has_good_norm_THEN_buttons_set(self, shuttercount_issue, normalise_issue, has_stack):
        has_stack.return_value = True
        normalise_issue.return_value = ""
        shuttercount_issue.return_value = ""
        self.view.normalisation_enabled.return_value = True
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(True)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(True)
        self.view.addBtn.setEnabled.assert_called_once_with(True)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(True)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.normalise_issue")
    def test_WHEN_has_stack_has_bad_norm_THEN_buttons_set(self, normalise_issue, has_stack):
        has_stack.return_value = True
        normalise_issue.return_value = "Something wrong"
        self.view.normalisation_enabled.return_value = True
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(False)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(False)
        self.view.addBtn.setEnabled.assert_called_once_with(True)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(False)

    def test_WHEN_show_sample_call_THEN_add_range_set(self):
        self.presenter.model.set_stack(generate_images([10, 5, 5]))
        self.presenter.model.tof_plot_range = (0, 9)
        self.presenter.show_new_sample()
        self.view.spectrum_widget.spectrum_plot_widget.add_range.assert_called_once_with(0, 9)

    def test_gui_changes_tof_range(self):
        image_stack = generate_images([30, 11, 12])
        new_tof_range = (10, 20)
        self.presenter.model.set_stack(image_stack)
        self.presenter.model.tof_mode = ToFUnitMode.IMAGE_NUMBER
        self.presenter.handle_range_slide_moved(new_tof_range)

        self.assertEqual(self.presenter.model.tof_range, new_tof_range)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_csv")
    def test_handle_export_csv_none(self, mock_save_csv: mock.Mock):
        self.view.get_csv_filename = mock.Mock(return_value=None)

        self.presenter.handle_export_csv()

        self.view.get_csv_filename.assert_called_once()
        mock_save_csv.assert_not_called()

    @parameterized.expand(["/fake/path", "/fake/path.csv"])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.shuttercount_issue")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_csv")
    def test_handle_export_csv(self, path_name: str, mock_save_csv: mock.Mock, mock_shuttercount_issue):
        self.view.get_csv_filename = mock.Mock(return_value=Path(path_name))
        self.view.shuttercount_norm_enabled.return_value = False
        mock_shuttercount_issue.return_value = "Something wrong"

        self.presenter.model.set_stack(generate_images())

        self.presenter.handle_export_csv()

        self.view.get_csv_filename.assert_called_once()
        mock_save_csv.assert_called_once_with(Path("/fake/path.csv"), False, False)

    @parameterized.expand(["/fake/path", "/fake/path.dat"])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_rits_roi")
    def test_handle_rits_export(self, path_name: str, mock_save_rits_roi: mock.Mock):
        self.view.get_rits_export_filename = mock.Mock(return_value=Path(path_name))
        self.view.transmission_error_mode = "Standard Deviation"
        self.view.spectrum_widget.add_new_roi("rits_roi")

        self.presenter.model.set_stack(generate_images())

        self.presenter.handle_rits_export()

        self.view.get_rits_export_filename.assert_called_once()
        mock_save_rits_roi.assert_called_once_with(Path("/fake/path.dat"), ErrorMode.STANDARD_DEVIATION,
                                                   self.view.spectrum_widget.get_roi("rits_roi"))

    def test_WHEN_do_add_roi_called_THEN_new_roi_added(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.assertEqual(["all", "roi"], self.view.spectrum_widget.get_list_of_roi_names())
        self.view.spectrum_widget.add_new_roi("roi_1")
        self.assertEqual(["all", "roi", "roi_1"], self.view.spectrum_widget.get_list_of_roi_names())

    def test_WHEN_do_add_roi_given_duplicate_THEN_exception_raised(self):
        with (mock.patch.object(self.view.spectrum_widget, "roi_dict") as mocked_spectrum_widget):
            mocked_spectrum_widget.roi_dict = {"all": mock.Mock, "roi": mock.Mock}
            with self.assertRaises(ValueError):
                self.view.spectrum_widget.add_new_roi("roi")

    def test_WHEN_do_add_roi_to_table_called_THEN_roi_added_to_table(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.view.add_roi_table_row.assert_called_once_with("roi", mock.ANY)
        self.view.add_roi_table_row.reset_mock()

        self.assertEqual(["all", "roi"], self.view.spectrum_widget.get_list_of_roi_names())
        self.view.spectrum_widget.roi_dict = {"roi_1": mock.Mock()}
        self.view.spectrum_widget.add_new_roi("roi_1")
        self.view.add_roi_table_row.assert_called_once_with("roi_1", mock.ANY)

    def test_WHEN_do_remove_roi_called_THEN_roi_removed(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.view.spectrum_widget.add_new_roi("roi_1")
        self.assertEqual(["all", "roi", "roi_1"], self.view.spectrum_widget.get_list_of_roi_names())
        self.view.spectrum_widget.remove_roi("roi_1")
        self.assertEqual(["all", "roi"], self.view.spectrum_widget.get_list_of_roi_names())

    def test_WHEN_roi_clicked_THEN_roi_updated(self):
        roi = SpectrumROI("themightyroi", SensibleROI())
        self.presenter.handle_roi_clicked(roi)
        self.assertEqual(self.view.current_roi_name, "themightyroi")
        self.assertEqual(self.view.last_clicked_roi, "themightyroi")
        self.view.set_roi_properties.assert_called_once()

    def test_WHEN_rits_roi_clicked_THEN_rois_not_updated(self):
        self.view.current_roi_name = self.view.last_clicked_roi = "NOT_RITS_ROI"
        roi = SpectrumROI(ROI_RITS, SensibleROI())
        self.presenter.handle_roi_clicked(roi)
        self.assertEqual(self.view.current_roi_name, "NOT_RITS_ROI")
        self.assertEqual(self.view.last_clicked_roi, "NOT_RITS_ROI")
        self.view.set_roi_properties.assert_not_called()

    def test_WHEN_ROI_renamed_THEN_roi_renamed(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.view.spectrum_widget.rename_roi("roi", "imaging_is_the_best")
        self.assertEqual(self.view.spectrum_widget.get_list_of_roi_names(), ["all", "imaging_is_the_best"])

    def test_WHEN_default_ROI_renamed_THEN_default_roi_renamed(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.view.spectrum_widget.rename_roi("roi", "imaging_is_the_best")
        self.assertEqual(self.view.spectrum_widget.get_list_of_roi_names(), ["all", "imaging_is_the_best"])

    @parameterized.expand(["all", "roi"])
    def test_WHEN_ROI_renamed_to_existing_name_THEN_runtimeerror(self, name):
        self.view.spectrum_widget.add_new_roi("roi")
        self.assertEqual(["all", "roi"], self.view.spectrum_widget.get_list_of_roi_names())
        with self.assertRaises(KeyError):
            self.view.spectrum_widget.rename_roi("roi", name)
        self.assertEqual(["all", "roi"], self.view.spectrum_widget.get_list_of_roi_names())

    def test_WHEN_do_remove_roi_called_with_no_arguments_THEN_all_rois_removed(self):
        self.view.spectrum_widget.add_new_roi("roi")
        self.view.spectrum_widget.add_new_roi("roi_1")
        self.view.spectrum_widget.add_new_roi("roi_2")
        self.assertEqual(["all", "roi", "roi_1", "roi_2"], self.view.spectrum_widget.get_list_of_roi_names())
        self.view.spectrum_widget.remove_all_rois()
        self.assertEqual([], self.view.spectrum_widget.get_list_of_roi_names())

    @parameterized.expand([("Image Index", ToFUnitMode.IMAGE_NUMBER), ("Wavelength", ToFUnitMode.WAVELENGTH),
                           ("Energy", ToFUnitMode.ENERGY), ("Time of Flight (\u03BCs)", ToFUnitMode.TOF_US)])
    def test_WHEN_tof_unit_selected_THEN_model_mode_changes(self, mode_text, expected_mode):
        self.view.tof_units_mode = mode_text
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_tof_unit_change_via_menu()
        self.assertEqual(self.presenter.model.tof_mode, expected_mode)

    @parameterized.expand([
        (None, ToFUnitMode.IMAGE_NUMBER),
        (np.arange(1, 10), ToFUnitMode.WAVELENGTH),
    ])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.get_stack_time_of_flight")
    def test_WHEN_data_loaded_THEN_relevant_mode_set(self, tof_data, expected_tof_mode, get_stack_time_of_flight):
        self.presenter.model.set_stack(generate_images())
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        get_stack_time_of_flight.return_value = tof_data
        self.view.tof_units_mode = "Wavelength"
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_sample_change(uuid.uuid4())
        self.assertEqual(self.presenter.model.tof_mode, expected_tof_mode)

    @parameterized.expand([
        (None, "Image Index", ToFUnitMode.IMAGE_NUMBER, np.arange(1, 10), [False, True], ToFUnitMode.WAVELENGTH),
        (np.arange(1, 10), "Wavelength", ToFUnitMode.WAVELENGTH, None, [True, False], ToFUnitMode.IMAGE_NUMBER),
        (None, "Image Index", ToFUnitMode.IMAGE_NUMBER, None, [False, False], ToFUnitMode.IMAGE_NUMBER),
        (np.arange(1, 10), "Wavelength", ToFUnitMode.WAVELENGTH, np.arange(2, 20), [True,
                                                                                    True], ToFUnitMode.WAVELENGTH),
        (np.arange(1, 10), "Energy", ToFUnitMode.ENERGY, np.arange(2, 20), [True, True], ToFUnitMode.ENERGY),
        (np.arange(1, 10), "Time of Flight (\u03BCs)", ToFUnitMode.TOF_US, np.arange(2, 20), [True,
                                                                                              True], ToFUnitMode.TOF_US)
    ])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.get_stack_time_of_flight")
    def test_WHEN_switch_between_no_spectra_to_spectra_files_THEN_tof_modes_availability_set(
            self, tof_data_before, tof_mode_text_before, tof_mode_before, tof_data_after, expected_calls, expected_mode,
            get_stack_time_of_flight):
        self.presenter.model.set_stack(generate_images())
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        get_stack_time_of_flight.return_value = tof_data_before
        self.presenter.model.tof_mode = tof_mode_before
        self.view.tof_units_mode = tof_mode_text_before
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_sample_change(uuid.uuid4())

        get_stack_time_of_flight.return_value = tof_data_after
        self.presenter.handle_sample_change(uuid.uuid4())
        expected_calls = [mock.call(b) for b in expected_calls]
        self.view.tof_mode_select_group.setEnabled.assert_has_calls(expected_calls)
        self.view.tofPropertiesGroupBox.setEnabled.assert_has_calls(expected_calls)
        self.assertEqual(self.presenter.model.tof_mode, expected_mode)

    def test_WHEN_no_stack_available_THEN_units_menu_disabled(self):
        self.presenter.current_stack_uuid = uuid.uuid4()
        self.presenter.handle_sample_change(None)
        self.view.tof_mode_select_group.setEnabled.assert_called_once_with(False)

    def test_WHEN_tof_flight_path_changed_THEN_unit_conversion_flight_path_set(self):
        self.view.flightPathSpinBox = mock.Mock()
        self.view.flightPathSpinBox.value.return_value = 10
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_flight_path_change()
        self.assertEqual(self.presenter.model.units.target_to_camera_dist, 10)

    def test_WHEN_tof_delay_changed_THEN_unit_conversion_delay_set(self):
        self.view.timeDelaySpinBox = mock.Mock()
        self.view.timeDelaySpinBox.value.return_value = 400
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_time_delay_change()
        self.assertEqual(self.presenter.model.units.data_offset, 400 * 1e-6)

    def test_WHEN_menu_option_selected_THEN_menu_option_changed(self):
        menu_options = [QAction("opt1"), QAction("opt2"), QAction("opt3"), QAction("opt4")]
        menu_options[0].setObjectName("opt1")
        menu_options[1].setObjectName("opt2")
        menu_options[2].setObjectName("opt3")
        menu_options[3].setObjectName("opt4")
        self.presenter.check_action = mock.Mock()
        self.view.tof_mode_select_group.actions = mock.Mock(return_value=menu_options)
        self.presenter.change_selected_menu_option("opt2")
        calls = [mock.call(menu_options[a], b) for a, b in [(0, False), (1, True), (2, False), (3, False)]]
        self.presenter.check_action.assert_has_calls(calls)

    def test_WHEN_roi_changed_via_spinboxes_THEN_roi_adjusted(self):
        self.presenter.view.roiPropertiesSpinBoxes = mock.Mock()
        self.presenter.convert_spinbox_roi_to_SensibleROI = mock.Mock(return_value=SensibleROI(10, 10, 20, 30))
        self.view.current_roi_name = "roi_1"
        self.presenter.do_adjust_roi()
        self.view.spectrum_widget.adjust_roi.assert_called_once_with(SensibleROI(10, 10, 20, 30), "roi_1")

    @parameterized.expand([(["roi_1", "roi_2", "roi_3"], "roi_2", "roi_2", ExportMode.IMAGE_MODE, "roi_2"),
                           (["roi_1", "roi_3"], "roi_3", "roi_2", ExportMode.IMAGE_MODE, "roi_3"),
                           (["roi_1", "roi_2", "roi_3"], ROI_RITS, "roi_2", ExportMode.ROI_MODE, "roi_2")])
    def test_WHEN_change_tab_THEN_current_roi_correct(self, old_table_names, current_roi_name, last_clicked_roi,
                                                      export_mode, expected_roi):
        self.view.old_table_names = old_table_names
        self.view.current_roi_name = current_roi_name
        self.view.last_clicked_roi = last_clicked_roi
        self.presenter.export_mode = export_mode
        self.presenter.handle_storing_current_roi_name_on_tab_change()
        self.assertEqual(self.view.current_roi_name, expected_roi)
        self.assertEqual(self.view.last_clicked_roi, expected_roi)

    def test_WHEN_refresh_spectrum_plot_THEN_spectrum_plot_refreshed(self):
        self.view.spectrum_widget.spectrum = mock.MagicMock()
        self.presenter.model.tof_plot_range = (23, 45)
        self.presenter.model.tof_range = (1, 80)
        self.presenter.refresh_spectrum_plot()
        self.view.show_visible_spectrums.assert_called_once()
        self.view.spectrum_widget.spectrum_plot_widget.add_range.assert_called_once_with(23, 45)
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label.assert_called_once_with(1, 80)
        self.view.auto_range_image.assert_called_once()

    def test_WHEN_redraw_all_rois_THEN_rois_set_correctly(self):

        def spec_roi_mock(name):
            if name == "all":
                return SensibleROI(0, 0, 10, 8)
            if name == "roi":
                return SensibleROI(1, 4, 3, 2)
            return None

        self.view.spectrum_widget.get_roi = mock.Mock(side_effect=spec_roi_mock)
        self.presenter.model.set_stack(generate_images())
        self.view.spectrum_widget.add_new_roi("roi")

        self.presenter.model.get_spectrum = mock.Mock()
        self.presenter.redraw_all_rois()

        self.assertEqual(self.view.spectrum_widget.get_roi("all"), SensibleROI(0, 0, 10, 8))
        self.assertEqual(self.view.spectrum_widget.get_roi("roi"), SensibleROI(1, 4, 3, 2))

        calls = [mock.call(a, b) for a, b in [("roi", mock.ANY)]]
        self.view.set_spectrum.assert_has_calls(calls)

    @parameterized.expand([("roi", "roi_clicked", "roi_clicked"), ("roi", ROI_RITS, "roi")])
    def test_WHEN_roi_clicked_THEN_current_and_last_clicked_roi_updated_correctly(self, old_roi, clicked_roi,
                                                                                  expected_roi):
        self.view.current_roi_name = old_roi
        self.view.last_clicked_roi = old_roi
        self.presenter.handle_roi_clicked(SpectrumROI(clicked_roi, SensibleROI(), pos=(0, 0)))
        self.assertEqual(self.view.current_roi_name, expected_roi)
        self.assertEqual(self.view.last_clicked_roi, expected_roi)

    def test_WHEN_roi_clicked_THEN_roi_properties_set(self):
        self.view.current_roi_name = ""
        self.view.last_clicked_roi = ""
        self.presenter.handle_roi_clicked(SpectrumROI("roi_clicked", SensibleROI(), pos=(0, 0)))
        self.view.set_roi_properties.assert_called_once()

    @parameterized.expand([(True, SpecType.SAMPLE_NORMED), (False, SpecType.SAMPLE)])
    def test_WHEN_normalised_enabled_THEN_correct_mode_set(self, norm_enabled, spec_type):
        self.presenter.redraw_all_rois = mock.Mock()
        self.presenter.handle_enable_normalised(norm_enabled)
        self.assertEqual(self.presenter.spectrum_mode, spec_type)
        self.view.display_normalise_error.assert_called_once()
