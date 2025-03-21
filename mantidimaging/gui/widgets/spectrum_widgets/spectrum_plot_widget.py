# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtCore import pyqtSignal, QSignalBlocker
from pyqtgraph import GraphicsLayoutWidget, PlotItem, LinearRegionItem


class SpectrumPlotWidget(GraphicsLayoutWidget):
    """
    Widget to display a line plot of spectrum data with an optional linear region slider.
    Emits a signal when the selected time-of-flight range changes.
    """

    range_changed = pyqtSignal(object)  # Emits (tof_min, tof_max)

    def __init__(self):
        super().__init__()

        # Create and configure the plot item
        self.spectrum: PlotItem = self.addPlot(title="Spectrum Plot")
        self.spectrum.setLabel('left', 'Intensity')
        self.spectrum.setLabel('bottom', 'ToF', units='a.u.')  # Default axis label
        self.spectrum.showGrid(x=True, y=True)

        # Create and add linear region control for ToF range selection
        self.range_control = LinearRegionItem()
        self.range_control.setZValue(10)
        self.range_control.sigRegionChangeFinished.connect(self._handle_range_changed)
        self.spectrum.addItem(self.range_control)

        # Add labels for current range
        self.nextRow()
        self._tof_range_label = self.addLabel()
        self.nextRow()
        self._image_index_label = self.addLabel()

    def _handle_range_changed(self):
        r_min, r_max = self.range_control.getRegion()
        self.set_tof_range_label(r_min, r_max)
        self.range_changed.emit((r_min, r_max))

    def set_tof_axis_label(self, label: str):
        """Set the label for the ToF (x) axis."""
        self.spectrum.setLabel('bottom', text=label)

    def add_range(self, range_min: float, range_max: float):
        """Set the bounds and current region of the slider."""
        with QSignalBlocker(self.range_control):
            self.range_control.setBounds((range_min, range_max))
            self.range_control.setRegion((range_min, range_max))
        self.set_tof_range_label(range_min, range_max)

    def set_tof_range_label(self, range_min: float, range_max: float):
        """Update the range label."""
        self._tof_range_label.setText(f"ToF Range: {range_min:.2f} - {range_max:.2f}")

    def set_image_index_range_label(self, index_min: int, index_max: int):
        """Update the image index label."""
        self._image_index_label.setText(f"Image Index Range: {index_min} - {index_max}")
