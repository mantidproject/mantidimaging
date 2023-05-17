# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# Contains ROI table model class which will be used to store ROI information
# and display it in the spectrum viewer.

# Dependencies
from PyQt5.QtCore import QAbstractTableModel, Qt, QItemSelectionModel
from PyQt5.QtGui import QColor, QBrush


class TableModel(QAbstractTableModel):
    """
    A subclass of QAbstractTableModel.
    Model for table view of ROI names and colours in Spectrum Viewer window to allow
    user to select which ROIs to plot.


    @param data: list of lists of ROI names and colours [str, tuple(int,int,int)]
    """
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def selectRow(self, index: int):
        """
        Selects the row at the given index.

        :param index: The index of the row to select.
        """
        selectionModel = self.tableView.selectionModel()
        selectionModel.clearSelection()
        selectionModel.select(self.createIndex(index + 1, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def rowCount(self, *args, **kwargs):
        """
        Return number of rows in table

        @return: number of rows in table
        """
        return len(self._data)

    def columnCount(self, *args, **kwargs):
        """
        Return number of columns in table

        @return: number of columns in table
        """
        return len(self._data[0])

    def data(self, index, role):
        """
        Set data in table roi name and colour - str and Tuple(int,int,int)
        and set background colour of colour column

        @param index: index of selected row
        @param role: Qt.DisplayRole or Qt.BackgroundRole
        @return: ROI name or colour values and background colour of colour column
        """
        if role == Qt.DisplayRole:
            if index.column() == 2:
                return None
            return self._data[index.row()][index.column()]

        if role == Qt.BackgroundRole:
            if index.column() == 1:
                return QBrush(QColor(*self._data[index.row()][index.column()]))

        if role == Qt.CheckStateRole:
            if index.column() == 2:
                if self._data[index.row()][index.column()]:
                    return Qt.Checked
                return Qt.Unchecked

    def setData(self, index, value, role):
        """
        Set data in table

        @param index: index of selected row
        @param value: new value
        @param role: Qt.EditRole
        @return: True
        """
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        if role == Qt.CheckStateRole:
            if index.column() == 2:
                self._data[index.row()][index.column()] = value == Qt.Checked
                self.dataChanged.emit(index, index)
                return True
            self.dataChanged.emit(index, index)
            return False

    def row_data(self, row: int) -> tuple:
        """
        Return data from selected row

        @param row: row number
        @return: data from selected rows
        """
        return self._data[row]

    def column_data(self, column: int) -> list:
        """
        Return data from selected column

        @param column: column number
        @return: data from selected column
        """
        return [row[column] for row in self._data]

    def appendNewRow(self, roi_name: str, roi_colour: tuple, visible: bool):
        """
        Append new row to table

        @param roi_name: ROI name
        @param roi_colour: ROI colour
        """
        item_list = [roi_name, roi_colour, visible]
        self._data.append(item_list)
        self.layoutChanged.emit()

    def sort_points(self):
        """
        Sort table by ROI name
        """
        self._data.sort(key=lambda x: x[0])

    def headerData(self, section, orientation, role):
        """
        Set horizontal colum header names to ROI and Colour

        @param section: column number
        @param orientation: horizontal
        @param role: Qt.DisplayRole
        @return: ROI or Colour
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "ROI"
                if section == 1:
                    return "Colour"
                if section == 2:
                    return ""

    def clear_table(self) -> None:
        """
        Clear all data in table except 'roi' (first element in _data list)
        """
        self._data = self._data[:1]
        self.layoutChanged.emit()

    def remove_row(self, row: int) -> None:
        """
        Remove selected row from table

        @param row: row number
        """
        if row > 0 and row < len(self._data):
            self._data.pop(row)
            self.layoutChanged.emit()

    def rename_row(self, row: int, new_name: str) -> None:
        """
        Rename selected row if new name does not already exist
        in table and is not default 'roi' ROI or duplicate

        @param row: row number
        @param new_name: new ROI name
        @raise ValueError: if new name already exists or is default 'roi' ROI
        """
        if new_name in self.roi_names():
            raise ValueError("ROI name already exists")
        else:
            self._data[row][0] = new_name
            self.layoutChanged.emit()

    def flags(self, index):
        """
        Handle selection of table rows to disable selection of ROI colour column
        if index is equal to roi, item not editable

        @param index: index of selected row
        @return: Qt.ItemIsEnabled | Qt.ItemIsSelectable
        """
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        elif index.column() == 2:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled

    def roi_names(self) -> list:
        """
        Return list of ROI names

        @return: list of ROI names
        """
        return [x[0] for x in self._data]
