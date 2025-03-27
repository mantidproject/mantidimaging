# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumPlotWidget
import numpy as np


class FittingDisplayWidget(QWidget):
    """
    Widget for displaying fitting-related spectrum plot using the reusable SpectrumPlotWidget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.spectrum_plot = SpectrumPlotWidget()
        self.layout.addWidget(self.spectrum_plot)

    def update_plot(self, x_data, y_data, label="ROI"):
        self.spectrum_plot.spectrum.clear()
        if self._valid_plot_data(x_data, y_data):
            self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))

    def update_labels(self, tof_range, image_range, wavelength_range=None):
        self.spectrum_plot.set_tof_range_label(*tof_range)
        self.spectrum_plot.set_image_index_range_label(*image_range)
        if wavelength_range is not None and len(wavelength_range) == 2:
            self.spectrum_plot.set_wavelength_range_label(*wavelength_range)

    @staticmethod
    def _valid_plot_data(x_data, y_data) -> bool:
        if x_data is None or y_data is None:
            return False
        if isinstance(x_data, np.ndarray) and isinstance(y_data, np.ndarray):
            return x_data.size > 0 and x_data.shape == y_data.shape
        if hasattr(x_data, "__len__") and hasattr(y_data, "__len__"):
            return len(x_data) > 0 and len(x_data) == len(y_data)
        return False
