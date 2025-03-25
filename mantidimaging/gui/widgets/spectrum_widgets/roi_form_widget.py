# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BaseWidget

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTabWidget, QComboBox, QPushButton
    from mantidimaging.gui.windows.spectrum_viewer.view import ROIPropertiesTableWidget, ROITableWidget


class ROIFormWidget(BaseWidget):
    exportTabs: QTabWidget
    roi_properties_widget: ROIPropertiesTableWidget
    table_view: ROITableWidget
    image_output_mode_combobox: QComboBox
    addBtn: QPushButton
    removeBtn: QPushButton
    exportButton: QPushButton
    exportButtonRITS: QPushButton

    def __init__(self, parent=None):
        super().__init__(parent, ui_file='gui/ui/roi_form_widget.ui')

        self.image_output_mode_combobox.currentTextChanged.connect(self.set_binning_visibility)
        self.set_binning_visibility()

    @property
    def image_output_mode(self) -> str:
        return self.image_output_mode_combobox.currentText()

    def set_binning_visibility(self) -> None:
        hide_binning = self.image_output_mode != "2D Binned"
        self.bin_size_label.setHidden(hide_binning)
        self.bin_size_spinBox.setHidden(hide_binning)
        self.bin_step_label.setHidden(hide_binning)
        self.bin_step_spinBox.setHidden(hide_binning)
