# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from collections.abc import Sequence
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
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

    def update_plot(self,
                    x_data: Sequence[float] | np.ndarray,
                    y_data: Sequence[float] | np.ndarray,
                    label: str = "ROI") -> None:
        self.spectrum_plot.spectrum.clear()
        self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))

    def update_labels(self, wavelength_range: tuple[float, float] | None = None) -> None:
        if wavelength_range is not None and len(wavelength_range) == 2:
            self.spectrum_plot.set_wavelength_range_label(*wavelength_range)
