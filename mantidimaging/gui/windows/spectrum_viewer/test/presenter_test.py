# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import uuid
from pathlib import Path
from unittest import mock

from PyQt5.QtWidgets import QPushButton
from parameterized import parameterized

from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.model import ErrorMode
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget
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
        self.view.spectrum = mock.create_autospec(SpectrumWidget, roi_dict=mock_spectrum_roi_dict)
        self.view.exportButton = mock.create_autospec(QPushButton)
        self.view.exportButtonRITS = mock.create_autospec(QPushButton)
        self.view.addBtn = mock.create_autospec(QPushButton)
        self.presenter = SpectrumViewerWindowPresenter(self.view, self.main_window)

    def test_get_dataset_id_for_stack_no_stack_id(self):
        self.assertIsNone(self.presenter.get_dataset_id_for_stack(None))

    def test_get_dataset_id_for_stack(self):
        self.main_window.get_dataset_id_from_stack_uuid = mock.Mock()

        self.presenter.get_dataset_id_for_stack(uuid.uuid4())
        self.main_window.get_dataset_id_from_stack_uuid.assert_called_once()

    def test_handle_sample_change_has_flat_before(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images([10, 11, 12]), flat_before=generate_images())
        new_dataset.flat_before.name = 'Flat_before'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.view.try_to_select_relevant_normalise_stack.assert_called_once_with('Flat_before')
        self.presenter.show_new_sample.assert_called_once()

    def test_handle_sample_change_has_flat_after(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images(), flat_after=generate_images())
        new_dataset.flat_after.name = 'Flat_after'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

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

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_not_called()
        self.assertEqual(self.view.current_dataset_id, initial_dataset_id)

    def test_handle_sample_change_to_MixedDataset(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = MixedDataset([generate_images()])
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_called_once()
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()

    def test_handle_sample_change_no_flat(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images())
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

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

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    def test_WHEN_has_stack_no_norm_THEN_buttons_set(self, has_stack):
        has_stack.return_value = True
        self.view.normalisation_enabled.return_value = False
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(True)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(False)  # RITS export needs norm
        self.view.addBtn.setEnabled.assert_called_once_with(True)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.has_stack")
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.normalise_issue")
    def test_WHEN_has_stack_has_good_norm_THEN_buttons_set(self, normalise_issue, has_stack):
        has_stack.return_value = True
        normalise_issue.return_value = ""
        self.view.normalisation_enabled.return_value = True
        self.presenter.handle_button_enabled()
        self.view.exportButton.setEnabled.assert_called_once_with(True)
        self.view.exportButtonRITS.setEnabled.assert_called_once_with(True)
        self.view.addBtn.setEnabled.assert_called_once_with(True)

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

    def test_WHEN_show_sample_call_THEN_add_range_set(self):
        self.presenter.model.tof_range = (0, 9)
        self.presenter.show_new_sample()
        self.view.spectrum.add_range.assert_called_once_with(0, 9)

    def test_gui_changes_tof_range(self):
        image_stack = generate_images([30, 11, 12])
        new_tof_range = (10, 20)
        self.presenter.model.set_stack(image_stack)
        self.presenter.handle_range_slide_moved(new_tof_range)

        self.assertEqual(self.presenter.model.tof_range, new_tof_range)

    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_csv")
    def test_handle_export_csv_none(self, mock_save_csv: mock.Mock):
        self.view.get_csv_filename = mock.Mock(return_value=None)

        self.presenter.handle_export_csv()

        self.view.get_csv_filename.assert_called_once()
        mock_save_csv.assert_not_called()

    @parameterized.expand(["/fake/path", "/fake/path.csv"])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_csv")
    def test_handle_export_csv(self, path_name: str, mock_save_csv: mock.Mock):
        self.view.get_csv_filename = mock.Mock(return_value=Path(path_name))

        self.presenter.model.set_stack(generate_images())

        self.presenter.handle_export_csv()

        self.view.get_csv_filename.assert_called_once()
        mock_save_csv.assert_called_once_with(Path("/fake/path.csv"), False)

    @parameterized.expand(["/fake/path", "/fake/path.dat"])
    @mock.patch("mantidimaging.gui.windows.spectrum_viewer.model.SpectrumViewerWindowModel.save_rits")
    def test_handle_rits_export(self, path_name: str, mock_save_rits: mock.Mock):
        self.view.get_rits_export_filename = mock.Mock(return_value=Path(path_name))
        self.view.transmission_error_mode = "Standard Deviation"

        self.presenter.model.set_stack(generate_images())

        self.presenter.handle_rits_export()

        self.view.get_rits_export_filename.assert_called_once()
        mock_save_rits.assert_called_once_with(Path("/fake/path.dat"), False, ErrorMode.STANDARD_DEVIATION)

    def test_WHEN_do_add_roi_called_THEN_new_roi_added(self):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi"], self.presenter.model.get_list_of_roi_names())
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi", "roi_1"], self.presenter.model.get_list_of_roi_names())

    def test_WHEN_do_add_roi_to_table_called_THEN_roi_added_to_table(self):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.view.add_roi_table_row.assert_called_once_with("roi", mock.ANY)
        self.view.add_roi_table_row.reset_mock()

        self.assertEqual(["all", "roi"], self.presenter.model.get_list_of_roi_names())
        self.presenter.view.spectrum.roi_dict = {"roi_1": mock.Mock()}
        self.presenter.do_add_roi_to_table("roi_1")
        self.view.add_roi_table_row.assert_called_once_with("roi_1", mock.ANY)

    def test_WHEN_do_remove_roi_called_THEN_roi_removed(self):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi", "roi_1"], self.presenter.model.get_list_of_roi_names())
        self.presenter.do_remove_roi("roi_1")
        self.assertEqual(["all", "roi"], self.presenter.model.get_list_of_roi_names())

    def test_WHEN_ROI_renamed_THEN_roi_renamed(self):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi", "roi_1"], self.presenter.model.get_list_of_roi_names())
        self.presenter.rename_roi("roi_1", "imaging_is_the_best")
        self.assertEqual(["all", "roi", "imaging_is_the_best"], self.presenter.model.get_list_of_roi_names())

    def test_WHEN_default_ROI_renamed_THEN_default_roi_renamed(self):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi", "roi_1"], self.presenter.model.get_list_of_roi_names())
        self.presenter.rename_roi("roi", "imaging_is_the_best")
        self.assertEqual(["all", "roi_1", "imaging_is_the_best"], self.presenter.model.get_list_of_roi_names())

    @parameterized.expand(["all", "roi"])
    def test_WHEN_ROI_renamed_to_existing_name_THEN_runtimeerror(self, name):
        self.presenter.model.set_stack(generate_images())
        self.presenter.do_add_roi()
        self.assertEqual(["all", "roi"], self.presenter.model.get_list_of_roi_names())
        with self.assertRaises(KeyError):
            self.presenter.rename_roi("roi", name)
        self.assertEqual(["all", "roi"], self.presenter.model.get_list_of_roi_names())

    def test_WHEN_do_remove_roi_called_with_no_arguments_THEN_all_rois_removed(self):
        self.presenter.model.set_stack(generate_images())
        for _ in range(3):
            self.presenter.do_add_roi()
        self.assertEqual(["all", "roi", "roi_1", "roi_2"], self.presenter.model.get_list_of_roi_names())
        self.presenter.do_remove_roi()
        self.assertEqual([], self.presenter.model.get_list_of_roi_names())
