# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Any, TYPE_CHECKING

import numpy as np
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

if TYPE_CHECKING:
    from mantidimaging.core.utility.sensible_roi import ROIBinner

_graveyard: list[Any] = []


class ExportImageViewWidget(QWidget):
    """
    Minimal image preview widget for the Export tab.
    """

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_view = pg.ImageView()
        _graveyard.append(self.image_view.view)
        _graveyard.append(self.image_view.getRoiPlot().plotItem.vb)
        _graveyard.append(self.image_view.getHistogramWidget().vb)
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        self.image_view.ui.histogram.hide()

        layout.addWidget(self.image_view)

        self.param_overlay = pg.ImageItem()
        self.param_overlay.hide()
        self.image_view.getView().addItem(self.param_overlay)

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
        self.image_view.ui.histogram.setImageItem(self.image_view.imageItem)
        self.image_view.ui.histogram.hide()
        self.param_overlay.hide()

    def populate_parameter_selector(self, param_names: list[str]) -> None:
        """Populate the parameter selector combobox with fitted parameter names"""
        self.parent().exportSettingsWidget.populate_parameter_selector(param_names)

    def show_parameter_map(self, map_array: np.ndarray, binner: ROIBinner, opacity: float = 0.5) -> None:
        """Display the parameter map with 50% transaparency and viridis over sample"""

        self.param_overlay.setColorMap('viridis')
        self.param_overlay.setOpacity(opacity)

        # Align mapping with sample and scale to match binned resolution
        transform = QTransform()
        transform.translate(binner.left_indexes[0], binner.top_indexes[0])
        transform.scale(binner.step_size, binner.step_size)
        self.param_overlay.setImage(map_array, autoLevels=True)
        self.param_overlay.setTransform(transform)
        self.param_overlay.show()

        # connect histogram to parameter values and match colourmap
        hist = self.image_view.ui.histogram
        hist.setImageItem(self.param_overlay)
        hist.gradient.setColorMap(pg.colormap.get('viridis'))
        hist.show()

    @property
    def image_data(self) -> np.ndarray | None:
        """Return the currently displayed image array, or None."""
        return getattr(self.image_view.imageItem, "image", None)
