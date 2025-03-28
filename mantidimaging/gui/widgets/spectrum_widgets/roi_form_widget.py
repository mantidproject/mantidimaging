# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt5.QtCore import pyqtSignal, QSignalBlocker, QModelIndex
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BaseWidget
from mantidimaging.gui.widgets import RemovableRowTableView
from mantidimaging.gui.windows.spectrum_viewer.roi_table_model import TableModel

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTabWidget, QComboBox, QPushButton, QSpinBox, QLabel, QGroupBox


class ROIFormWidget(BaseWidget):
    exportTabs: QTabWidget
    roi_properties_widget: ROIPropertiesTableWidget
    table_view: ROITableWidget
    image_output_mode_combobox: QComboBox
    addBtn: QPushButton
    removeBtn: QPushButton
    exportButton: QPushButton
    exportButtonRITS: QPushButton
    transmission_error_mode_combobox: QComboBox
    bin_size_spinBox: QSpinBox
    bin_step_spinBox: QSpinBox

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


class ROITableWidget(RemovableRowTableView):
    """
    A class to represent the ROI table widget in the spectrum viewer window.
    """
    ElementType = str | tuple[int, int, int] | bool
    RowType = list[ElementType]
    selected_row: int

    selection_changed = pyqtSignal()
    name_changed = pyqtSignal(str, str)
    visibility_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected_row = 0

        # Point table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)

        # Initialise model
        self.roi_table_model = TableModel()
        self.setModel(self.roi_table_model)

        # Configure up the table view
        self.setVisible(True)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.selectionModel().currentRowChanged.connect(self.on_row_change)
        self.roi_table_model.name_changed.connect(self.name_changed.emit)
        self.roi_table_model.visibility_changed.connect(self.visibility_changed.emit)

    def on_row_change(self, item: QModelIndex, _: Any) -> None:
        self.selected_row = item.row()
        self.selection_changed.emit()

    def get_roi_names(self) -> list[str]:
        return self.roi_table_model.roi_names()

    def get_roi_name_by_row(self, row: int) -> str:
        """
        Retrieve the name an ROI by its row index.
        """
        return self.roi_table_model.get_element(row, 0)

    @property
    def current_roi_name(self) -> str:
        return self.get_roi_name_by_row(self.selected_row)

    def get_roi_visibility_by_row(self, row: int) -> bool:
        """
        Retrieve the visibility status of an ROI by its row index.
        """
        return self.roi_table_model.get_element(row, 2)

    def row_count(self) -> int:
        """
        Returns the number of rows in the ROI table model.
        """
        return self.roi_table_model.rowCount()

    def find_row_for_roi(self, roi_name: str) -> int | None:
        """
        Returns row index for ROI name, or None if not found.
        """
        for row in range(self.roi_table_model.rowCount()):
            if self.roi_table_model.index(row, 0).data() == roi_name:
                return row
        return None

    def update_roi_color(self, roi_name: str, new_color: tuple[int, int, int, int]) -> None:
        """
        Finds ROI by name in table and updates it's colour (R, G, B) format.
        """
        row = self.find_row_for_roi(roi_name)
        if row is not None:
            self.roi_table_model.update_color(row, new_color)

    def add_row(self, name: str, colour: tuple[int, int, int, int], roi_names: list[str]) -> None:
        """
        Add a new row to the ROI table
        """
        self.roi_table_model.appendNewRow(name, colour, True)
        self.selected_row = self.roi_table_model.rowCount() - 1
        self.selectRow(self.selected_row)

    def remove_row(self, row: int) -> None:
        """
        Remove a row from the ROI table
        """
        self.roi_table_model.remove_row(row)
        self.selectRow(0)

    def clear_table(self) -> None:
        """
        Clears the ROI table in the spectrum viewer.
        """
        self.roi_table_model.clear_table()

    def select_roi(self, roi_name: str) -> None:
        selected_row = self.find_row_for_roi(roi_name)
        assert selected_row is not None
        self.selectRow(selected_row)
