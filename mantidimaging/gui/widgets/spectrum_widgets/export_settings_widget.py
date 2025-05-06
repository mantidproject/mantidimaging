# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox


class FitExportFormWidget(QWidget):
    """
    Export Format and Export Area dropdowns.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.formatDropdown = QComboBox()
        self.formatDropdown.addItems(["CSV", "Nexus", "RITS"])
        self.areaDropdown = QComboBox()
        self.areaDropdown.addItem("All")

        layout.addWidget(QLabel("Export Format"))
        layout.addWidget(self.formatDropdown)
        layout.addWidget(QLabel("Export Area"))
        layout.addWidget(self.areaDropdown)
        layout.addStretch()

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

    def selected_format(self) -> str:
        return self.formatDropdown.currentText()

    def selected_area(self) -> str:
        return self.areaDropdown.currentText()
