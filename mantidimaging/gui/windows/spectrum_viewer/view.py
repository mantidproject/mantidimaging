# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from enum import Enum

from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QPixmap, QColor, QBrush
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog, QPushButton, QLabel, QAbstractItemView

from mantidimaging.core.utility import finder
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .presenter import SpectrumViewerWindowPresenter
from mantidimaging.gui.widgets import RemovableRowTableView
from .spectrum_widget import SpectrumWidget

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID
    import numpy as np


class Column(Enum):
    name = 0
    colour = 1


class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        print((f"Data is {self._data}"))

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def data(self, index, role):
        """
        Set data in table roi name and colour - str and Tuple(int,int,int)
        """
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        # if role == Qt.ForegroundRole:
        #     if index.column() == 1:
        #         return QColor(*self._data[index.row()][index.column()])
        # change text colour?
        if role == Qt.BackgroundRole:
            if index.column() == 1:
                return QBrush(QColor(*self._data[index.row()][index.column()]))
                # return QColor(*self._data[index.row()][index.column()])

    def appendNewRow(self, row: int, roi_name: str, roi_colour: tuple):
        print(f"Appending new row {row} with {roi_name} and {roi_colour}")
        item_list = [roi_name, roi_colour]
        self._data.append(item_list)

        self.layoutChanged.emit()

    # def set_point(self, row: int, roi_name: str, roi_colour: tuple):
    #     """
    #     Set data str and tuple in table
    #     """
    #     item = self._data[row]
    #     self.dataChanged.emit(self.index(row, 0), self.index(row, 1))

    # def add_point(self, row: int, roi_name: str, roi_colour: tuple):
    #     """
    #     Add new row to table
    #     """
    #     if row is None:
    #         self._data.append([roi_name, roi_colour])
    #     else:
    #         self._data.insert(row, [roi_name, roi_colour])

    # def insertRows(self, row: int, count: int, roi_name: str, roi_colour: tuple):
    #     """
    #     Insert new row of two columns string and tuple
    #     """
    #     self.beginInsertRows(QModelIndex(), row, row + count - 1)
    #     self._data.insert(row, [roi_name, roi_colour])
    #     self.endInsertRows()

    # self.beginInsertRows(QModelIndex(), row, row + count - 1)

    # for _ in range(count):
    #     self.add_point(row, roi_name, roi_colour)

    def sort_points(self):
        """
        Sort table by ROI name
        """
        self._data.sort(key=lambda x: x[0])

    def headerData(self, section, orientation, role):
        """
        Set horizontal colum header names to ROI and Colour
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "ROI"
                if section == 1:
                    return "Colour"


class SpectrumViewerWindowView(BaseMainWindowView):
    tableView: RemovableRowTableView
    sampleStackSelector: DatasetSelectorWidgetView
    normaliseStackSelector: DatasetSelectorWidgetView

    normaliseCheckBox: QCheckBox
    imageLayout: QVBoxLayout
    exportButton: QPushButton
    normaliseErrorIcon: QLabel
    _current_dataset_id: Optional['UUID']
    normalise_error_issue: str = ""

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window

        icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
        self.normalise_error_icon_pixmap = QPixmap(icon_path)

        self.presenter = SpectrumViewerWindowPresenter(self, main_window)

        self.spectrum = SpectrumWidget(self)
        self.imageLayout.addWidget(self.spectrum)

        self.spectrum.range_changed.connect(self.presenter.handle_range_slide_moved)
        # Where roi signal is omitted from spectrum_widget.py to be updated on change
        self.spectrum.roi_changed.connect(self.presenter.handle_roi_moved)

        self._current_dataset_id = None
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_normalise_stack_change)
        self.normaliseCheckBox.stateChanged.connect(self.set_normalise_dropdown_state)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_enable_normalised)

        # Create a new ROI on the image on click
        self.addBtn.clicked.connect(self.set_new_roi)

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.normaliseStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.try_to_select_relevant_normalise_stack("Flat")

        self.exportButton.clicked.connect(self.presenter.handle_export_csv)

        # Point table
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        # self.roi_table_model = self.tableView.model()

        # self.roi_table_model.rowsInserted.connect(self.on_table_row_count_change)  # type: ignore
        # self.roi_table_model.rowsRemoved.connect(self.on_table_row_count_change)  # type: ignore
        # self.roi_table_model.modelReset.connect(self.on_table_row_count_change)  # type: ignore

        # self.roi_table_model.dataChanged.connect()

        # Update initial UI state
        # self.on_table_row_count_change()

    def clear_cor_table(self):
        return self.roi_table_model.removeAllRows()

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.normaliseStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    @property
    def roi_table_model(self):
        print("roi_table_model")
        print(self.tableView)
        data = [
            ["roi", (26, 133, 255)],
        ]
        if self.tableView.model() is None:
            mdl = TableModel(data)
            # mdl = TableModel(self.tableView)
            self.tableView.setModel(mdl)
        return self.tableView.model()

    @property
    def current_dataset_id(self) -> Optional['UUID']:
        return self._current_dataset_id

    @current_dataset_id.setter
    def current_dataset_id(self, uuid: Optional['UUID']) -> None:
        self._current_dataset_id = uuid

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView) -> None:
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)

    def set_normalise_dropdown_state(self) -> None:
        if self.normaliseCheckBox.isChecked():
            self.normaliseStackSelector.setEnabled(True)
        else:
            self.normaliseStackSelector.setEnabled(False)

    def try_to_select_relevant_normalise_stack(self, name: str) -> None:
        self.normaliseStackSelector.try_to_select_relevant_stack(name)

    def get_normalise_stack(self) -> Optional['UUID']:
        return self.normaliseStackSelector.current()

    def get_csv_filename(self) -> Optional[Path]:
        path = QFileDialog.getSaveFileName(self, "Save CSV file", "", "CSV file (*.csv)")[0]
        if path:
            return Path(path)
        else:
            return None

    # def on_table_row_count_change(self, _=None, __=None):
    #     """
    #     Called when rows have been added or removed from the point table.

    #     Used to conditionally enable UI controls that depend on a certain
    #     amount of entries in the table.
    #     """
    #     # Disable clear buttons when there are no rows in the table
    #     empty = self.tableView.model().empty
    #     self.removeBtn.setEnabled(not empty)
    #     self.clearAllBtn.setEnabled(not empty)

    def set_image(self, image_data: Optional['np.ndarray'], autoLevels: bool = True):
        self.spectrum.image.setImage(image_data, autoLevels=autoLevels)

    def set_spectrum(self, spectrum_data: 'np.ndarray'):
        self.spectrum.spectrum.clearPlots()
        self.spectrum.spectrum.plot(spectrum_data)

    def clear(self) -> None:
        self.spectrum.clear_data()

    def auto_range_image(self):
        self.spectrum.image.vb.autoRange()

    def set_normalise_error(self, norm_issue: str):
        self.normalise_error_issue = norm_issue

        self.display_normalise_error()

    def display_normalise_error(self):
        if self.normalise_error_issue and self.normaliseCheckBox.isChecked():
            self.normaliseErrorIcon.setPixmap(self.normalise_error_icon_pixmap)
            self.normaliseErrorIcon.setToolTip(self.normalise_error_issue)
        else:
            self.normaliseErrorIcon.setPixmap(QPixmap())
            self.normaliseErrorIcon.setToolTip("")

    def set_new_roi(self) -> None:
        """
        Set a new ROI on the image
        """
        self.presenter.do_add_roi()

    def set_export_button_enabled(self, enabled: bool):
        """
        Toggle enabled state of the export button

        :param enabled: True to enable the button, False to disable it
        """
        self.exportButton.setEnabled(enabled)

    def add_roi_table_row(self, row: int, name: str, colour: str):
        """
        Add a new row to the ROI table

        :param row: The row number
        :param name: The name of the ROI
        :param colour: The colour of the ROI
        """
        circle_label = QLabel()
        circle_label.setStyleSheet(f"background-color: {colour}; border-radius: 5px;")
        self.roi_table_model.appendNewRow(row, name, colour)
        self.tableView.selectRow(row)
