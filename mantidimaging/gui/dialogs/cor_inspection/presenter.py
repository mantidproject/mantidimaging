from __future__ import absolute_import, division, print_function

from logging import getLogger
from enum import Enum
from PyQt5 import Qt

from mantidimaging.core.utility.progress_reporting import ProgressHandler
from mantidimaging.gui.mvp_base import BasePresenter

from .model import CORInspectionDialogModel
from .types import ImageType

LOG = getLogger(__name__)


class Notification(Enum):
    IMAGE_CLICKED_LESS = 1
    IMAGE_CLICKED_CURRENT = 2
    IMAGE_CLICKED_MORE = 3
    FULL_UPDATE = 4
    UPDATE_PARAMETERS_FROM_UI = 5
    LOADED = 6


class CORInspectionDialogPresenter(BasePresenter):
    progress_updated = Qt.pyqtSignal(float, str)

    def __init__(self, view, **args):
        super(CORInspectionDialogPresenter, self).__init__(view)

        self.model = CORInspectionDialogModel(**args)

    def notify(self, signal):
        try:
            if signal == Notification.IMAGE_CLICKED_LESS:
                self.on_select_image(ImageType.LESS)
            elif signal == Notification.IMAGE_CLICKED_CURRENT:
                self.on_select_image(ImageType.CURRENT)
            elif signal == Notification.IMAGE_CLICKED_MORE:
                self.on_select_image(ImageType.MORE)
            elif signal == Notification.FULL_UPDATE:
                self.do_full_ui_update()
            elif signal == Notification.UPDATE_PARAMETERS_FROM_UI:
                self.do_update_ui_parameters()
            elif signal == Notification.LOADED:
                self.on_load()

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def on_load(self):
        self.view.set_maximum_cor(self.model.cor_extents[1])
        self.notify(Notification.FULL_UPDATE)

    def on_select_image(self, img):
        LOG.debug('Image selected: {}'.format(img))

        # Adjust COR step
        self.model.adjust_cor(img)

        # Update UI
        self.notify(Notification.FULL_UPDATE)

    def do_full_ui_update(self):
        # Parameters
        self.view.step_size = self.model.cor_step

        # Images
        for i in ImageType:
            title = 'COR: {}'.format(self.model.cor(i))
            self.view.set_image(i, self.model.recon_preview(i), title)

        self.view.image_canvas_draw()

    def do_update_ui_parameters(self):
        self.model.cor_step = self.view.step_size

        # Update UI
        self.notify(Notification.FULL_UPDATE)

    @property
    def optimal_rotation_centre(self):
        return self.model.centre_cor
