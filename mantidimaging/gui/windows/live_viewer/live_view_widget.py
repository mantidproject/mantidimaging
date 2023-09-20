# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from pyqtgraph import GraphicsLayoutWidget
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.gui.widgets.zslider.zslider import ZSlider

if TYPE_CHECKING:
    import numpy as np


class LiveViewWidget(GraphicsLayoutWidget):
    """
    The widget containing the spectrum plot and the image projection.

    @param parent: The parent widget
    """
    image: MIMiniImageView

    def __init__(self) -> None:
        super().__init__()

        self.image = MIMiniImageView(name="Projection")
        self.addItem(self.image, 0, 0)
        self.nextRow()

        self.z_slider = ZSlider()
        self.addItem(self.z_slider)

        self.image.enable_message()

    def show_image(self, image: np.ndarray) -> None:
        """
        Show the image in the image view.
        @param image: The image to show
        """
        self.image.setImage(image)

    def handle_deleted(self) -> None:
        """
        Handle the deletion of the image.
        """
        self.image.clear()

    def show_error(self, message: str | None):
        self.image.show_message(message)
