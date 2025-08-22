# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
from pathlib import Path
from unittest import mock

import numpy as np
from PyQt5.QtWidgets import QPushButton, QActionGroup, QGroupBox, QAction, QCheckBox, QTabWidget
from parameterized import parameterized

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.spectrum_widgets.roi_form_widget import ROIFormWidget, ROIPropertiesTableWidget, \
    ROITableWidget
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.model import ErrorMode, ToFUnitMode, ROI_RITS, SpecType, \
    SpectrumViewerWindowModel
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget, SpectrumPlotWidget, SpectrumROI, \
    MIPlotItem
from mantidimaging.gui.widgets.spectrum_widgets.tof_properties import ExperimentSetupFormWidget
from mantidimaging.test_helpers import start_qapplication
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers.unit_test_helper import generate_images


@start_qapplication
class SpectrumViewerWindowPresenterTest(unittest.TestCase):

    def setUp(self) -> None:
        self.main_window = mock.create_autospec(MainWindowView, instance=True, stack_modified=mock.Mock())
        self.view = mock.create_autospec(SpectrumViewerWindowView, instance=True)
        self.view.current_dataset_id = uuid.uuid4()
        self.view.roi_form = mock.create_autospec(ROIFormWidget, instance=True)
        self.view.roi_form.roi_properties_widget = mock.create_autospec(ROIPropertiesTableWidget, instance=True)
        self.view.table_view = mock.create_autospec(ROITableWidget, instance=True)
        self.view.table_view.find_row_for_roi.return_value = 0
        type(self.view.table_view).current_roi_name = mock.PropertyMock(return_value="roi")
        mock_spectrum_roi_dict = mock.create_autospec(dict, instance=True)
        self.view.spectrum_widget = mock.create_autospec(SpectrumWidget, roi_dict=mock_spectrum_roi_dict, instance=True)
        self.view.spectrum_widget.spectrum_plot_widget = mock.create_autospec(SpectrumPlotWidget,
                                                                              roi_dict=mock_spectrum_roi_dict,
                                                                              instance=True)
        self.view.roi_form.exportButton = mock.create_autospec(QPushButton, instance=True)
        self.view.roi_form.exportButtonRITS = mock.create_autospec(QPushButton, instance=True)
        self.view.normalise_ShutterCount_CheckBox = mock.create_autospec(QCheckBox, instance=True)
        self.view.roi_form.addBtn = mock.create_autospec(QPushButton, instance=True)
        self.view.roi_form.exportTabs = mock.create_autospec(QTabWidget, instance=True)
        self.view.tof_mode_select_group = mock.create_autospec(QActionGroup, instance=True)
        self.view.experimentSetupGroupBox = mock.create_autospec(QGroupBox, instance=True)
        self.view.experimentSetupFormWidget = mock.Mock(spec=ExperimentSetupFormWidget)
        self.view.experimentSetupFormWidget.time_delay = 0.0
        self.view.fittingDisplayWidget = mock.Mock()
        self.view.scalable_roi_widget = mock.Mock()
        self.view.roiSelectionWidget = mock.Mock()
        self.view.fittingDisplayWidget.spectrum_plot = mock.Mock()
        self.view.fittingDisplayWidget.spectrum_plot.spectrum = mock.Mock()
        self.view.fittingDisplayWidget.update_labels = mock.Mock()
        self.presenter = SpectrumViewerWindowPresenter(self.view, self.main_window)

    def test_get_dataset_id_for_stack_no_stack_id(self):
        self.assertIsNone(self.presenter.get_dataset_id_for_stack(None))

    def test_get_dataset_id_for_stack(self):
        self.main_window.get_dataset_id_from_stack_uuid = mock.Mock()

        self.presenter.get_dataset_id_for_stack(uuid.uuid4())
        self.main_window.get_dataset_id_from_stack_uuid.assert_called_once()

    def test_handle_sample_change_has_flat_before(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = Dataset(sample=generate_images([10, 11, 12]), flat_before=generate_images())
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
        new_dataset = Dataset(sample=generate_images(), flat_after=generate_images())
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
        new_dataset = Dataset(sample=generate_images())
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
        self.view.roi_form.exportButton.setEnabled.assert_called_once_with(False)
        self.view.roi_form.exportButtonRITS.setEnabled.assert_called_once_with(False)
        self.view.roi_form.addBtn.setEnabled.assert_called_once_with(False)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(False)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    def test_WHEN_has_stack_no_norm_THEN_buttons_set(self, has_stack):
        has_stack.return_value = True
        self.view.normalisation_enabled.return_value = False
        self.presenter.handle_button_enabled()
        self.view.roi_form.exportButton.setEnabled.assert_called_once_with(True)
        self.view.roi_form.exportButtonRITS.setEnabled.assert_called_once_with(False)  # RITS export needs norm
        self.view.roi_form.addBtn.setEnabled.assert_called_once_with(True)
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
        self.view.roi_form.exportButton.setEnabled.assert_called_once_with(True)
        self.view.roi_form.exportButtonRITS.setEnabled.assert_called_once_with(True)
        self.view.roi_form.addBtn.setEnabled.assert_called_once_with(True)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(True)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.normalise_issue")
    def test_WHEN_has_stack_has_bad_norm_THEN_buttons_set(self, normalise_issue, has_stack):
        has_stack.return_value = True
        normalise_issue.return_value = "Something wrong"
        self.view.normalisation_enabled.return_value = True
        self.presenter.handle_button_enabled()
        self.view.roi_form.exportButton.setEnabled.assert_called_once_with(False)
        self.view.roi_form.exportButtonRITS.setEnabled.assert_called_once_with(False)
        self.view.roi_form.addBtn.setEnabled.assert_called_once_with(True)
        self.view.normalise_ShutterCount_CheckBox.setEnabled.assert_called_once_with(False)

    def test_WHEN_show_sample_call_THEN_add_range_set(self):
        self.presenter.view.normalisation_enabled.return_value = False
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
        mock_save_csv.assert_called_once_with(Path("/fake/path.csv"), {},
                                              normalise=False,
                                              normalise_with_shuttercount=False)

    @parameterized.expand(["/fake/path", "/fake/path.dat"])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_single_rits_spectrum")
    def test_handle_rits_export(self, path_name: str, mock_save_single_rits_spectrum: mock.Mock):
        self.view.get_rits_export_filename = mock.Mock(return_value=Path(path_name))
        self.view.transmission_error_mode = "Standard Deviation"

        mock_roi = SensibleROI.from_list([0, 0, 5, 5])
        self.view.spectrum_widget.get_roi = mock.Mock(return_value=mock_roi)
        self.presenter.model.set_stack(generate_images())
        self.presenter.handle_rits_export()

        self.view.get_rits_export_filename.assert_called_once()
        mock_save_single_rits_spectrum.assert_called_once_with(Path("/fake/path.dat"), ErrorMode.STANDARD_DEVIATION,
                                                               mock_roi)

    def test_WHEN_do_add_roi_called_THEN_new_roi_added(self):
        self.view.spectrum_widget.roi_dict = {"all": mock.Mock()}
        self.view.spectrum_widget.add_roi.side_effect = lambda roi, name: self.view.spectrum_widget.roi_dict.update(
            {name: mock.Mock()})
        self.presenter.model.set_stack(generate_images())
        for _ in range(2):
            self.presenter.do_add_roi()
        self.assertIn("roi", self.view.spectrum_widget.roi_dict)
        self.assertIn("roi_1", self.view.spectrum_widget.roi_dict)
        self.assertEqual(len(self.view.spectrum_widget.roi_dict), 3)

    def test_WHEN_do_add_roi_given_dupelicate_THEN_exception_raised(self):
        self.presenter.model.set_stack(generate_images())
        with (mock.patch.object(self.presenter.model, "roi_name_generator") as
              mocked_generator, mock.patch.object(self.view, "spectrum_widget") as mocked_spectrum_widget):
            mocked_generator.return_value = "roi"
            mocked_spectrum_widget.roi_dict = {"all": mock.Mock, "roi": mock.Mock}
            self.assertRaises(ValueError, self.presenter.do_add_roi)

    def test_WHEN_do_add_roi_to_table_called_THEN_roi_added_to_table(self):
        self.view.spectrum_widget.roi_dict = {"all": mock.Mock(), "roi": mock.Mock()}
        self.presenter.do_add_roi_to_table("roi")
        self.view.add_roi_table_row.assert_called_once_with("roi", mock.ANY)
        self.view.add_roi_table_row.reset_mock()
        self.view.spectrum_widget.roi_dict["roi_1"] = mock.Mock(colour=(255, 0, 0))
        self.presenter.do_add_roi_to_table("roi_1")
        self.view.add_roi_table_row.assert_called_once_with("roi_1", (255, 0, 0))

    def test_WHEN_do_remove_roi_called_THEN_roi_removed(self):
        self.presenter.view.spectrum_widget.roi_dict = {"all": mock.Mock(), "roi": mock.Mock(), "roi_1": mock.Mock()}
        self.presenter.view.spectrum_widget.remove_roi = mock.Mock()
        self.presenter.do_remove_roi("roi_1")

        self.presenter.view.spectrum_widget.remove_roi.assert_called_once_with("roi_1")

    def test_WHEN_roi_clicked_THEN_roi_updated(self):
        roi = SpectrumROI("themightyroi", SensibleROI())
        self.presenter.handle_roi_clicked(roi)
        self.view.set_roi_properties.assert_called_once()

    def test_WHEN_rits_roi_clicked_THEN_rois_not_updated(self):
        roi = SpectrumROI(ROI_RITS, SensibleROI())
        self.presenter.handle_roi_clicked(roi)
        self.view.set_roi_properties.assert_not_called()

    def test_WHEN_do_remove_roi_called_with_no_arguments_THEN_all_rois_removed(self):
        rois = ["all", "roi", "roi_1", "roi_2"]
        self.view.spectrum_widget.roi_dict = {roi: mock.Mock() for roi in rois}
        self.presenter.do_remove_roi()
        self.assertEqual(self.view.spectrum_widget.roi_dict, {})

    @parameterized.expand([("Image Index", ToFUnitMode.IMAGE_NUMBER), ("Wavelength", ToFUnitMode.WAVELENGTH),
                           ("Energy", ToFUnitMode.ENERGY), ("Time of Flight (\u03BCs)", ToFUnitMode.TOF_US)])
    def test_WHEN_tof_unit_selected_THEN_model_mode_changes(self, mode_text, expected_mode):
        self.view.tof_units_mode = mode_text
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_tof_unit_change_via_menu(mode_text)
        self.assertEqual(self.presenter.model.tof_mode, expected_mode)

    @parameterized.expand([
        (np.array([]), ToFUnitMode.IMAGE_NUMBER),
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
        (np.array([]), "Image Index", ToFUnitMode.IMAGE_NUMBER, np.arange(1, 10), [False,
                                                                                   True], ToFUnitMode.WAVELENGTH),
        (np.arange(1, 10), "Wavelength", ToFUnitMode.WAVELENGTH, np.array([]), [True, False], ToFUnitMode.IMAGE_NUMBER),
        (np.array([]), "Image Index", ToFUnitMode.IMAGE_NUMBER, np.array([]), [False, False], ToFUnitMode.IMAGE_NUMBER),
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
        self.view.experimentSetupGroupBox.setEnabled.assert_has_calls(expected_calls)
        self.assertEqual(self.presenter.model.tof_mode, expected_mode)

    def test_WHEN_no_stack_available_THEN_units_menu_disabled(self):
        self.presenter.current_stack_uuid = uuid.uuid4()
        self.presenter.handle_sample_change(None)
        self.view.tof_mode_select_group.setEnabled.assert_called_once_with(False)

    def test_WHEN_tof_flight_path_changed_THEN_unit_conversion_flight_path_set(self):
        self.view.experimentSetupFormWidget.flight_path = 10.0
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_experiment_setup_properties_change()
        self.assertEqual(self.presenter.model.units.target_to_camera_dist, 10.0)

    def test_WHEN_tof_delay_changed_THEN_unit_conversion_delay_set(self):
        self.view.experimentSetupFormWidget.time_delay = 400.00
        self.presenter.refresh_spectrum_plot = mock.Mock()
        self.presenter.handle_experiment_setup_properties_change()
        self.assertEqual(float(self.presenter.model.units.data_offset), 400.00 * 1e-6)

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

    @mock.patch.object(SpectrumViewerWindowModel, 'get_spectrum')
    def test_WHEN_roi_changed_via_spinboxes_THEN_roi_adjusted(self, mock_get_spectrum):
        self.view.roi_form.roi_properties_widget.to_roi = mock.Mock(return_value=SensibleROI(10, 10, 20, 30))
        type(self.view.table_view).current_roi_name = mock.PropertyMock(return_value="roi_1")
        self.view.roiSelectionWidget = mock.Mock()
        type(self.view.roiSelectionWidget).current_roi_name = mock.PropertyMock(return_value="roi_1")
        self.view.get_open_beam_roi = mock.Mock(return_value=None)
        roi_mock = mock.Mock()
        roi_mock.name = "roi_1"
        roi_mock.as_sensible_roi.return_value = SensibleROI(10, 10, 20, 30)
        self.view.spectrum_widget.roi_dict = {"roi_1": roi_mock}
        self.presenter.clear_spectrum = mock.Mock()
        self.presenter.changed_roi = mock.Mock()
        self.presenter.changed_roi.name = "roi_1"
        self.view.spectrum_widget.roi_dict = {"roi_1": SpectrumROI("roi_1", SensibleROI(10, 10, 20, 30))}
        self.view.spectrum_widget.spectrum = MIPlotItem()
        self.view.spectrum_widget.spectrum_data_dict = {"roi_1": np.arange(10)}
        mock_get_spectrum.return_value = np.arange(10)
        self.presenter.do_adjust_roi()
        wait_until(lambda: len(self.presenter.roi_to_process_queue) == 0, max_retry=1000)
        self.view.spectrum_widget.adjust_roi.assert_called_once_with(SensibleROI(10, 10, 20, 30), "roi_1")

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
        rois = ["all", "roi"]
        roi_data = {"all": SensibleROI(0, 0, 10, 8), "roi": SensibleROI(1, 4, 3, 2)}
        self.view.spectrum_widget.roi_dict = {roi: mock.Mock() for roi in rois}
        self.view.spectrum_widget.get_roi = mock.Mock(side_effect=roi_data.get)
        self.view.get_open_beam_roi_choice = mock.Mock(return_value="roi")

        self.presenter.model.get_spectrum = mock.Mock()
        self.presenter.redraw_all_rois()

        self.view.spectrum_widget.get_roi.assert_has_calls([mock.call(roi) for roi in rois], any_order=True)
        self.view.set_spectrum.assert_has_calls([mock.call(roi, mock.ANY) for roi in rois], any_order=True)

    def test_WHEN_roi_clicked_THEN_roi_properties_set(self):
        self.presenter.handle_roi_clicked(SpectrumROI("roi_clicked", SensibleROI(), pos=(0, 0)))
        self.view.set_roi_properties.assert_called_once()

    @parameterized.expand([(True, SpecType.SAMPLE_NORMED), (False, SpecType.SAMPLE)])
    def test_WHEN_normalised_enabled_THEN_correct_mode_set(self, norm_enabled, spec_type):
        self.presenter.redraw_all_rois = mock.Mock()
        self.presenter.handle_enable_normalised(norm_enabled)
        self.assertEqual(self.presenter.spectrum_mode, spec_type)
        self.view.display_normalise_error.assert_called_once()

    def test_show_initial_fit_calls_correct_plot_method(self):
        self.view.scalable_roi_widget.get_initial_param_values = mock.Mock(return_value=[1.0, 2.0, 3.0, 4.0])
        self.presenter.model.tof_data = np.array([1, 2, 3])
        self.presenter.model.fitting_engine.model.evaluate = mock.Mock(return_value=np.array([10, 20, 30]))
        self.view.fittingDisplayWidget.show_fit_line = mock.Mock()

        self.presenter.show_initial_fit()

        self.view.fittingDisplayWidget.show_fit_line.assert_called_once()
        args, kwargs = self.view.fittingDisplayWidget.show_fit_line.call_args
        np.testing.assert_array_equal(args[0], np.array([1, 2, 3]))
        np.testing.assert_array_equal(args[1], np.array([10, 20, 30]))
        assert kwargs["color"] == (128, 128, 128)
        assert kwargs["label"] == "initial"
        assert kwargs["initial"] is True
        self.view.fittingDisplayWidget.show_fit_line.reset_mock()

    @parameterized.expand([
        (True, True, False),  # (is_initial_fit_visible, expect_plot_initial, expect_show_fit)
        (False, False, True),
    ])
    def test_on_initial_params_edited_updates_plot_correctly(self, is_initial_fit_visible, expect_plot_initial,
                                                             expect_show_fit):
        self.presenter._plot_initial_fit = mock.Mock()
        self.view.fittingDisplayWidget.show_fit_line = mock.Mock()
        self.view.scalable_roi_widget.get_initial_param_values = mock.Mock(return_value=[1.0, 2.0, 3.0, 4.0])
        self.view.roiSelectionWidget.current_roi_name = "roi"
        self.view.spectrum_widget.get_roi = mock.Mock(return_value="mock_roi")
        self.presenter.model.get_spectrum = mock.Mock(return_value=np.array([1, 2, 3]))
        self.presenter.model.tof_data = np.array([1, 2, 3])
        self.presenter.model.fitting_engine.find_best_fit = mock.Mock(return_value={
            "mu": 1.0,
            "sigma": 2.0,
            "h": 3.0,
            "a": 4.0
        })
        self.view.scalable_roi_widget.set_fitted_parameter_values = mock.Mock()
        self.view.fittingDisplayWidget.is_initial_fit_visible.return_value = is_initial_fit_visible

        self.presenter.on_initial_params_edited()

        if expect_plot_initial:
            self.presenter._plot_initial_fit.assert_called_once()
            self.view.fittingDisplayWidget.show_fit_line.assert_not_called()
            self.view.scalable_roi_widget.set_fitted_parameter_values.assert_not_called()
        if expect_show_fit:
            self.presenter._plot_initial_fit.assert_not_called()
            self.view.fittingDisplayWidget.show_fit_line.assert_called_once()
            args, kwargs = self.view.fittingDisplayWidget.show_fit_line.call_args
            np.testing.assert_array_equal(args[0], np.array([1, 2, 3]))
            assert kwargs["color"] == (0, 128, 255)
            assert kwargs["label"] == "fit"
            assert kwargs["initial"] is False
            self.view.scalable_roi_widget.set_fitted_parameter_values.assert_called_once_with({
                "mu": 1.0,
                "sigma": 2.0,
                "h": 3.0,
                "a": 4.0
            })

    @parameterized.expand([
        ([1.0, 2.0], [10, 20, 30], [100, 200, 300]),
        ([0.5, 1.5], [5, 15, 25], [50, 150, 250]),
    ])
    def test_show_fit_calls_show_fit_line_with_expected_args(self, fitted_params, xvals, fit):
        xvals = np.array(xvals)
        fit = np.array(fit)
        self.presenter.model.tof_data = xvals
        self.presenter.model.fitting_engine.model.evaluate = mock.Mock(return_value=fit)
        self.view.fittingDisplayWidget.show_fit_line = mock.Mock()

        self.presenter.show_fit(fitted_params)

        self.presenter.model.fitting_engine.model.evaluate.assert_called_once_with(xvals, fitted_params)
        self.view.fittingDisplayWidget.show_fit_line.assert_called_once_with(xvals,
                                                                             fit,
                                                                             color=(0, 128, 255),
                                                                             label="fit",
                                                                             initial=False)
