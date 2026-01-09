# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from functools import partial
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsItem, QAction, QActionGroup
from PyQt5.QtGui import QTransform
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import RectROI, mkPen, ImageItem, PlotDataItem, ROI

from mantidimaging.gui.windows.spectrum_viewer.model import allowed_modes
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumPlotWidget, SpectrumROI
from mantidimaging.core.fitting.fitting_functions import FittingRegion
from logging import getLogger

LOG = getLogger(__name__)


class FittingDisplayWidget(QWidget):
    """
    Widget for displaying fitting-related spectrum plot using the reusable SpectrumPlotWidget.
    """

    initial_fit_line: PlotDataItem | None = None
    unit_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.spectrum_plot = SpectrumPlotWidget()
        self.layout.addWidget(self.spectrum_plot)
        self._current_fit_line: PlotDataItem | None = None

        self.fitting_region = RectROI([-1, -1], [1, 1], pen=mkPen((255, 0, 0), width=2), movable=True)
        self.fitting_region.setZValue(10)
        self.fitting_region.addScaleHandle([1, 1], [0, 0])
        self.fitting_region.addScaleHandle([0, 0], [1, 1])
        self.fitting_region.addScaleHandle([0, 1], [1, 0])
        self.fitting_region.addScaleHandle([1, 0], [0, 1])
        self.spectrum_plot.spectrum.addItem(self.fitting_region)

        self.image_item = ImageItem()
        self.image_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.image_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.image_item.setImage(np.zeros((150, 150)), autoLevels=True)
        self.image_item.setParentItem(self.spectrum_plot.spectrum)
        self.image_item.setZValue(20)
        self.spectrum_plot.spectrum.set_right_anchored_child(self.image_item, (160, 10))

        self.image_preview_roi = ROI([0, 0], [10, 10], pen=mkPen((0, 255, 0), width=2))
        self.image_preview_roi.setZValue(21)
        self.image_preview_roi.setParentItem(self.image_item)
        self.image_preview_roi.setAcceptedMouseButtons(QtCore.Qt.NoButton)  # Optional: make non-interactive
        self.image_preview_roi.hide()
        self._add_units_menu()

        self._showing_initial_fit = False

    def set_plot_mode(self, mode: str) -> None:
        self._showing_initial_fit = (mode == "initial")

    def update_plot(self, x_data: np.ndarray, y_data: np.ndarray, label: str = "ROI") -> None:
        self.spectrum_plot.spectrum.clear()
        self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))
        self.spectrum_plot.spectrum.addItem(self.fitting_region)
        self.set_default_region_if_needed(x_data, y_data)
        if not getattr(self, "_log_emitted", False):
            LOG.debug("Spectrum plot updated: label=%s, points=%d", label, len(x_data))
        self._log_emitted = True

    def update_image(self, image: np.ndarray | None) -> None:
        if image is not None:
            self.image_item.setImage(image, autoLevels=True)
            height, width = image.shape
            scale = 150 / max(width, height)
            self.image_item.setTransform(QTransform().scale(scale, scale))

    def _add_units_menu(self) -> None:
        """Add a right-click units menu to the spectrum plot for unit conversion."""
        self.units_menu = self.spectrum_plot.spectrum_viewbox.menu.addMenu("Units")
        self.tof_mode_select_group = QActionGroup(self)
        for mode in allowed_modes.keys():
            action = QAction(mode, self.tof_mode_select_group)
            action.setCheckable(True)
            action.setObjectName(mode)
            self.units_menu.addAction(action)
            action.triggered.connect(partial(self.unit_changed.emit, mode))
            if mode == "Image Index":
                action.setChecked(True)

    def set_default_region_if_needed(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Position the ROI centrally over the plotted data, if valid data and not in existing region
        We define valid data as a spectrum which is non-zero in length and does not consist of nans or zeros
        We check for lengths <= 1 to prevent the fitting region being shown for single-image ImageStacks, e.g. Flats
        """
        if x_data.size <= 1 or np.all(np.isnan(y_data)) or np.all(y_data == 0):
            self.fitting_region.hide()
            return

        self.fitting_region.show()
        if self.is_data_in_region(x_data, y_data, self.get_selected_fit_region()):
            return

        x_min, x_max = float(np.nanmin(x_data)), float(np.nanmax(x_data))
        y_min, y_max = float(np.nanmin(y_data)), float(np.nanmax(y_data))
        x_span = (x_max - x_min) * 0.25
        y_span = (y_max - y_min) * 0.5
        x_start = (x_min + x_max - x_span) / 2
        y_start = (y_min + y_max - y_span) / 2
        self.fitting_region.setPos((x_start, y_start))
        self.fitting_region.setSize((x_span, y_span))

    @staticmethod
    def is_data_in_region(x_data: np.ndarray, y_data: np.ndarray, roi: FittingRegion):
        return np.any((x_data >= roi.x_min) & (x_data <= roi.x_max)
                    & (y_data >= roi.y_min) & (y_data <= roi.y_max)) # yapf: disable

    def get_selected_fit_region(self) -> FittingRegion:
        pos = self.fitting_region.pos()
        size = self.fitting_region.size()
        x1, x2 = pos.x(), pos.x() + size.x()
        y1, y2 = pos.y(), pos.y() + size.y()
        assert x1 < x2
        assert y1 < y2
        return FittingRegion(x1, x2, y1, y2)

    def show_roi_on_thumbnail_from_widget(self, roi_widget: SpectrumROI) -> None:
        """
        Copy ROI size and color from the main image window ROI to the thumbnail overlay.
        """
        pos = roi_widget.pos()
        size = roi_widget.size()
        color = roi_widget.colour

        self.image_preview_roi.setPos(pos)
        self.image_preview_roi.setSize(size)
        self.image_preview_roi.setPen(mkPen(color, width=2))
        self.image_preview_roi.show()

    def show_fit_line(self, x_data: np.ndarray, y_data: np.ndarray, *, color: tuple[int, int, int], label: str,
                      initial: bool) -> None:
        """
        Plot a single fit line (initial or fitted) on the spectrum plot, removing any previous fit line.

        Args:
            x_data: The x-axis data for the fit line.
            y_data: The y-axis data for the fit line.
            color: The RGB color tuple for the line.
            label: The legend label for the line.
            initial: True if this is the initial fit, False if fitted curve.
        """
        if self._current_fit_line:
            self.spectrum_plot.spectrum.removeItem(self._current_fit_line)
            self._current_fit_line = None
        self._current_fit_line = self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=color)
        self._showing_initial_fit = initial
        LOG.debug("Fit line displayed: label=%s, initial=%s, points=%d", label, initial, len(x_data))

    def is_initial_fit_visible(self) -> bool:
        return self._showing_initial_fit
