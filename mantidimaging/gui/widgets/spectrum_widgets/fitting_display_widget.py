# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsItem
from PyQt5 import QtCore
from pyqtgraph import RectROI, mkPen, ImageItem, ROI
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumPlotWidget, SpectrumROI


class FittingDisplayWidget(QWidget):
    """
    Widget for displaying fitting-related spectrum plot using the reusable SpectrumPlotWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.spectrum_plot = SpectrumPlotWidget()
        self.layout.addWidget(self.spectrum_plot)

        self.fitting_region = RectROI([0, 0], [1, 1], pen=mkPen((255, 0, 0), width=2), movable=True)
        self.fitting_region.setZValue(10)
        self.fitting_region.addScaleHandle([1, 1], [0, 0])
        self.fitting_region.addScaleHandle([0, 0], [1, 1])
        self.fitting_region.addScaleHandle([0, 1], [1, 0])
        self.fitting_region.addScaleHandle([1, 0], [0, 1])
        self.spectrum_plot.spectrum.addItem(self.fitting_region)

        self.image_item = ImageItem()
        self.image_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.image_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.image_item.setParentItem(self.spectrum_plot.spectrum)
        self.image_item.setZValue(20)
        self.image_item.setScale(0.2)
        self.image_item.setPos(self.spectrum_plot.width() - 150, 10)

        self.image_preview_roi = ROI([0, 0], [10, 10], pen=mkPen((0, 255, 0), width=2))
        self.image_preview_roi.setZValue(21)
        self.image_preview_roi.setParentItem(self.image_item)
        self.image_preview_roi.setAcceptedMouseButtons(QtCore.Qt.NoButton)  # Optional: make non-interactive
        self.image_preview_roi.hide()

    def update_plot(self,
                    x_data: np.ndarray,
                    y_data: np.ndarray,
                    label: str = "ROI",
                    image: np.ndarray | None = None) -> None:
        self.spectrum_plot.spectrum.clear()
        self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))
        self.spectrum_plot.spectrum.addItem(self.fitting_region)
        self.set_default_region(x_data, y_data)
        self.update_image(image)

    def update_image(self, image: np.ndarray | None) -> None:
        if image is not None:
            self.image_item.setImage(image, autoLevels=True)

    def update_labels(self, wavelength_range: tuple[float, float] | None = None) -> None:
        """Update wavelength range label below the plot, if available."""
        if wavelength_range is not None:
            self.spectrum_plot.set_wavelength_range_label(*wavelength_range)

    def set_default_region(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Position the ROI centrally over the plotted data."""
        x_min, x_max = float(np.min(x_data)), float(np.max(x_data))
        y_min, y_max = float(np.min(y_data)), float(np.max(y_data))
        x_span = max((x_max - x_min) * 0.25, 20.0)
        y_span = max((y_max - y_min) * 0.5, 10.0)
        x_start = (x_min + x_max - x_span) / 2
        y_start = max((y_min + y_max - y_span) / 2, 0.0)

        self.fitting_region.setPos((x_start, y_start))
        self.fitting_region.setSize((x_span, y_span))

    def set_selected_fit_region(self, region: tuple[float, float]) -> None:
        """Set the horizontal (X-axis) range of the ROI."""
        x_start, x_end = region
        width = x_end - x_start
        y_pos = self.fitting_region.pos().y()
        height = self.fitting_region.size().y()
        self.fitting_region.setPos((x_start, y_pos))
        self.fitting_region.setSize((width, height))

    def get_selected_fit_region(self) -> tuple[float, float]:
        pos = self.fitting_region.pos()
        size = self.fitting_region.size()
        return float(pos.x()), float(pos.x() + size.x())

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
