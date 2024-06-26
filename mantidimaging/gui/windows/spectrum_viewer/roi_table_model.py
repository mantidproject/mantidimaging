# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import cast, overload, Literal

# Contains ROI table model class which will be used to store ROI information
# and display it in the spectrum viewer.

# Dependencies
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt5.QtGui import QColor, QBrush

ElementType = str | tuple[int, int, int] | bool
RowType = list[ElementType]


class TableModel(QAbstractTableModel):
    """
    A subclass of QAbstractTableModel.
    Model for table view of ROI names and colours in Spectrum Viewer window to allow
    user to select which ROIs to plot.
    """

    def __init__(self) -> None:
        super().__init__()
        self._data: list[RowType] = []

    def rowCount(self, *args, **kwargs) -> int:
        """
        Return number of rows in table

        @return: number of rows in table
        """
        return len(self._data)

    def columnCount(self, *args, **kwargs) -> int:
        """
        Return number of columns in table

        @return: number of columns in table
        """
        return 3

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
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

    def update_color(self, row: int, new_color: tuple[int, int, int]) -> None:
        if 0 <= row < len(self._data):
            self._data[row][1] = new_color
            index = self.index(row, 1)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.BackgroundRole])

    def setData(self, index: QModelIndex, value: ElementType, role: Qt.ItemDataRole) -> bool:
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
        return False

    def row_data(self, row: int) -> RowType:
        """
        Return data from selected row

        @param row: row number
        @return: data from selected rows
        """
        return self._data[row]

    def __getitem__(self, item: int) -> RowType:
        return self.row_data(item)

    @overload
    def get_element(self, row: int, column: Literal[0]) -> str:
        ...

    @overload
    def get_element(self, row: int, column: Literal[1]) -> tuple[int, int, int]:
        ...

    @overload
    def get_element(self, row: int, column: Literal[2]) -> bool:
        ...

    def get_element(self, row: int, column: int) -> ElementType:
        return self.row_data(row)[column]

    def set_element(self, row: int, column: int, value: ElementType) -> None:
        self.row_data(row)[column] = value

    def column_data(self, column: int) -> list[ElementType]:
        """
        Return data from selected column

        @param column: column number
        @return: data from selected column
        """
        return [row[column] for row in self._data]

    def appendNewRow(self, roi_name: str, roi_colour: tuple[int, int, int], visible: bool) -> None:
        """
        Append new row to table

        @param roi_name: ROI name
        @param roi_colour: ROI colour
        """
        item_list: RowType = [roi_name, roi_colour, visible]
        self._data.append(item_list)
        self.layoutChanged.emit()

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole) -> str | None:
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
        return None

    def clear_table(self) -> None:
        """
        Clear all data in table except 'roi' (first element in _data list)
        """
        self._data = []
        self.layoutChanged.emit()

    def remove_row(self, row: int) -> None:
        """
        Remove selected row from table

        @param row: row number
        """
        if row >= 0 and row < len(self._data):
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

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
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

    def roi_names(self) -> list[str]:
        """
        Return list of ROI names

        @return: list of ROI names
        """
        return [cast(str, x[0]) for x in self._data]
