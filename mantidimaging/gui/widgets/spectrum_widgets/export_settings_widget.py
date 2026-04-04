# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QGroupBox)


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
        """Populate the parameter selector combo with fitted parameter names and enable it."""
        self.parameterDropdown.clear()
        self.parameterDropdown.addItems(param_names)
        self.parameterDropdown.setEnabled(bool(param_names))

    @property
    def parameter_selected(self):
        return self.parameterDropdown.currentTextChanged

    def selected_format(self) -> str:
        return self.formatDropdown.currentText()

    def selected_area(self) -> str:
        return self.areaDropdown.currentText()
