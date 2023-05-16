# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import traceback
from enum import Enum, auto
from functools import partial
from logging import getLogger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Callable, Set

import numpy as np
from PyQt5.QtWidgets import QWidget

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees
from mantidimaging.gui.dialogs.async_task import start_async_task_view, TaskWorkerThread
from mantidimaging.gui.dialogs.cor_inspection.view import CORInspectionDialogView
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility.qt_helpers import BlockQtSignals
from mantidimaging.gui.windows.recon.model import ReconstructWindowModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.recon.view import ReconstructWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView


class AutoCorMethod(Enum):
    CORRELATION = auto()
    MINIMISATION_SQUARE_SUM = auto()


class Notifications(Enum):
    RECONSTRUCT_VOLUME = auto()
    RECONSTRUCT_PREVIEW_SLICE = auto()
    RECONSTRUCT_PREVIEW_USER_CLICK = auto()
    RECONSTRUCT_STACK_SLICE = auto()
    RECONSTRUCT_USER_CLICK = auto()
    COR_FIT = auto()
    CLEAR_ALL_CORS = auto()
    REMOVE_SELECTED_COR = auto()
    CALCULATE_CORS_FROM_MANUAL_TILT = auto()
    ALGORITHM_CHANGED = auto()
    UPDATE_PROJECTION = auto()
    ADD_COR = auto()
    REFINE_COR = auto()
    REFINE_ITERS = auto()
    AUTO_FIND_COR_CORRELATE = auto()
    AUTO_FIND_COR_MINIMISE = auto()


