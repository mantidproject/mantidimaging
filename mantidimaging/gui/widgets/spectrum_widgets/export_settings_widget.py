# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox, QDoubleSpinBox, QGroupBox)


class FitExportFormWidget(QWidget):
    """
    Export Format and Export Area dropdowns.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)

        # Parameter map group
        map_group = QGroupBox("Parameter Map")
        map_layout = QVBoxLayout(map_group)

        self.fitAllButton = QPushButton("Fit All")
        map_layout.addWidget(self.fitAllButton)

        map_layout.addWidget(QLabel("Map Parameter"))
        self.parameterDropdown = QComboBox()
        self.parameterDropdown.setEnabled(False)
        self.parameterDropdown.setPlaceholderText("Run fit to populate")
        map_layout.addWidget(self.parameterDropdown)

        map_layout.addWidget(QLabel("Map Transparency (%)"))
        self.transparencySpinBox = QSpinBox()
        self.transparencySpinBox.setRange(0, 100)
        self.transparencySpinBox.setValue(50)
        self.transparencySpinBox.setSuffix("%")
        map_layout.addWidget(self.transparencySpinBox)

        map_layout.addWidget(QLabel("Colour Range"))
        self.colourRangeDropdown = QComboBox()
        map_layout.addWidget(self.colourRangeDropdown)

        map_layout.addWidget(QLabel("chi\u00b2 threshold"))
        self.chiSquaredThresholdSpinBox = QDoubleSpinBox()
        self.chiSquaredThresholdSpinBox.setRange(0.0, 1e6)
        self.chiSquaredThresholdSpinBox.setDecimals(6)
        self.chiSquaredThresholdSpinBox.setSingleStep(0.0001)
        self.chiSquaredThresholdSpinBox.setToolTip("Pixels with reduced chi\u00b2 above threshold are masked. "
                                                   "Initialised to the 95th percentile of good fits.")
        map_layout.addWidget(self.chiSquaredThresholdSpinBox)

        map_layout.addWidget(QLabel("Image Export Region"))
        self.exportContentDropdown = QComboBox()
        self.exportContentDropdown.addItems(["Mapped region only", "Full sample image"])
        map_layout.addWidget(self.exportContentDropdown)

        self.exportMappedImageButton = QPushButton("Export Map...")
        self.exportMappedImageButton.setEnabled(False)
        map_layout.addWidget(self.exportMappedImageButton)

        outer_layout.addWidget(map_group)

        # Table export group
        table_group = QGroupBox("Table Export")
        table_layout = QVBoxLayout(table_group)

        self.formatDropdown = QComboBox()
        self.formatDropdown.addItems(["CSV"])
        self.areaDropdown = QComboBox()
        self.areaDropdown.addItem("All")

        table_layout.addWidget(QLabel("Export Format"))
        table_layout.addWidget(self.formatDropdown)
        table_layout.addWidget(QLabel("Export Area"))
        table_layout.addWidget(self.areaDropdown)

        self.exportButton = QPushButton("Export")
        table_layout.addWidget(self.exportButton)

        outer_layout.addWidget(table_group)
        outer_layout.addStretch()

    def set_roi_names(self, roi_names: list[str]) -> None:
        """Update ROI dropdown list dynamically."""
        current = self.areaDropdown.currentText()
        self.areaDropdown.blockSignals(True)
        self.areaDropdown.clear()
        self.areaDropdown.addItem("All")
        self.areaDropdown.addItems(roi_names)
        if current in roi_names:
            self.areaDropdown.setCurrentText(current)
        self.areaDropdown.blockSignals(False)

    def populate_parameter_selector(self, param_names: list[str]) -> None:
        """
        Populate the parameter selector combo with fitted parameter names and enable it
        after all data is written to export table
        """
        with QSignalBlocker(self.parameterDropdown):
            self.parameterDropdown.clear()
            self.parameterDropdown.addItems(param_names)
            self.parameterDropdown.setEnabled(bool(param_names))
            self.exportMappedImageButton.setEnabled(bool(param_names))
            if param_names:
                self.parameterDropdown.setCurrentIndex(0)

    def set_chi2_threshold(self, value: float) -> None:
        """
        Set the chi2 threshold without emitting signals to avoid pre-maturely
        updating the map display before all data is written to table
        """
        with QSignalBlocker(self.chiSquaredThresholdSpinBox):
            self.chiSquaredThresholdSpinBox.setValue(value)

    @property
    def parameter_selected(self):
        return self.parameterDropdown.currentTextChanged

    @property
    def overlay_opacity(self) -> float:
        """
        Return overlay opacity spinbox. Opacity flipped so that
        0% transparency = 100% opacity to improve intuitivenessl
        """
        return (100 - self.transparencySpinBox.value()) / 100.0

    @property
    def is_full_sample_export(self) -> bool:
        """True when the user has selected 'Full sample image' in the Image Export Region dropdown."""
        return self.exportContentDropdown.currentText() == "Full sample image"

    @property
    def selected_colour_range_mode(self) -> str:
        return self.colourRangeDropdown.currentText()

    def selected_format(self) -> str:
        return self.formatDropdown.currentText()

    def selected_area(self) -> str:
        return self.areaDropdown.currentText()
