from logging import getLogger
from typing import TYPE_CHECKING, Dict, List

from PyQt5.QtWidgets import QWidget

from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees, Slope
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.dialogs.cor_inspection.view import CORInspectionDialogView
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.recon.model import ReconstructWindowModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.recon.view import ReconstructWindowView


class ReconstructWindowPresenter(BasePresenter):
    ERROR_STRING = "COR/Tilt finding failed: {}"
    view: 'ReconstructWindowView'

    def __init__(self, view: 'ReconstructWindowView', main_window):
        super(ReconstructWindowPresenter, self).__init__(view)
        self.view = view
        self.model = ReconstructWindowModel(self.view.cor_table_model)
        self.allowed_recon_kwargs: Dict[str, List[str]] = self.model.load_allowed_recon_kwargs()
        self.restricted_arg_widgets: Dict[str, List[QWidget]] = {
            'filter_name': [self.view.filterName, self.view.filterNameLabel],
            'num_iter': [self.view.numIter, self.view.numIterLabel],
        }
        self.main_window = main_window

    def do_algorithm_changed(self):
        allowed_args = self.allowed_recon_kwargs[self.view.algorithm_name]
        for arg, widgets in self.restricted_arg_widgets.items():
            if arg in allowed_args:
                for widget in widgets:
                    widget.show()
            else:
                for widget in widgets:
                    widget.hide()

    def set_stack_uuid(self, uuid):
        self.view.reset_image_recon_preview()
        self.view.clear_cor_table()
        stack = self.main_window.get_stack_visualiser(uuid) if uuid is not None else None
        self.set_stack(stack)
        if stack is not None:
            self.view.reset_slice_and_tilt(self.model.get_initial_slice_index())
        # find a cor for the middle
        self.view.add_cor_table_row(0, self.model.preview_slice_idx, self.model.last_cor.value)
        self.do_reconstruct_slice()

    def set_stack(self, stack):
        self.model.initial_select_data(stack)
        self.view.set_results(ScalarCoR(0.0), Degrees(0.0), Slope(0.0))
        self.do_update_projection()

    def set_preview_projection_idx(self, idx):
        self.model.preview_projection_idx = idx
        self.do_update_projection()

    def set_row(self, row):
        self.model.selected_row = row

    def set_preview_slice_idx(self, idx):
        self.model.preview_slice_idx = idx
        self.do_update_projection()
        self.do_reconstruct_slice()

    def do_crop_to_roi(self):
        self.model.update_roi_from_stack()
        self.view.set_results(ScalarCoR(0.0), Degrees(0.0), Slope(0.0))
        self.do_update_projection()

    def do_update_projection(self):
        img_data = self.model.sample[self.model.preview_projection_idx] \
            if self.model.sample is not None else None

        self.view.update_image_preview(img_data,
                                       self.model.preview_slice_idx,
                                       self.model.preview_tilt_line_data,
                                       self.model.roi)

    def do_add_cor(self):
        row = self.model.selected_row
        # TODO why7 doesn't add get one form the regression?!
        cor = self.model.get_me_a_cor()
        self.view.add_cor_table_row(row, self.model.preview_slice_idx, cor.value)

    def do_reconstruct_slice(self, cor=None, slice_idx=None):
        if slice_idx is None:
            slice_idx = self.model.preview_slice_idx

        # If no COR is provided and there are regression results then calculate
        # the COR for the selected preview slice
        cor = self.model.get_me_a_cor(cor)

        data = self.model.run_preview_recon(slice_idx, cor, self.view.algorithm_name, self.view.filter_name)
        self.view.update_image_recon_preview(data)

    def do_user_click_recon(self, slice_idx):
        self.model.preview_slice_idx = slice_idx
        self.do_reconstruct_slice(slice_idx=slice_idx)

    def do_refine_selected_cor(self):
        slice_idx = self.model.preview_slice_idx

        dialog = CORInspectionDialogView(self.view, self.model.images, slice_idx, self.model.last_cor)

        res = dialog.exec()
        LOG.debug('COR refine dialog result: {}'.format(res))
        if res == CORInspectionDialogView.Accepted:
            new_cor = dialog.optimal_rotation_centre
            LOG.debug('New optimal rotation centre: {}'.format(new_cor))
            self.model.data_model.set_cor_at_slice(slice_idx, new_cor.value)
            self.model.last_cor = new_cor
            # Update reconstruction preview with new COR
            self.do_reconstruct_slice(new_cor, slice_idx)

    def do_cor_fit(self):
        start_async_task_view(self.view, self.model.do_fit, self._on_finding_done)

    def _on_finding_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            self.view.set_results(*self.model.get_results())
            self.do_update_projection()
            self.do_reconstruct_slice()
        else:
            msg = self.ERROR_STRING.format(task.error)
            log.error(msg)
            self.show_error(msg)

    def do_set_all_row_values(self):
        if self.view.cor_table_model.empty:
            return
        self.model.set_all_cors(self.model.cor_for_current_preview_slice)

    def do_clear_all_cors(self):
        self.view.clear_cor_table()
        self.model.reset_selected_row()

    def do_remove_selected_cor(self):
        self.view.remove_selected_cor()

    def do_reconstruct_volume(self):
        raise NotImplementedError("TODO")

    def find_initial_cor(self):
        self.model.find_initial_cor()

    def set_last_cor(self, cor):
        self.model.last_cor = ScalarCoR(cor)

    def do_calculate_cors_from_manual_tilt(self):
        cor = ScalarCoR(self.view.resultCor.value())
        tilt = Degrees(self.view.resultTilt.value())
        self.model.set_precalculated(cor, tilt)
        self.view.set_results(*self.model.get_results())
        for idx, point in enumerate(self.model.data_model.iter_points()):
            self.view.set_table_point(idx, point.slice_index, point.cor)
        self.do_reconstruct_slice()
