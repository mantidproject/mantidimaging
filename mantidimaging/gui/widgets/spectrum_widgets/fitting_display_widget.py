# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import LinearRegionItem, mkPen
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumPlotWidget


class FittingDisplayWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.spectrum_plot = SpectrumPlotWidget()
        self.layout.addWidget(self.spectrum_plot)

        self.fitting_region = None  # We'll add it once, safely

    def update_plot(self, x_data, y_data, label="ROI"):
        if len(x_data) == 0:
            print("[FittingDisplayWidget] No x_data to plot.")
            return

        print(f"[FittingDisplayWidget] Plotting {label} with x range: {min(x_data)} to {max(x_data)}")
        self.spectrum_plot.spectrum.clear()
        self.spectrum_plot.spectrum.plot(x_data, y_data, name=label, pen=(255, 255, 0))

        # Safe add
        if self.fitting_region is None:
            self.fitting_region = LinearRegionItem(brush=(255, 0, 0, 80), pen=mkPen((255, 0, 0, 255)))
            self.fitting_region.setZValue(10)
            self.fitting_region.setMovable(True)
            self.spectrum_plot.spectrum.addItem(self.fitting_region)
            print("[FittingDisplayWidget] Added fitting region to plot.")

        self.set_default_region(x_data)

    def update_labels(self, tof_range, image_range, wavelength_range=None):
        self.spectrum_plot.set_tof_range_label(*tof_range)
        self.spectrum_plot.set_image_index_range_label(*image_range)
        if wavelength_range and len(wavelength_range) == 2:
            self.spectrum_plot.set_wavelength_range_label(*wavelength_range)

    def set_default_region(self, x_data):
        min_x = float(min(x_data))
        max_x = float(max(x_data))

        if max_x - min_x < 1e-6:
            region = (min_x - 1, min_x + 1)
        else:
            span = max((max_x - min_x) * 0.25, 20)
            mid = (min_x + max_x) / 2
            region = (mid - span / 2, mid + span / 2)

        print(f"[FittingDisplayWidget] Setting red region to: {region}")
        self.fitting_region.setRegion(region)

    def get_selected_fit_region(self) -> tuple[float, float]:
        region = self.fitting_region.getRegion()
        return float(region[0]), float(region[1])

    def set_selected_fit_region(self, region: tuple[float, float]):
        print(f"[FittingDisplayWidget] Manually setting region to: {region}")
        if self.fitting_region:
            self.fitting_region.setRegion(region)