class ReconstructWindowPresenter(BasePresenter):
    ERROR_STRING = "COR/Tilt finding failed: {}"
    view: 'ReconstructWindowView'

    def __init__(self, view: 'ReconstructWindowView', main_window: 'MainWindowView'):
        super().__init__(view)
        self.view = view
        self.model = ReconstructWindowModel(self.view.cor_table_model)
        self.allowed_recon_kwargs: Dict[str, List[str]] = self.model.load_allowed_recon_kwargs()
        self.restricted_arg_widgets: Dict[str, List[QWidget]] = {
            'filter_name': [self.view.filterName, self.view.filterNameLabel],
            'num_iter': [self.view.numIter, self.view.numIterLabel],
            'alpha': [self.view.alphaSpinBox, self.view.alphaLabel],
            'non_negative': [self.view.nonNegativeCheckBox, self.view.nonNegativeLabel],
            'stochastic': [self.view.stochasticCheckBox, self.view.stochasticLabel],
            'projections_per_subset': [self.view.subsetsSpinBox, self.view.subsetsLabel],
        }
        self.main_window = main_window

        self.recon_is_running = False
        self.async_tracker: Set[Any] = set()

        self.main_window.stack_changed.connect(self.handle_stack_changed)
        self.stack_changed_pending = False
        self.stack_selection_change_pending = False

    def notify(self, notification, slice_idx=None):
        try:
            if notification == Notifications.RECONSTRUCT_VOLUME:
                self.do_reconstruct_volume()
            elif notification == Notifications.RECONSTRUCT_PREVIEW_SLICE:
                self.do_preview_reconstruct_slice()
            elif notification == Notifications.RECONSTRUCT_PREVIEW_USER_CLICK:
                self.do_preview_reconstruct_slice(force_update=True)
            elif notification == Notifications.RECONSTRUCT_STACK_SLICE:
                self.do_stack_reconstruct_slice()
            elif notification == Notifications.RECONSTRUCT_USER_CLICK:
                self.do_preview_reconstruct_slice(slice_idx=slice_idx)
            elif notification == Notifications.COR_FIT:
                self.do_cor_fit()
            elif notification == Notifications.CLEAR_ALL_CORS:
                self.do_clear_all_cors()
            elif notification == Notifications.REMOVE_SELECTED_COR:
                self.do_remove_selected_cor()
            elif notification == Notifications.CALCULATE_CORS_FROM_MANUAL_TILT:
                self.do_calculate_cors_from_manual_tilt()
            elif notification == Notifications.ALGORITHM_CHANGED:
                self.do_algorithm_changed()
            elif notification == Notifications.UPDATE_PROJECTION:
                self.do_update_projection()
            elif notification == Notifications.ADD_COR:
                self.do_add_cor()
            elif notification == Notifications.REFINE_COR:
                self._do_refine_selected_cor()
            elif notification == Notifications.REFINE_ITERS:
                self._do_refine_iterations()
            elif notification == Notifications.AUTO_FIND_COR_CORRELATE:
                self._auto_find_correlation()
            elif notification == Notifications.AUTO_FIND_COR_MINIMISE:
                self._auto_find_minimisation_square_sum()
        except Exception as err:
            self.show_error(err, traceback.format_exc())

    def do_algorithm_changed(self):
        alg_name = self.view.algorithm_name
        allowed_args = self.allowed_recon_kwargs[alg_name]
        for arg, widgets in self.restricted_arg_widgets.items():
            if arg in allowed_args:
                for widget in widgets:
                    widget.show()
            else:
                for widget in widgets:
                    widget.hide()
        with BlockQtSignals([self.view.filterName, self.view.numIter]):
            self.view.set_filters_for_recon_tool(self.model.get_allowed_filters(alg_name))
        self.do_preview_reconstruct_slice()
        self.view.change_refine_iterations()

    def set_stack_uuid(self, uuid):
        if not self.view.isVisible():
            self.stack_selection_change_pending = True
            return

        images = self.view.get_stack(uuid)
        if self.model.is_current_stack(uuid):
            return

        self.view.reset_recon_and_sino_previews()
        self.view.clear_cor_table()
        self.model.initial_select_data(images)
        self.view.rotation_centre = self.model.last_cor.value
        self.view.pixel_size = self.get_pixel_size_from_images()
        self.do_update_projection()
        self.view.update_recon_hist_needed = True
        if images is None:
            self.view.reset_recon_line_profile()
            self.view.show_status_message("")
            return
        self._set_max_preview_indexes()
        self.do_preview_reconstruct_slice(reset_roi=True)
        self._do_nan_zero_negative_check()

    def _set_max_preview_indexes(self):
        images = self.model.images
        if images is not None:
            self.view.set_max_projection_index(images.num_projections - 1)
            self.view.set_max_slice_index(images.height - 1)

    def set_preview_projection_idx(self, idx):
        self.model.preview_projection_idx = idx
        self.do_update_projection()

    def set_preview_slice_idx(self, idx):
        self.model.preview_slice_idx = idx
        self.do_update_projection()
        self.do_preview_reconstruct_slice()

    def set_row(self, row):
        self.model.selected_row = row

    def get_pixel_size_from_images(self):
        if self.model.images is not None and self.model.images.pixel_size is not None:
            return self.model.images.pixel_size
        else:
            return 0.

    def do_update_projection(self):
        images = self.model.images
        if images is None:
            self.view.reset_projection_preview()
            return
        img_data = images.projection(self.model.preview_projection_idx)
        self.view.update_projection(img_data, self.model.preview_slice_idx, self.model.tilt_angle)

    def handle_stack_changed(self):
        if self.view.isVisible():
            self.model.reset_cor_model()
            self.do_update_projection()
            self._set_max_preview_indexes()
            self.do_preview_reconstruct_slice(reset_roi=True)
        else:
            self.stack_changed_pending = True

    def _find_next_free_slice_index(self) -> int:
        slice_index = self.model.preview_slice_idx
        max_slice = self.model.images.height
        column = self.view.cor_table_model.getColumn(0)

        for index in range(slice_index + 1, max_slice):
            if index not in column:
                return index

        for index in range(0, slice_index):
            if index not in column:
                return index

        raise RuntimeError("No free slice indexes to add to the COR Table")

    def do_add_cor(self):
        row = self.model.selected_row
        cor = self.model.get_me_a_cor()
        slice_index = self._find_next_free_slice_index()
        self.view.add_cor_table_row(row, slice_index, cor.value)

    def do_reconstruct_volume(self):
        if not self.model.has_results:
            raise ValueError("Fit is not performed on the data, therefore the CoR cannot be found for each slice.")

        self.recon_is_running = True
        self.view.set_recon_buttons_enabled(False)
        start_async_task_view(self.view,
                              self.model.run_full_recon,
                              self._on_volume_recon_done, {'recon_params': self.view.recon_params()},
                              tracker=self.async_tracker)

    def _get_reconstruct_slice(self, cor, slice_idx: int, call_back: Callable[[TaskWorkerThread], None]) -> None:
        # If no COR is provided and there are regression results then calculate
        # the COR for the selected preview slice
        cor = self.model.get_me_a_cor(cor)
        start_async_task_view(self.view,
                              self.model.run_preview_recon,
                              call_back, {
                                  'slice_idx': slice_idx,
                                  'cor': cor,
                                  'recon_params': self.view.recon_params()
                              },
                              tracker=self.async_tracker)

    def _get_slice_index(self, slice_idx: Optional[int]) -> int:
        if slice_idx is None:
            slice_idx = self.model.preview_slice_idx
        else:
            self.model.preview_slice_idx = slice_idx
        return slice_idx

    def do_preview_reconstruct_slice(self,
                                     cor=None,
                                     slice_idx: Optional[int] = None,
                                     force_update: bool = False,
                                     reset_roi: bool = False):
        if self.model.images is None:
            self.view.reset_recon_and_sino_previews()
            return

        slice_idx = self._get_slice_index(slice_idx)
        self.view.update_sinogram(self.model.images.sino(slice_idx))
        if self.view.is_auto_update_preview() or force_update:
            on_preview_complete = partial(self._on_preview_reconstruct_slice_done, reset_roi=reset_roi)
            self._get_reconstruct_slice(cor, slice_idx, on_preview_complete)

    def _on_preview_reconstruct_slice_done(self, task: TaskWorkerThread, reset_roi: bool = False):
        if task.error is not None:
            self.view.show_error_dialog(f"Encountered error while trying to reconstruct: {str(task.error)}")
            return

        images: ImageStack = task.result
        if images is not None:
            # We copy the preview data out of shared memory when passing it into update_recon_preview so that it
            # will still be available after this function ends
            self.view.update_recon_preview(np.copy(images.data[0]), reset_roi)

    def do_stack_reconstruct_slice(self, cor=None, slice_idx: Optional[int] = None):
        self.view.set_recon_buttons_enabled(False)
        slice_idx = self._get_slice_index(slice_idx)
        self._get_reconstruct_slice(cor, slice_idx, self._on_stack_reconstruct_slice_done)

    def _on_stack_reconstruct_slice_done(self, task: TaskWorkerThread):
        if task.error is not None:
            self.view.show_error_dialog(f"Encountered error while trying to reconstruct: {str(task.error)}")
            self.view.set_recon_buttons_enabled(True)
            return

        try:
            images: ImageStack = task.result
            slice_idx = self._get_slice_index(None)
            if images is not None:
                assert self.model.images is not None
                images.name = "Recon"
                self._replace_inf_nan(images)  # pyqtgraph workaround
                self.view.show_recon_volume(images, self.model.stack_id)
                images.record_operation('AstraRecon.single_sino',
                                        'Slice Reconstruction',
                                        slice_idx=slice_idx,
                                        **self.view.recon_params().to_dict())
        finally:
            self.view.set_recon_buttons_enabled(True)

    def _do_refine_selected_cor(self):
        selected_rows = self.view.get_cor_table_selected_rows()
        if len(selected_rows):
            slice_idx = self.model.slices[selected_rows[0]]
        else:
            raise ValueError("No slice selected in COR table")

        dialog = CORInspectionDialogView(self.view, self.model.images, slice_idx, self.model.last_cor,
                                         self.view.recon_params(), False)

        res = dialog.exec()
        dialog.deleteLater()
        LOG.debug('COR refine dialog result: {}'.format(res))
        if res == CORInspectionDialogView.Accepted:
            new_cor = dialog.optimal_rotation_centre
            LOG.debug('New optimal rotation centre: {}'.format(new_cor))
            self.model.data_model.set_cor_at_slice(slice_idx, new_cor.value)
            self.model.last_cor = new_cor
            # Update reconstruction preview with new COR
            self.set_preview_slice_idx(slice_idx)

    def _do_refine_iterations(self):
        slice_idx = self.model.preview_slice_idx

        dialog = CORInspectionDialogView(self.view, self.model.images, slice_idx, self.model.last_cor,
                                         self.view.recon_params(), True)

        res = dialog.exec()
        LOG.debug('COR refine iteration result: {}'.format(res))
        if res == CORInspectionDialogView.Accepted:
            new_iters = dialog.optimal_iterations
            LOG.debug('New optimal iterations: {}'.format(new_iters))
            self.view.num_iter = new_iters

    def do_cor_fit(self):
        self.model.do_fit()
        self.view.set_results(*self.model.get_results())
        self.do_update_projection()
        self.do_preview_reconstruct_slice()

    def _on_volume_recon_done(self, task):
        self.recon_is_running = False
        if task.error is not None:
            self.view.show_error_dialog(f"Encountered error while trying to reconstruct: {str(task.error)}")
            self.view.set_recon_buttons_enabled(True)
            return

        try:
            self._replace_inf_nan(task.result)  # pyqtgraph workaround
            assert self.model.images is not None
            task.result.name = "Recon"
            self.view.show_recon_volume(task.result, self.model.stack_id)
        finally:
            self.view.set_recon_buttons_enabled(True)

    def do_clear_all_cors(self):
        self.view.clear_cor_table()
        self.model.reset_selected_row()

    def do_remove_selected_cor(self):
        self.view.remove_selected_cor()

    def set_last_cor(self, cor):
        self.model.last_cor = ScalarCoR(cor)

    def do_calculate_cors_from_manual_tilt(self):
        cor = ScalarCoR(self.view.rotation_centre)
        tilt = Degrees(self.view.tilt)
        self._set_precalculated_cor_tilt(cor, tilt)

    def _set_precalculated_cor_tilt(self, cor: ScalarCoR, tilt: Degrees):
        self.model.set_precalculated(cor, tilt)
        self.view.set_results(*self.model.get_results())
        for idx, point in enumerate(self.model.data_model.iter_points()):
            self.view.set_table_point(idx, point.slice_index, point.cor)
        self.do_update_projection()
        self.do_preview_reconstruct_slice()

    def _auto_find_correlation(self):
        if not self.model.images.has_proj180deg():
            self.view.show_status_message("Unable to correlate 0 and 180 because the dataset doesn't have a 180 "
                                          "projection set. Please load a 180 projection manually.")
            return

        self.recon_is_running = True

        def completed(task: TaskWorkerThread):
            if task.result is None and task.error is not None:
                selected_stack = self.view.main_window.get_images_from_stack_uuid(self.view.stackSelector.current())
                self.view.show_error_dialog(
                    f"Finding the COR failed, likely caused by the selected stack's 180 "
                    f"degree projection being a different shape. \n\n "
                    f"Error: {str(task.error)} "
                    f"\n\n Suggestion: Use crop coordinates to resize the 180 degree projection to "
                    f"({selected_stack.height}, {selected_stack.width})")
            else:
                cor, tilt = task.result
                self._set_precalculated_cor_tilt(cor, tilt)
            self.view.set_correlate_buttons_enabled(True)
            self.recon_is_running = False

        self.view.set_correlate_buttons_enabled(False)
        start_async_task_view(self.view, self.model.auto_find_correlation, completed, tracker=self.async_tracker)

    def _auto_find_minimisation_square_sum(self):
        num_cors = self.view.get_number_of_cors()
        if num_cors is None:
            return

        self.do_clear_all_cors()

        selected_row, slice_indices = self.model.get_slice_indices(num_cors)

        if self.model.has_results:
            initial_cor = []
            for slc in slice_indices:
                initial_cor.append(self.model.data_model.get_cor_from_regression(slc))
        else:
            initial_cor = self.view.rotation_centre

        def _completed_finding_cors(task: TaskWorkerThread):
            if task.error is not None:
                self.view.show_error_dialog(f"Finding the COR failed.\n\n Error: {str(task.error)}")
            else:
                cors = task.result
                for slice_idx, cor in zip(slice_indices, cors):
                    self.view.add_cor_table_row(selected_row, slice_idx, cor)
                self.do_cor_fit()
            self.view.set_correlate_buttons_enabled(True)

        self.view.set_correlate_buttons_enabled(False)
        start_async_task_view(self.view,
                              self.model.auto_find_minimisation_sqsum,
                              _completed_finding_cors, {
                                  'slices': slice_indices,
                                  'recon_params': self.view.recon_params(),
                                  'initial_cor': initial_cor
                              },
                              tracker=self.async_tracker)

    def proj_180_degree_shape_matches_images(self, images):
        return self.model.proj_180_degree_shape_matches_images(images)

    def _do_nan_zero_negative_check(self):
        """
        Checks if the data contains NaNs/zeroes and displays a message if they are found.
        """
        msg_list = []
        if self.model.stack_contains_nans():
            msg_list.append("NaN(s) found in the stack.")
        if self.model.stack_contains_zeroes():
            msg_list.append("Zero(es) found in the stack.")
        if self.model.stack_contains_negative_values():
            msg_list.append("Negative value(s) found in the stack.")

        if len(msg_list) == 0:
            self.view.show_status_message("")
        else:
            msg_list.insert(0, "Warning:")
            self.view.show_status_message(" ".join(msg_list))

    @staticmethod
    def _replace_inf_nan(images: ImageStack):
        """
        Replaces infinity values in a data array with NaNs. Used because pyqtgraph has programs with arrays containing
        inf.
        :param images: The ImageStack object.
        """
        images.data[np.isinf(images.data)] = np.nan
