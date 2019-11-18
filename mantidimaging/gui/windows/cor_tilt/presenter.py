from typing import TYPE_CHECKING
from enum import Enum
from logging import getLogger

import matplotlib.pyplot as plt

from mantidimaging.core.data import const as data_const
from mantidimaging.gui.dialogs.cor_inspection import CORInspectionDialogView
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.windows.cor_tilt.model import CORTiltWindowModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.cor_tilt.view import CORTiltWindowView


class Notification(Enum):
    CROP_TO_ROI = 1
    UPDATE_PREVIEWS = 2
    RUN_AUTOMATIC = 3
    RUN_MANUAL = 4
    PREVIEW_RECONSTRUCTION = 5
    PREVIEW_RECONSTRUCTION_SET_COR = 6
    ADD_NEW_COR_TABLE_ROW = 7
    REFINE_SELECTED_COR = 8
    SHOW_COR_VS_SLICE_PLOT = 9
    SET_ALL_ROW_VALUES = 10


class CORTiltWindowPresenter(BasePresenter):
    ERROR_STRING = "COR/Tilt finding failed: {}"

    def __init__(self, view: 'CORTiltWindowView', main_window):
        super(CORTiltWindowPresenter, self).__init__(view)
        self.view = view
        self.model = CORTiltWindowModel(self.view.point_model)
        self.main_window = main_window

    def notify(self, signal):
        try:
            if signal == Notification.CROP_TO_ROI:
                self.do_crop_to_roi()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
            elif signal == Notification.RUN_AUTOMATIC:
                self.do_execute_automatic()
            elif signal == Notification.RUN_MANUAL:
                self.do_execute_manual()
            elif signal == Notification.PREVIEW_RECONSTRUCTION:
                self.do_preview_reconstruction()
            elif signal == Notification.PREVIEW_RECONSTRUCTION_SET_COR:
                self.do_preview_reconstruction_set_cor()
            elif signal == Notification.ADD_NEW_COR_TABLE_ROW:
                self.do_add_manual_cor_table_row()
            elif signal == Notification.REFINE_SELECTED_COR:
                self.do_refine_selected_cor()
            elif signal == Notification.SHOW_COR_VS_SLICE_PLOT:
                self.do_plot_cor_vs_slice_index()
            elif signal == Notification.SET_ALL_ROW_VALUES:
                self.change_all_rows_to_selected_cor()

        except Exception as e:
            self.show_error(e)
            LOG.exception("Notification handler failed")

    def set_stack_uuid(self, uuid):
        self.view.reset_image_recon_preview()
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)

    def set_stack(self, stack):
        self.model.initial_select_data(stack)
        self.view.set_results(0, 0, 0)
        self.view.set_num_projections(self.model.num_projections)
        self.view.set_num_slices(self.model.num_slices)
        self.notify(Notification.UPDATE_PREVIEWS)

    def set_preview_projection_idx(self, idx):
        self.model.preview_projection_idx = idx
        self.notify(Notification.UPDATE_PREVIEWS)

    def set_row(self, row):
        self.model.selected_row = row

    def set_preview_slice_idx(self, idx):
        self.model.preview_slice_idx = idx
        self.notify(Notification.UPDATE_PREVIEWS)
        self.notify(Notification.PREVIEW_RECONSTRUCTION)

    def handle_cor_manually_changed(self, slice_idx):
        if slice_idx == self.model.preview_slice_idx:
            self.notify(Notification.PREVIEW_RECONSTRUCTION_SET_COR)

    def do_crop_to_roi(self):
        self.model.update_roi_from_stack()
        self.view.set_results(0, 0, 0)
        self.notify(Notification.UPDATE_PREVIEWS)

    def do_update_previews(self):
        img_data = self.model.sample[self.model.preview_projection_idx] \
            if self.model.sample is not None else None

        self.view.update_image_preview(img_data, self.model.preview_slice_idx, self.model.preview_tilt_line_data,
                                       self.model.roi)

        self.view.update_fit_plot(self.model.slices, self.model.cors, self.model.preview_fit_y_data)

    def do_preview_reconstruction(self, cor=None):
        # If no COR is provided and there are regression results then calculate
        # the COR for the selected preview slice
        if self.model.has_results and cor is None:
            cor = self.model.get_cor_for_slice_from_regression()

        if cor is not None:
            data = self.model.run_preview_recon(self.model.preview_slice_idx, cor)
            self.view.update_image_recon_preview(data)

    def do_preview_reconstruction_set_cor(self):
        cor = self.model.cor_for_current_preview_slice
        self.do_preview_reconstruction(cor)

    def do_add_manual_cor_table_row(self):
        row = self.model.selected_row
        cor = self.model.last_result[data_const.COR_TILT_ROTATION_CENTRE] if \
            self.model.last_result else 0
        self.view.add_cor_table_row(row, self.model.preview_slice_idx, cor)

    def do_refine_selected_cor(self):
        slice_idx = self.model.preview_slice_idx

        dialog = CORInspectionDialogView(self.view, data=self.model.sample, slice_idx=slice_idx)

        res = dialog.exec()
        LOG.debug('COR refine dialog result: {}'.format(res))
        if res == CORInspectionDialogView.Accepted:
            new_cor = dialog.optimal_rotation_centre
            LOG.debug('New optimal rotation centre: {}'.format(new_cor))
            self.model.data_model.set_cor_at_slice(slice_idx, new_cor)

        # Update reconstruction preview with new COR
        self.notify(Notification.PREVIEW_RECONSTRUCTION_SET_COR)

    def do_plot_cor_vs_slice_index(self):
        if self.model.data_model.num_points > 1:
            fig = plt.figure()
            ax = fig.add_subplot(111)

            lines = []
            names = []

            # Add data line
            lines.append(ax.plot(self.model.data_model.slices, self.model.data_model.cors)[0])
            names.append('Data')

            # Add fit line (if a fit has been performed)
            fit_data = self.model.preview_fit_y_data
            if fit_data is not None:
                lines.append(ax.plot(self.model.data_model.slices, fit_data)[0])
                names.append('Fit')

            # Add legend
            ax.legend(lines, names)

            # Set axes labels
            ax.set_xlabel('Slice Index')
            ax.set_ylabel('Rotation Centre')

            plt.show()

    def do_execute_automatic(self):
        self.model.calculate_slices(self.view.slice_count)
        self.model.calculate_projections(self.view.projection_count)

        start_async_task_view(self.view, self.model.run_finding_automatic, self._on_finding_done)

    def do_execute_manual(self):
        start_async_task_view(self.view, self.model.run_finding_manual, self._on_finding_done)

    def _on_finding_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            self.view.set_results(*self.model.get_results())
            self.view.show_results()
            self.notify(Notification.UPDATE_PREVIEWS)
            self.notify(Notification.PREVIEW_RECONSTRUCTION)
        else:
            msg = self.ERROR_STRING.format(task.error)
            log.error(msg)
            self.show_error(msg)

    def change_all_rows_to_selected_cor(self):
        if self.view.point_model.empty:
            return
        self.model.set_all_cors(self.model.cor_for_current_preview_slice)
