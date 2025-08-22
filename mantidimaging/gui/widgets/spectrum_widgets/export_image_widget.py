# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class ExportImageViewWidget(QWidget):
    """
    Minimal image preview widget for the Export tab.
    """

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_view = pg.ImageView()
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        self.image_view.ui.histogram.hide()

        layout.addWidget(self.image_view)
        self.clear()

    def update_image(self, image: np.ndarray | None, autoLevels: bool = True) -> None:
        if image is None:
            self.clear()
            return

        arr = np.asarray(image)
        if arr.ndim == 3 and arr.shape[0] > 0:
            arr = arr.mean(axis=0)
        self.image_view.setImage(arr, autoLevels=autoLevels)

    def clear(self) -> None:
        """Show a blank canvas."""
        self.image_view.setImage(np.zeros((1, 1), dtype=np.float32), autoLevels=True)

    @property
    def image_data(self) -> np.ndarray | None:
        """Return the currently displayed image array, or None."""
        return getattr(self.image_view.imageItem, "image", None)
