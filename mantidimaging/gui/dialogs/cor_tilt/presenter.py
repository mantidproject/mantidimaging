from __future__ import absolute_import, division, print_function

from enum import Enum
from logging import getLogger

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.dialogs.async_task import AsyncTaskDialogView
from mantidimaging.gui.mvp_base import BasePresenter

from .model import CORTiltDialogModel


class Notification(Enum):
    CROP_TO_ROI = 1
    UPDATE_PREVIEWS = 2
    UPDATE_INDICES = 3
    RUN = 4


class CORTiltDialogPresenter(BasePresenter):

    def __init__(self, view, main_window):
        super(CORTiltDialogPresenter, self).__init__(view)
        self.model = CORTiltDialogModel()
        self.main_window = main_window

    def notify(self, signal):
        try:
            if signal == Notification.CROP_TO_ROI:
                self.do_crop_to_roi()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
            elif signal == Notification.UPDATE_INDICES:
                self.do_update_indices()
            elif signal == Notification.RUN:
                self.do_execute()

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def set_stack_uuid(self, uuid):
        self.set_stack(
                self.main_window.get_stack_visualiser(uuid)
                if uuid is not None else None)

    def set_stack(self, stack):
        self.model.initial_select_data(stack)

        self.notify(Notification.UPDATE_PREVIEWS)
        self.notify(Notification.UPDATE_INDICES)
        self.view.set_results(0, 0)
        self.view.set_max_preview_idx(self.model.num_projections - 1)

    def set_preview_idx(self, idx):
        self.model.preview_idx = idx
        self.notify(Notification.UPDATE_PREVIEWS)

    def do_crop_to_roi(self):
        self.model.update_roi_from_stack()

        self.notify(Notification.UPDATE_PREVIEWS)
        self.notify(Notification.UPDATE_INDICES)
        self.view.set_results(0, 0)

    def do_update_previews(self):
        img_data = self.model.sample[self.model.preview_idx] \
                if self.model.sample is not None else None

        self.view.update_image_preview(
                img_data, self.model.preview_tilt_line_data, self.model.roi)

        self.view.update_fit_plot(self.model.slice_indices,
                                  self.model.cors,
                                  self.model.preview_fit_y_data)

    def do_update_indices(self):
        self.model.calculate_slices(self.view.slice_count)

    def do_execute(self):
        atd = AsyncTaskDialogView(self.view, auto_close=True)
        kwargs = {'progress': Progress()}
        kwargs['progress'].add_progress_handler(atd.presenter)

        atd.presenter.set_task(self.model.run_finding)
        atd.presenter.set_on_complete(self._on_finding_done)
        atd.presenter.set_parameters(**kwargs)
        atd.presenter.do_start_processing()

    def _on_finding_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            self.view.set_results(self.model.cor, self.model.tilt)
            self.notify(Notification.UPDATE_PREVIEWS)
        else:
            log.error("COR/Tilt finding failed: %s", str(task.error))
            self.show_error("COR/Tilt finding failed. See log for details.")
