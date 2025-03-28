# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal, QSignalBlocker

from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BaseWidget

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTabWidget, QComboBox, QPushButton, QSpinBox, QLabel, QGroupBox
    from mantidimaging.gui.windows.spectrum_viewer.view import ROITableWidget


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


class ROIPropertiesTableWidget(BaseWidget):
    spin_left: QSpinBox
    spin_right: QSpinBox
    spin_top: QSpinBox
    spin_bottom: QSpinBox
    label_height: QLabel
    label_width: QLabel
    group_box: QGroupBox

    roi_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, ui_file='gui/ui/roi_properties_table_widget.ui')

        self.spin_boxes = [self.spin_left, self.spin_right, self.spin_top, self.spin_bottom]

        for spin_box in self.spin_boxes:
            spin_box.valueChanged.connect(self.roi_changed.emit)

    def set_roi_name(self, name: str) -> None:
        self.group_box.setTitle(f"Roi Properties: {name}")

    def set_roi_values(self, roi: SensibleROI) -> None:
        with QSignalBlocker(self):
            self.spin_left.setValue(roi.left)
            self.spin_right.setValue(roi.right)
            self.spin_top.setValue(roi.top)
            self.spin_bottom.setValue(roi.bottom)
            self.label_width.setText(str(roi.width))
            self.label_height.setText(str(roi.height))

    def set_roi_limits(self, shape: tuple[int, ...]) -> None:
        self.spin_left.setMaximum(shape[1])
        self.spin_right.setMaximum(shape[1])
        self.spin_top.setMaximum(shape[0])
        self.spin_bottom.setMaximum(shape[0])

    def as_roi(self) -> SensibleROI:
        new_roi = SensibleROI(left=self.spin_left.value(),
                              right=self.spin_right.value(),
                              top=self.spin_top.value(),
                              bottom=self.spin_bottom.value())
        return new_roi

    def enable_widgets(self, enable: bool) -> None:
        for spin_box in self.spin_boxes:
            spin_box.setEnabled(enable)
        if not enable:
            self.set_roi_values(SensibleROI(0, 0, 0, 0))
