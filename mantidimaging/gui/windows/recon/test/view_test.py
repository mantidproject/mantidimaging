# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from PyQt5.QtWidgets import QWidget

from mantidimaging.core.net.help_pages import SECTION_USER_GUIDE
from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees, Slope
from mantidimaging.gui.utility.qt_helpers import INPUT_DIALOG_FLAGS
from mantidimaging.gui.windows.recon import ReconstructWindowView
from mantidimaging.gui.windows.recon.presenter import AutoCorMethod, Notifications
from mantidimaging.test_helpers import start_qapplication


class MockMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.stack_changed = mock.Mock()
        self.model_changed = mock.Mock()
        self.model_changed = mock.Mock()
        self.presenter = mock.Mock(datasets=dict())


@start_qapplication
class ReconstructWindowViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.main_window = MockMainWindow()
        self.view = ReconstructWindowView(self.main_window)

        self.view.presenter = self.presenter = mock.Mock()
        self.view.image_view = self.image_view = mock.Mock()
        self.view.tableView = self.tableView = mock.Mock()
        self.view.autoFindMethod = self.autoFindMethod = mock.Mock()

    @mock.patch("mantidimaging.gui.windows.recon.view.QMessageBox")
    def test_check_stack_for_invalid_180_deg_proj_when_proj_180_degree_shape_matches_images_is_false(
            self, qmessagebox_mock):
        self.main_window.get_images_from_stack_uuid = mock.Mock()
        selected_images = self.main_window.get_images_from_stack_uuid.return_value
        selected_images.has_proj180deg.return_value = True
        self.presenter.proj_180_degree_shape_matches_images.return_value = False

        uuid = mock.Mock()
        self.view.check_stack_for_invalid_180_deg_proj(uuid)
        self.main_window.get_images_from_stack_uuid.assert_called_once_with(uuid)
        self.presenter.proj_180_degree_shape_matches_images.assert_called_once_with(selected_images)
        qmessagebox_mock.warning.assert_called_once_with(
            self.view, "Potential Failure",
            "The shapes of the selected stack and it's 180 degree projections do not match! This is going to cause an "
            "error when calculating the COR. Fix the shape before continuing!")

    @mock.patch("mantidimaging.gui.windows.recon.view.QMessageBox")
    def test_check_stack_for_invalid_180_deg_proj_when_proj_180_degree_shape_matches_images_is_true(
            self, qmessagebox_mock):
        self.main_window.get_images_from_stack_uuid = mock.Mock()
        selected_images = self.main_window.get_images_from_stack_uuid.return_value
        selected_images.has_proj180deg.return_value = True
        self.presenter.proj_180_degree_shape_matches_images.return_value = True

        uuid = mock.Mock()
        self.view.check_stack_for_invalid_180_deg_proj(uuid)
        self.main_window.get_images_from_stack_uuid.assert_called_once_with(uuid)
        self.presenter.proj_180_degree_shape_matches_images.assert_called_once_with(selected_images)
        qmessagebox_mock.warning.assert_not_called()

    def test_remove_selected_cor(self):
        assert self.view.remove_selected_cor() == self.tableView.removeSelectedRows.return_value

    def test_clear_cor_table(self):
        assert self.view.clear_cor_table() == self.tableView.model.return_value.removeAllRows.return_value

    def test_cleanup(self):
        self.view.stackSelector = stack_selector_mock = mock.Mock()

        self.view.cleanup()
        stack_selector_mock.unsubscribe_from_main_window.assert_called_once()
        assert self.main_window.recon is None

    @mock.patch("mantidimaging.gui.windows.recon.view.CorTiltPointQtModel")
    def test_cor_table_model_when_model_is_none(self, cortiltpointqtmodel_mock):
        self.tableView.model.return_value = None
        mdl = cortiltpointqtmodel_mock.return_value

        assert self.view.cor_table_model == self.tableView.model.return_value
        cortiltpointqtmodel_mock.assert_called_once_with(self.tableView)
        self.tableView.setModel.assert_called_once_with(mdl)

    @mock.patch("mantidimaging.gui.windows.recon.view.CorTiltPointQtModel")
    def test_cor_table_model_when_model_is_not_none(self, cortiltpointqtmodel_mock):
        assert self.view.cor_table_model == self.tableView.model.return_value
        cortiltpointqtmodel_mock.assert_not_called()
        self.tableView.setModel.assert_not_called()

    def test_cor_table_model_selected_rows(self):
        mock_row = mock.Mock(row=mock.Mock(return_value=1))
        mock_selection_model = mock.Mock(selectedRows=lambda: [mock_row, mock_row])
        self.tableView.selectionModel = mock.Mock(return_value=mock_selection_model)

        ret = self.view.get_cor_table_selected_rows()

        self.assertEqual(ret, [1, 1])

    def test_set_results(self):
        cor_val = 20
        tilt_val = 30
        slope_val = 40
        cor = ScalarCoR(cor_val)
        tilt = Degrees(tilt_val)
        slope = Slope(slope_val)

        with mock.patch.object(self.image_view, "set_tilt") as set_tilt:
            self.view.set_results(cor, tilt, slope)
            self.assertEqual(self.view.rotation_centre, cor_val)
            self.assertEqual(self.view.tilt, tilt_val)
            self.assertEqual(self.view.slope, slope_val)
            set_tilt.assert_called_once_with(tilt)

    def test_preview_image_on_button_press(self):
        event_mock = mock.Mock()
        event_mock.button = 1
        event_mock.ydata = ydata = 20.3

        self.view.preview_image_on_button_press(event_mock)
        self.presenter.set_preview_slice_idx.assert_called_once_with(int(ydata))

    def test_no_preview_image_on_button_press(self):
        event_mock = mock.Mock()
        event_mock.button = 2
        event_mock.ydata = 20.3

        self.view.preview_image_on_button_press(event_mock)
        self.presenter.set_preview_slice_idx.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.recon.view.QSignalBlocker")
    def test_update_projection(self, _):
        image_data = mock.Mock()
        preview_slice_idx = 13
        tilt_angle = Degrees(30)

        self.view.previewSliceIndex = preview_slice_index_mock = mock.Mock()
        self.view.update_projection(image_data, preview_slice_idx, tilt_angle)

        preview_slice_index_mock.setValue.assert_called_once_with(preview_slice_idx)
        self.image_view.update_projection.assert_called_once_with(image_data, preview_slice_idx, tilt_angle)

    def test_update_sinogram(self):
        image_data = mock.Mock()
        self.view.update_sinogram(image_data)
        self.image_view.update_sinogram.assert_called_once_with(image_data)

    def test_update_recon_preview_no_hist(self):
        image_data = mock.Mock()
        self.view.update_recon_hist_needed = False

        self.view.update_recon_preview(image_data)
        self.image_view.update_recon.assert_called_once_with(image_data, False)

    def test_update_recon_preview_and_hist(self):
        image_data = mock.Mock()
        self.view.update_recon_hist_needed = True

        self.view.update_recon_preview(image_data)
        self.image_view.update_recon.assert_called_once_with(image_data, False)
        self.image_view.update_recon_hist.assert_called_once_with()

    def test_reset_recon_and_sino_previews(self):
        self.view.reset_recon_and_sino_previews()
        self.image_view.clear_recon.assert_called_once()
        self.image_view.clear_sinogram.assert_called_once()

    def test_reset_slice_and_tilt(self):
        slice_index = 5
        self.view.reset_slice_and_tilt(slice_index)
        self.image_view.reset_slice_and_tilt.assert_called_once_with(slice_index)

    def test_on_table_row_count_change(self):
        self.tableView.model.return_value.empty = empty = False
        self.view.removeBtn = remove_button_mock = mock.Mock()
        self.view.clearAllBtn = clear_all_button_mock = mock.Mock()
        self.view.on_table_row_count_change()

        remove_button_mock.setEnabled.assert_called_once_with(not empty)
        clear_all_button_mock.setEnabled.assert_called_once_with(not empty)

    def test_add_cor_table_row(self):
        row = 3
        slice_index = 4
        cor = 5.0

        self.view.add_cor_table_row(row, slice_index, cor)

        self.tableView.model.return_value.appendNewRow.assert_called_once_with(row, slice_index, cor)
        self.tableView.selectRow.assert_called_once_with(row)

    def test_rotation_centre_property(self):
        self.assertEqual(self.view.rotation_centre, 0)

    def test_tilt_property(self):
        self.assertEqual(self.view.tilt, 0)

    def test_slope_property(self):
        self.assertEqual(self.view.slope, 0)

    def test_max_proj_angle(self):
        self.assertEqual(self.view.max_proj_angle, 360)

    def test_algorithm_name(self):
        self.assertIn(self.view.algorithm_name, ["gridrec", "FBP_CUDA"])

    def test_filter_name(self):
        self.assertIn(self.view.filter_name, ["ramlak", "ram-lak"])

    def test_num_iter_property(self):
        self.assertEqual(self.view.num_iter, 1)

    def test_stochastic_property(self):
        self.assertEqual(self.view.stochastic, False)

    def test_subsets_property(self):
        self.assertEqual(self.view.subsets, 1)

    def test_num_iter_setter(self):
        iters = 123
        self.view.num_iter = iters
        self.assertEqual(self.view.num_iter, iters)

    def test_pixel_size_property(self):
        self.assertEqual(self.view.pixel_size, 0)

    @mock.patch("mantidimaging.gui.windows.recon.view.QSignalBlocker")
    def test_pixel_size_setter(self, _):
        value = 123
        self.view.pixel_size = value
        self.assertEqual(self.view.pixel_size, value)

    def test_recon_params(self):
        rp = self.view.recon_params()
        self.assertIn(rp.algorithm, self.view.algorithm_name)
        self.assertEqual(rp.num_iter, self.view.num_iter)
        self.assertEqual(rp.alpha, self.view.alpha)
        self.assertEqual(rp.non_negative, self.view.non_negative)
        self.assertEqual(rp.stochastic, self.view.stochastic)
        self.assertEqual(rp.subsets, self.view.subsets)

    def test_set_table_point(self):
        idx = 12
        slice_idx = 34
        cor = 12.34

        self.view.set_table_point(idx, slice_idx, cor)
        self.tableView.model.return_value.set_point.assert_called_once_with(idx, slice_idx, cor, reset_results=False)

    def test_show_recon_volume(self):
        data = mock.Mock()
        self.main_window.add_recon_to_dataset = add_to_dataset_mock = mock.Mock()
        stack_id = "id"
        self.view.show_recon_volume(data, stack_id)
        add_to_dataset_mock.assert_called_once_with(data, stack_id)

    def test_get_stack_when_uuid_is_none(self):
        assert self.view.get_stack(None) is None

    def test_get_stack_when_uuid_is_not_none(self):
        uuid = mock.Mock()
        self.main_window.get_stack = mock.Mock()

        assert self.view.get_stack(uuid) == self.main_window.get_stack.return_value
        self.main_window.get_stack.assert_called_once_with(uuid)

    def test_hide_tilt(self):
        self.view.hide_tilt()
        self.image_view.hide_tilt.assert_called_once()

    def test_set_filters_for_recon_tool(self):
        filters = ["abc" for _ in range(3)]
        with mock.patch.object(self.view, "filterName") as fn:
            self.view.set_filters_for_recon_tool(filters)
            fn.clear.assert_called_once()
            fn.insertItems.assert_called_once_with(0, filters)

    @mock.patch("mantidimaging.gui.windows.recon.view.QInputDialog")
    def test_get_number_of_cors_when_accepted_is_true(self, qinputdialog_mock):
        num = 2
        accepted = True
        qinputdialog_mock.getInt.return_value = (num, accepted)

        assert self.view.get_number_of_cors() == num
        qinputdialog_mock.getInt.assert_called_once_with(self.view,
                                                         "Number of slices",
                                                         "On how many slices to run the automatic CoR finding?",
                                                         value=6,
                                                         min=2,
                                                         max=30,
                                                         step=1,
                                                         flags=INPUT_DIALOG_FLAGS)

    @mock.patch("mantidimaging.gui.windows.recon.view.QInputDialog")
    def test_get_number_of_cors_when_accepted_is_false(self, qinputdialog_mock):
        num = 2
        accepted = False
        qinputdialog_mock.getInt.return_value = (num, accepted)

        assert self.view.get_number_of_cors() is None
        qinputdialog_mock.getInt.assert_called_once_with(self.view,
                                                         "Number of slices",
                                                         "On how many slices to run the automatic CoR finding?",
                                                         value=6,
                                                         min=2,
                                                         max=30,
                                                         step=1,
                                                         flags=INPUT_DIALOG_FLAGS)

    def test_get_auto_cor_method_when_current_is_correlation(self):
        self.autoFindMethod.currentText.return_value = "Correlation"
        assert self.view.get_auto_cor_method() == AutoCorMethod.CORRELATION

    def test_get_auto_cor_method_when_current_is_not_correlation(self):
        self.autoFindMethod.currentText.return_value = "NotCorrelation"
        assert self.view.get_auto_cor_method() == AutoCorMethod.MINIMISATION_SQUARE_SUM

    def test_set_correlate_buttons_enables(self):
        self.view.correlateBtn = correlate_button_mock = mock.Mock()
        self.view.minimiseBtn = minimise_button_mock = mock.Mock()

        for enabled in [True, False]:
            with self.subTest(enabled=enabled):
                self.view.set_correlate_buttons_enabled(enabled)
                correlate_button_mock.setEnabled.assert_called_once_with(enabled)
                minimise_button_mock.setEnabled.assert_called_once_with(enabled)
            if enabled:
                correlate_button_mock.reset_mock()
                minimise_button_mock.reset_mock()

    @mock.patch("mantidimaging.gui.windows.recon.view.open_help_webpage")
    def test_open_help_webpage_when_no_exception(self, open_help_webpage_mock):
        page = "page"
        self.view.open_help_webpage(page)
        open_help_webpage_mock.assert_called_once_with(SECTION_USER_GUIDE, page)

    @mock.patch("mantidimaging.gui.windows.recon.view.open_help_webpage")
    def test_open_help_webpage_when_exception(self, open_help_webpage_mock):
        page = "page"
        open_help_webpage_mock.side_effect = RuntimeError
        self.view.show_error_dialog = show_error_dialog_mock = mock.Mock()
        self.view.open_help_webpage(page)
        open_help_webpage_mock.assert_called_once_with(SECTION_USER_GUIDE, page)
        show_error_dialog_mock.assert_called_once_with(str(RuntimeError()))

    def test_change_refine_iterations_when_algorithm_name_is_sirt(self):
        self.view.refineIterationsBtn = refine_iterations_button_mock = mock.Mock()
        self.view.algorithmName = mock.Mock()
        self.view.algorithmName.currentText.return_value = "SIRT_CUDA"

        self.view.change_refine_iterations()
        refine_iterations_button_mock.setEnabled.assert_called_once_with(True)

    def test_change_refine_iterations_when_algorithm_name_is_not_sirt(self):
        self.view.refineIterationsBtn = refine_iterations_button_mock = mock.Mock()
        self.view.algorithmName = mock.Mock()
        self.view.algorithmName.currentText.return_value = "FBP_CUDA"

        self.view.change_refine_iterations()
        refine_iterations_button_mock.setEnabled.assert_called_once_with(False)

    def test_set_recon_buttons_enabled(self):
        def assert_button_state_is_correct(is_enabled):
            self.assertEqual(self.view.reconstructSlice.isEnabled(), is_enabled)
            self.assertEqual(self.view.reconstructVolume.isEnabled(), is_enabled)

        assert_button_state_is_correct(is_enabled=True)

        self.view.set_recon_buttons_enabled(False)
        assert_button_state_is_correct(is_enabled=False)

        self.view.set_recon_buttons_enabled(True)
        assert_button_state_is_correct(is_enabled=True)

    def test_WHEN_stochastic_ticked_THEN_subsets_enabled(self):
        self.assertFalse(self.view.subsetsSpinBox.isEnabled())
        self.assertFalse(self.view.subsetsLabel.isEnabled())

        self.view.stochasticCheckBox.setChecked(True)
        self.assertTrue(self.view.subsetsSpinBox.isEnabled())
        self.assertTrue(self.view.subsetsLabel.isEnabled())

        self.view.stochasticCheckBox.setChecked(False)
        self.assertFalse(self.view.subsetsSpinBox.isEnabled())
        self.assertFalse(self.view.subsetsLabel.isEnabled())

    def test_WHEN_param_change_THEN_preview_called(self):
        for func, val in [
            (self.view.numIter.setValue, 2),
            (self.view.alphaSpinBox.setValue, 2),
            (self.view.stochasticCheckBox.setChecked, True),
            (self.view.subsetsSpinBox.setValue, 2),
        ]:
            self.presenter.notify.reset_mock()
            func(val)
            self.presenter.notify.assert_called_once_with(Notifications.RECONSTRUCT_PREVIEW_SLICE)
