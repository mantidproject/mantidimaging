# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.rotation.data_model import Point
from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from mantidimaging.gui.windows.recon import ReconstructWindowPresenter, ReconstructWindowView
from mantidimaging.gui.windows.recon.presenter import Notifications as PresNotification
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView

TEST_PIXEL_SIZE = 1443


class ReconWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        # Mock view
        self.make_view()

        self.presenter = ReconstructWindowPresenter(self.view, None)

        # Mock stack
        self.sv_view = mock.create_autospec(StackVisualiserView)

        data = Images(data=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        data.pixel_size = TEST_PIXEL_SIZE
        self.sv_view.presenter = StackVisualiserPresenter(self.sv_view, data)

        self.presenter.model.initial_select_data(self.sv_view)
        self.view.get_stack_visualiser = mock.Mock(return_value=self.sv_view)

        import uuid
        self.uuid = uuid.uuid4()

    def make_view(self):
        self.view = mock.create_autospec(ReconstructWindowView)
        self.view.filterName = mock.Mock()
        self.view.filterNameLabel = mock.Mock()
        self.view.numIter = mock.Mock()
        self.view.numIterLabel = mock.Mock()

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_set_stack_uuid(self, mock_get_reconstructor_for):
        # reset the model data
        self.presenter.model.initial_select_data(None)

        mock_reconstructor = mock.Mock()
        mock_reconstructor.single_sino = mock.Mock()
        mock_reconstructor.single_sino.return_value = np.random.rand(128, 128)
        mock_get_reconstructor_for.return_value = mock_reconstructor

        recon_params = ReconstructionParameters("FBP", "ram-lak", 10)
        self.view.recon_params.return_value = recon_params

        # first-time selecting this data after reset
        self.presenter.set_stack_uuid(self.uuid)
        self.view.get_stack_visualiser.assert_called_once_with(self.uuid)

        self.view.update_projection.assert_called_once()
        self.view.clear_cor_table.assert_called_once()
        self.view.update_projection.assert_called_once()
        self.view.update_sinogram.assert_called_once()
        self.view.update_recon_preview.assert_called_once()
        mock_get_reconstructor_for.assert_called_once()
        mock_reconstructor.single_sino.assert_called_once()
        self.view.recon_params.assert_called_once()

        # calling again with the same stack shouldn't re-do everything
        self.presenter.set_stack_uuid(self.uuid)
        self.assertEqual(self.view.get_stack_visualiser.call_count, 2)
        self.view.get_stack_visualiser.assert_has_calls([mock.call(self.uuid), mock.call(self.uuid)])

        self.view.update_projection.assert_called_once()
        self.view.clear_cor_table.assert_called_once()
        self.view.update_projection.assert_called_once()
        self.view.update_sinogram.assert_called_once()
        self.view.update_recon_preview.assert_called_once()
        mock_get_reconstructor_for.assert_called_once()
        mock_reconstructor.single_sino.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_set_stack_uuid_updates_rotation_centre_and_pixel_size(self, _):
        self.presenter.model.stack = None
        # first-time selecting this data after reset
        self.presenter.set_stack_uuid(self.uuid)

        self.assertEqual(64.0, self.view.rotation_centre)
        self.assertEqual(TEST_PIXEL_SIZE, self.view.pixel_size)

    def test_set_projection_preview_index(self):
        self.presenter.set_preview_projection_idx(5)
        self.assertEqual(self.presenter.model.preview_projection_idx, 5)
        self.view.update_projection.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_set_slice_preview_index(self, mock_get_reconstructor_for):
        mock_reconstructor = mock.Mock()
        mock_reconstructor.single_sino = mock.Mock()
        mock_reconstructor.single_sino.return_value = np.random.rand(128, 128)
        mock_get_reconstructor_for.return_value = mock_reconstructor

        recon_params = ReconstructionParameters("FBP", "ram-lak", 10)
        self.view.recon_params.return_value = recon_params

        self.presenter.set_preview_slice_idx(5)
        self.assertEqual(self.presenter.model.preview_slice_idx, 5)
        self.view.update_projection.assert_called_once()
        self.view.update_sinogram.assert_called_once()
        self.view.update_recon_preview.assert_called_once()
        self.view.recon_params.assert_called_once()

        mock_get_reconstructor_for.assert_called_once()
        mock_reconstructor.single_sino.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.model.ReconstructWindowModel.get_me_a_cor', return_value=ScalarCoR(15))
    def test_do_add_manual_cor_table_row(self, mock_get_me_a_cor):
        self.presenter.model.selected_row = 0
        self.presenter.model.preview_slice_idx = 15

        self.presenter.notify(PresNotification.ADD_COR)
        self.view.add_cor_table_row.assert_called_once_with(self.presenter.model.selected_row, 0, 15)
        mock_get_me_a_cor.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_do_reconstruct_slice(self, mock_get_reconstructor_for):
        mock_reconstructor = mock.Mock()
        mock_reconstructor.single_sino = mock.Mock()
        mock_reconstructor.single_sino.return_value = np.random.rand(128, 128)
        mock_get_reconstructor_for.return_value = mock_reconstructor

        recon_params = ReconstructionParameters("FBP", "ram-lak", 10)
        self.view.recon_params.return_value = recon_params

        self.presenter.model.preview_slice_idx = 0
        self.presenter.model.last_cor = ScalarCoR(150)
        self.presenter.model.data_model._cached_gradient = None

        self.presenter.do_preview_reconstruct_slice()
        self.view.update_sinogram.assert_called_once()
        self.view.update_recon_preview.assert_called_once()
        self.view.recon_params.assert_called_once()

        mock_get_reconstructor_for.assert_called_once()
        mock_reconstructor.single_sino.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_do_reconstruct_slice_raises(self, mock_get_reconstructor_for):
        mock_get_reconstructor_for.side_effect = ValueError
        mock_reconstructor = mock.Mock()
        mock_reconstructor.single_sino = mock.Mock()
        mock_get_reconstructor_for.return_value = mock_reconstructor
        self.presenter.model.preview_slice_idx = 0
        self.presenter.model.last_cor = ScalarCoR(150)
        self.presenter.model.data_model._cached_gradient = None

        self.presenter.do_preview_reconstruct_slice()
        self.view.update_sinogram.assert_called_once()
        self.view.show_error_dialog.assert_called_once()
        mock_get_reconstructor_for.assert_called_once()

        self.view.update_recon_preview.assert_not_called()
        mock_reconstructor.single_sino.assert_not_called()

    @mock.patch('mantidimaging.gui.windows.recon.presenter.start_async_task_view')
    def test_do_reconstruct_volume(self, mock_async_task):
        self.presenter.do_reconstruct_volume()
        # kind of a pointless test, but at least it might capture some parameter change
        mock_async_task.assert_called_once_with(self.view, self.presenter.model.run_full_recon,
                                                self.presenter._on_volume_recon_done,
                                                {'recon_params': self.view.recon_params()})

    @mock.patch('mantidimaging.gui.windows.recon.presenter.CORInspectionDialogView')
    def test_do_refine_selected_cor_declined(self, mock_corview):
        self.presenter.model.preview_slice_idx = 155
        self.presenter.model.last_cor = ScalarCoR(314)
        self.presenter.do_preview_reconstruct_slice = mock.Mock()

        mock_dialog = mock.Mock()
        mock_corview.return_value = mock_dialog

        self.presenter._do_refine_selected_cor()

        mock_corview.assert_called_once()
        mock_dialog.exec.assert_called_once()
        self.presenter.do_preview_reconstruct_slice.assert_not_called()

    @mock.patch('mantidimaging.gui.windows.recon.presenter.CORInspectionDialogView')
    def test_do_refine_selected_cor_accepted(self, mock_corview):
        self.presenter.model.preview_slice_idx = 155
        self.presenter.model.last_cor = ScalarCoR(314)
        self.presenter.do_preview_reconstruct_slice = mock.Mock()
        mock_dialog = mock.Mock()
        mock_dialog.exec.return_value = mock_corview.Accepted
        mock_corview.return_value = mock_dialog

        self.presenter._do_refine_selected_cor()

        self.presenter.model.data_model.set_cor_at_slice.assert_called_once()
        self.assertEqual(self.presenter.model.last_cor, mock_dialog.optimal_rotation_centre)
        mock_corview.assert_called_once()
        mock_dialog.exec.assert_called_once()
        self.presenter.do_preview_reconstruct_slice.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.presenter.CORInspectionDialogView')
    def test_do_refine_iterations_declined(self, mock_corview):
        self.presenter._do_refine_iterations()

        mock_corview.assert_called_once()
        mock_corview.return_value.exec.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.presenter.CORInspectionDialogView')
    def test_do_refine_iterations_accepted(self, mock_corview):
        mock_dialog = mock_corview.return_value
        mock_dialog.exec.return_value = mock_corview.Accepted
        mock_dialog.optimal_iterations = iters = 25

        self.presenter._do_refine_iterations()

        mock_corview.assert_called_once()
        mock_corview.return_value.exec.assert_called_once()
        assert self.view.num_iter == iters

    def test_do_cor_fit(self):
        self.presenter.do_preview_reconstruct_slice = mock.Mock()
        self.presenter.do_update_projection = mock.Mock()

        self.presenter.do_cor_fit()

        self.view.set_results.assert_called_once()
        self.presenter.do_update_projection.assert_called_once()
        self.presenter.do_preview_reconstruct_slice.assert_called_once()

    def test_set_precalculated_cor_tilt(self):
        self.view.rotation_centre = 150
        self.view.tilt = 1
        self.presenter.do_preview_reconstruct_slice = mock.Mock()
        self.presenter.do_update_projection = mock.Mock()
        self.presenter.model.data_model.iter_points.return_value = [Point(0, 0)]

        self.presenter.do_calculate_cors_from_manual_tilt()

        self.presenter.model.data_model.iter_points.assert_called_once()
        self.view.set_table_point.assert_called_once()
        self.assertTrue(self.presenter.model.has_results)
        self.view.set_results.assert_called_once()
        self.presenter.do_update_projection.assert_called_once()
        self.presenter.do_preview_reconstruct_slice.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.recon.presenter.start_async_task_view')
    def test_auto_find_correlation(self, mock_start_async: mock.Mock):
        self.presenter.notify(PresNotification.AUTO_FIND_COR_CORRELATE)
        mock_start_async.assert_called_once()
        mock_first_call = mock_start_async.call_args[0]
        self.assertEqual(self.presenter.view, mock_first_call[0])
        self.assertEqual(self.presenter.model.auto_find_correlation, mock_first_call[1])
        self.view.set_correlate_buttons_enabled.assert_called_once_with(False)

    @mock.patch('mantidimaging.gui.windows.recon.presenter.start_async_task_view')
    def test_auto_find_correlation_failed_due_to_180_deg_shape(self, mock_start_async: mock.MagicMock):
        images = mock.MagicMock()
        images.height = 10
        images.width = 10
        images.proj180deg.height = 20
        images.proj180deg.width = 20
        self.view = mock.MagicMock()
        self.presenter.view = self.view
        self.view.main_window.get_images_from_stack_uuid = mock.MagicMock(return_value=images)

        self.presenter.notify(PresNotification.AUTO_FIND_COR_CORRELATE)

        mock_start_async.assert_called_once()
        completed_function = mock_start_async.call_args[0][2]

        task = mock.MagicMock()
        task.result = None
        task.error = ValueError("Task Error")
        completed_function(task)

        self.view.warn_user.assert_called_once_with(
            "Failure!",
            "Finding the COR failed, likely caused by the selected stack's 180 degree projection being a different "
            "shape. \n\n Error: Task Error \n\n Suggestion: Use crop coordinates to resize the 180 degree "
            "projection to (10, 10)")

    def test_do_stack_reconstruct_slice(self):
        self.presenter._get_reconstruct_slice = mock.Mock()
        self.presenter._get_reconstruct_slice.return_value = test_data = Images(
            np.ndarray(shape=(200, 250), dtype=np.float32))
        test_data.record_operation = mock.Mock()
        slice_idx = 123
        self.presenter.do_stack_reconstruct_slice(slice_idx=slice_idx)
        self.view.show_recon_volume.assert_called_once()
        np.array_equal(self.view.show_recon_volume.call_args[0][0].data, test_data)
        test_data.record_operation.assert_called_once_with('AstraRecon.single_sino',
                                                           'Slice Reconstruction',
                                                           slice_idx=slice_idx,
                                                           **self.view.recon_params().to_dict())

    def test_do_stack_reconstruct_slice_raises(self):
        self.presenter._get_reconstruct_slice = mock.Mock()
        self.presenter._get_reconstruct_slice.side_effect = ValueError
        self.presenter.do_stack_reconstruct_slice()
        self.view.show_recon_volume.assert_not_called()
        self.view.show_error_dialog.assert_called_once()

    def test_proj_180_degree_shape_matches_images_where_they_match(self):
        images = mock.MagicMock()
        images.height = 10
        images.width = 10
        images.proj180deg.height = 10
        images.proj180deg.width = 10
        has_proj180deg = mock.MagicMock(return_value=True)
        images.has_proj180deg = has_proj180deg

        self.assertTrue(self.presenter.proj_180_degree_shape_matches_images(images))

    def test_proj_180_degree_shape_matches_images_where_they_dont_match(self):
        images = mock.MagicMock()
        images.height = 10
        images.width = 10
        images.proj180deg.height = 20
        images.proj180deg.width = 20
        has_proj180deg = mock.MagicMock(return_value=True)
        images.has_proj180deg = has_proj180deg

        self.assertFalse(self.presenter.proj_180_degree_shape_matches_images(images))

    def test_proj_180_degree_shape_matches_images_where_no_180_present(self):
        images = mock.MagicMock()
        has_proj180deg = mock.MagicMock(return_value=False)
        images.has_proj180deg = has_proj180deg

        self.assertFalse(self.presenter.proj_180_degree_shape_matches_images(images))
