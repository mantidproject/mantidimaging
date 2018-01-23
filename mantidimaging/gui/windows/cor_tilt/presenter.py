from __future__ import absolute_import, division, print_function

from enum import Enum
from logging import getLogger

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.dialogs.async_task import AsyncTaskDialogView
from mantidimaging.gui.mvp_base import BasePresenter

from .model import CORTiltWindowModel


class Notification(Enum):
    CROP_TO_ROI = 1
    UPDATE_PREVIEWS = 2
    RUN = 3


class CORTiltWindowPresenter(BasePresenter):

    def __init__(self, view, main_window):
        super(CORTiltWindowPresenter, self).__init__(view)
        self.model = CORTiltWindowModel()
        self.main_window = main_window

    def notify(self, signal):
        try:
            if signal == Notification.CROP_TO_ROI:
                self.do_crop_to_roi()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
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
        self.view.set_results(0, 0)
        self.view.set_num_projections(self.model.num_projections)
        self.notify(Notification.UPDATE_PREVIEWS)

    def set_preview_idx(self, idx):
        self.model.preview_idx = idx
        self.notify(Notification.UPDATE_PREVIEWS)

    def do_crop_to_roi(self):
        self.model.update_roi_from_stack()
        self.view.set_results(0, 0)
        self.notify(Notification.UPDATE_PREVIEWS)

    def do_update_previews(self):
        img_data = self.model.sample[self.model.preview_idx] \
                if self.model.sample is not None else None

        self.view.update_image_preview(
                img_data, self.model.preview_tilt_line_data, self.model.roi)

        self.view.update_fit_plot(self.model.model.slices,
                                  self.model.model.cors,
                                  self.model.preview_fit_y_data)

    def do_execute(self):
        self.model.calculate_slices(self.view.slice_count)
        self.model.calculate_projections(self.view.projection_count)

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
            self.view.set_results(
                    self.model.model.c,
                    self.model.model.angle_rad)
            self.notify(Notification.UPDATE_PREVIEWS)
        else:
            log.error("COR/Tilt finding failed: %s", str(task.error))
            self.show_error("COR/Tilt finding failed. See log for details.")
