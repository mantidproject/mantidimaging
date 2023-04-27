# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Tuple, List

# Contains ROI table model class which will be used to store ROI information
# and display it in the spectrum viewer.

# Dependencies
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt5.QtGui import QColor, QBrush


class TableModel(QAbstractTableModel):  # type: ignore
    """
    A subclass of QAbstractTableModel.
    Model for table view of ROI names and colours in Spectrum Viewer window to allow
    user to select which ROIs to plot.


    @param data: list of lists of ROI names and colours [str, tuple(int,int,int)]
    """
    def __init__(self, data: List[List[str | Tuple[int, int, int]]]) -> None:
        super(TableModel, self).__init__()
        self._data: List[List[str | Tuple[int, int, int]]] = data

    def rowCount(self, *args, **kwargs) -> int:  # type: ignore
        """
        Return number of rows in table

        @return: number of rows in table
        """
        return len(self._data)

    def columnCount(self, *args, **kwargs) -> int:  # type: ignore
        """
        Return number of columns in table

        @return: number of columns in table
        """
        return len(self._data[0])

    def data(self, index: QModelIndex, role: int) -> QBrush:
        """
        Set data in table roi name and colour - str and Tuple(int,int,int)
        and set background colour of colour column

        @param index: index of selected row
        @param role: Qt.DisplayRole or Qt.BackgroundRole
        @return: ROI name or colour values and background colour of colour column
        """
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        if role == Qt.BackgroundRole:
            if index.column() == 1:
                return QBrush(QColor(*self._data[index.row()][index.column()]))

    # edit roi name on double click
    def setData(self, index: QModelIndex, value: str, role: int) -> bool:
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
        return False

    def row_data(self, row: int) -> List[str | Tuple[int, int, int]]:
        """
        Return data from selected row

        @param row: row number
        @return: data from selected rows
        """
        return self._data[row]

    def appendNewRow(self, roi_name: str, roi_colour: tuple[int, int, int]) -> None:
        """
        Append new row to table

        @param roi_name: ROI name
        @param roi_colour: ROI colour
        """
        item_list = [roi_name, roi_colour]
        self._data.append(item_list)  # type: ignore
        self.layoutChanged.emit()

    def sort_points(self) -> None:
        """
        Sort table by ROI name
        """
        self._data.sort(key=lambda x: x[0])

    def headerData(self, section: int, orientation: int, role: int) -> str:
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

    def flags(self, index: QModelIndex) -> int:
        """
        Handle selection of table rows to disable selection of ROI colour column
        if index is equal to roi, item not editable

        @param index: index of selected row
        @return: Qt.ItemIsEnabled | Qt.ItemIsSelectable
        """
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable  # type: ignore
        else:
            return Qt.ItemIsEnabled  # type: ignore

    def roi_names(self) -> list[str]:
        """
        Return list of ROI names

        @return: list of ROI names
        """
        return [x[0] for x in self._data]  # type: ignore
