# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import traceback
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from mantidimaging.gui.mvp_base import BasePresenter
from .model import CORInspectionDialogModel
from .types import ImageType

if TYPE_CHECKING:
    from .view import CORInspectionDialogView  # pragma: no cover

LOG = getLogger(__name__)


class Notification(Enum):
    IMAGE_CLICKED_LESS = 1
    IMAGE_CLICKED_CURRENT = 2
    IMAGE_CLICKED_MORE = 3
    FULL_UPDATE = 4
    UPDATE_PARAMETERS_FROM_UI = 5
    LOADED = 6


class CORInspectionDialogPresenter(BasePresenter):
    progress_updated = pyqtSignal(float, str)

    view: CORInspectionDialogView

    def __init__(self, view, images: ImageStack, slice_index: int, initial_cor: ScalarCoR,
                 recon_params: ReconstructionParameters, iters_mode: bool):
        super().__init__(view)

        if iters_mode:
            self.get_title = self._make_iters_title
        else:
            self.get_title = self._make_cor_title

        self.model = CORInspectionDialogModel(images, slice_index, initial_cor, recon_params, iters_mode)

    def notify(self, signal) -> None:
        try:
            if signal == Notification.IMAGE_CLICKED_LESS:
                self.on_select_image(ImageType.LESS)
            elif signal == Notification.IMAGE_CLICKED_MORE:
                self.on_select_image(ImageType.MORE)
            elif signal == Notification.IMAGE_CLICKED_CURRENT:
                self.on_select_image(ImageType.CURRENT)
            elif signal == Notification.FULL_UPDATE:
                self.do_refresh()
            elif signal == Notification.UPDATE_PARAMETERS_FROM_UI:
                self.do_update_ui_parameters()
            elif signal == Notification.LOADED:
                self.on_load()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def on_load(self) -> None:
        self.view.set_maximum_cor(self.model.cor_extents[1])
        self.notify(Notification.FULL_UPDATE)

    def on_select_image(self, img) -> None:
        LOG.debug(f'Image selected: {img}')

        # Adjust COR/iterations step
        self.model.adjust(img)

        if img != ImageType.CURRENT:
            # Update UI
            self.do_refresh()
        else:
            self.do_refresh([ImageType.LESS, ImageType.MORE])

    def _make_cor_title(self, image) -> str:
        return f'COR: {self.model.cor(image)}'

    def _make_iters_title(self, image) -> str:
        return f'Iterations: {self.model.iterations(image)}'

    def do_refresh(self, images=None):
        if images is None:
            images = ImageType
        # Parameters
        self.view.step_size = self.model.step

        # Images
        for i in images:
            self.view.set_image(i, self.model.recon_preview(i), self.get_title(i))

    def do_update_ui_parameters(self):
        self.model.step = self.view.step_size

        # Update UI
        self.notify(Notification.FULL_UPDATE)

    @property
    def optimal_rotation_centre(self) -> ScalarCoR:
        return ScalarCoR(self.model.centre_value)

    @property
    def optimal_iterations(self):
        return self.model.centre_value
