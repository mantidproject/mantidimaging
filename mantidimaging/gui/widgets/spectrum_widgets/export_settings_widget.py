# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox


class ExportDropdownWidget(QWidget):
    """
    A minimal export format + ROI area dropdown widget for the export tab's left panel.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        layout.addWidget(QLabel("Export Format"))
        self.formatDropdown = QComboBox()
        self.formatDropdown.addItems(["CSV", "Nexus", "RITS"])
        layout.addWidget(self.formatDropdown)
        layout.addWidget(QLabel("Export Area"))
        self.areaDropdown = QComboBox()
        self.areaDropdown.addItem("All")
        layout.addWidget(self.areaDropdown)
        self.setLayout(layout)

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
