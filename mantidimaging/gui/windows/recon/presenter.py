from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, Dict, List

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget

from mantidimaging.core.utility.cor_holder import ScalarCoR
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.dialogs.cor_inspection.view import CORInspectionDialogView
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.recon.model import ReconstructWindowModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.recon.view import ReconstructWindowView


class Notification(Enum):
    CROP_TO_ROI = auto()
    UPDATE_PREVIEWS = auto()
    RUN_AUTOMATIC = auto()
    RUN_MANUAL = auto()
    PREVIEW_RECONSTRUCTION = auto()
    PREVIEW_RECONSTRUCTION_SET_COR = auto()
    ADD_NEW_COR_TABLE_ROW = auto()
    REFINE_SELECTED_COR = auto()
    SHOW_COR_VS_SLICE_PLOT = auto()
    SET_ALL_ROW_VALUES = auto()
    ALGORITHM_CHANGED = auto()
    RECONSTRUCT_VOLUME = auto()
    CLEAR_ALL_CORS = auto()
    REMOVE_SELECTED_COR = auto()


class ReconstructWindowPresenter(BasePresenter):
    ERROR_STRING = "COR/Tilt finding failed: {}"
    view: 'ReconstructWindowView'

    def __init__(self, view: 'ReconstructWindowView', main_window):
        super(ReconstructWindowPresenter, self).__init__(view)
        self.view = view
        self.model = ReconstructWindowModel(self.view.point_model)
        self.allowed_recon_kwargs: Dict[str, List[str]] = self.model.load_allowed_recon_kwargs()
        self.restricted_arg_widgets: Dict[str, List[QWidget]] = {
            'filter_name': [self.view.filterName, self.view.filterNameLabel],
            'num_iter': [self.view.numIter, self.view.numIterLabel],
        }
        self.main_window = main_window

    def notify(self, signal):
        try:
            if signal == Notification.PREVIEW_RECONSTRUCTION:
                self.do_reconstruct_slice()
            elif signal == Notification.SHOW_COR_VS_SLICE_PLOT:
                self.do_plot_cor_vs_slice_index()
        except Exception as e:
            self.show_error(e)
            LOG.exception("Notification handler failed")

    def set_stack_uuid(self, uuid):
        self.view.reset_image_recon_preview()
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)
        # find a cor for the middle
        slice_idx, cor = self.model.find_initial_cor()
        self.view.add_cor_table_row(0, slice_idx, cor.value)
        # self.view.add_cor_table_row(0, first_slice_to_recon, initial_cor)

    def set_stack(self, stack):
        self.model.initial_select_data(stack)
        self.view.set_results(0, 0)
        self.set_preview_slice_idx(1024)
        self.do_update_previews()

    def set_preview_projection_idx(self, idx):
        self.model.preview_projection_idx = idx
        self.do_update_previews()

    def set_row(self, row):
        self.model.selected_row = row

    def set_preview_slice_idx(self, idx):
        self.model.preview_slice_idx = idx
        self.do_update_previews()
        self.do_reconstruct_slice()

    def do_crop_to_roi(self):
        self.model.update_roi_from_stack()
        self.view.set_results(0, 0)
        self.do_update_previews()

    def do_update_previews(self):
        img_data = self.model.sample[self.model.preview_projection_idx] \
            if self.model.sample is not None else None

        self.view.update_image_preview(img_data,
                                       self.model.preview_slice_idx,
                                       self.model.preview_tilt_line_data,
                                       self.model.roi)

        # self.view.update_fit_plot(self.model.slices, self.model.cors, self.model.preview_fit_y_data)

    def do_reconstruct_slice(self, cor=None, slice_idx=None):
        if slice_idx is None:
            slice_idx = self.model.preview_slice_idx

        # If no COR is provided and there are regression results then calculate
        # the COR for the selected preview slice
        if self.model.has_results and cor is None:
            cor = self.model.get_cor_for_slice_from_regression()

        if cor is not None:
            data = self.model.run_preview_recon(slice_idx, cor, self.view.algorithm_name, self.view.filter_name)
            self.view.update_image_recon_preview(data)

    def do_user_click_recon(self, slice_idx):
        self.model.preview_slice_idx = slice_idx

        cor = self.model.last_cor
        self.do_reconstruct_slice(cor, slice_idx)

    # def do_add_cor(self):
    #     row = self.model.selected_row
    #     cor = self.model.last_cor
    #     self.view.add_cor_table_row(row, self.model.preview_slice_idx, cor.value)

    def do_refine_selected_cor(self):
        slice_idx = self.model.preview_slice_idx

        dialog = CORInspectionDialogView(self.view, self.model.sample, slice_idx, self.model.last_cor)

        res = dialog.exec()
        LOG.debug('COR refine dialog result: {}'.format(res))
        if res == CORInspectionDialogView.Accepted:
            new_cor = dialog.optimal_rotation_centre
            LOG.debug('New optimal rotation centre: {}'.format(new_cor))
            self.model.data_model.set_cor_at_slice(slice_idx, new_cor)
            self.model.last_cor = ScalarCoR(new_cor)
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

    # def initial_cor(self):
    #     # start_async_task_view(self.view, self.model.run_finding_automatic, self._on_finding_done)
    #     start_async_task_view(self.view, self.model.initial_cor, self._on_finding_done)

    def do_cor_fit(self):
        start_async_task_view(self.view, self.model.run_finding_manual, self._on_finding_done)

    def _on_finding_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            self.view.set_results(*self.model.get_results())
            self.view.show_results()
            self.do_update_previews()
            self.do_reconstruct_slice()
        else:
            msg = self.ERROR_STRING.format(task.error)
            log.error(msg)
            self.show_error(msg)

    def do_set_all_row_values(self):
        if self.view.point_model.empty:
            return
        self.model.set_all_cors(self.model.cor_for_current_preview_slice)

    def do_algorithm_changed(self):
        allowed_args = self.allowed_recon_kwargs[self.view.algorithm_name]
        for arg, widgets in self.restricted_arg_widgets.items():
            if arg in allowed_args:
                for widget in widgets:
                    widget.show()
            else:
                for widget in widgets:
                    widget.hide()

    def do_clear_all_cors(self):
        self.view.clear_cor_table()

    def do_remove_selected_cor(self):
        self.view.remove_selected_cor()

    def do_reconstruct_volume(self):
        raise NotImplementedError("TODO")

    def find_initial_cor(self):
        self.model.find_initial_cor()
