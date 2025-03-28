# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import RectROI, mkPen
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumPlotWidget


class FittingDisplayWidget(QWidget):
    """
    Widget for displaying fitting-related spectrum plot using the reusable SpectrumPlotWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.spectrum_plot: SpectrumPlotWidget = SpectrumPlotWidget()
        self.layout.addWidget(self.spectrum_plot)

        self.fitting_region: RectROI | None = None

    def update_plot(self, x_data: np.ndarray, y_data: np.ndarray, label: str = "ROI") -> None:
        """Update the spectrum plot and preserve the fitting ROI if it exists."""
        if x_data is None or len(x_data) == 0:
            return
        existing_region = self.fitting_region
        self.spectrum_plot.spectrum.clear()
        self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))
        if existing_region is not None:
            self.spectrum_plot.spectrum.addItem(existing_region)
        else:
            self.fitting_region = RectROI([0, 0], [1, 1], pen=mkPen((255, 0, 0), width=2), movable=True)
            self.fitting_region.setZValue(10)
            self.fitting_region.addScaleHandle([1, 1], [0, 0])
            self.fitting_region.addScaleHandle([0, 0], [1, 1])
            self.fitting_region.addScaleHandle([0, 1], [1, 0])
            self.fitting_region.addScaleHandle([1, 0], [0, 1])
            self.spectrum_plot.spectrum.addItem(self.fitting_region)
            self.set_default_region(x_data, y_data)

    def update_labels(self, wavelength_range: tuple[float, float] | None = None) -> None:
        """Update wavelength range label below the plot, if available."""
        if wavelength_range and len(wavelength_range) == 2:
            self.spectrum_plot.set_wavelength_range_label(*wavelength_range)

    def set_default_region(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Position the ROI centrally over the plotted data."""
        x_min, x_max = float(np.min(x_data)), float(np.max(x_data))
        y_min, y_max = float(np.min(y_data)), float(np.max(y_data))
        x_span = max((x_max - x_min) * 0.25, 20.0)
        y_span = max((y_max - y_min) * 0.5, 10.0)
        x_start = (x_max + x_min) / 2 - x_span / 2
        y_start = (y_max + y_min) / 2 - y_span / 2

        if self.fitting_region is not None:
            self.fitting_region.setPos((x_start, y_start))
            self.fitting_region.setSize((x_span, y_span))

    def set_selected_fit_region(self, region: tuple[float, float]) -> None:
        if self.fitting_region:
            x_start = float(region[0])
            width = float(region[1] - region[0])
            current_pos = self.fitting_region.pos()
            self.fitting_region.setPos((x_start, current_pos.y()))
            self.fitting_region.setSize((width, self.fitting_region.size().y()))

    def get_selected_fit_region(self) -> tuple[float, float]:
        if self.fitting_region:
            pos = self.fitting_region.pos()
            size = self.fitting_region.size()
            return float(pos.x()), float(pos.x() + size.x())
        return 0.0, 1.0
