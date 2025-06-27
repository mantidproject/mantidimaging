# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

LOG = getLogger(__name__)


class ExportDataTableWidget(QWidget):
    """
    A scalable table widget to display export-relevant data for each ROI.
    For integration with the fitting/export tab in the spectrum viewer.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.table_view.setModel(self.model)

        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)

        layout.addWidget(self.table_view)

        self.parameter_names: list[str] = []

    def set_parameters(self, parameter_names: list[str]) -> None:
        """
        Set the column headers dynamically based on the given parameter names.
        Clears any existing data in the table.
        """
        self.parameter_names = parameter_names
        headers = ["ROI Name"] + parameter_names + ["Export Status"]
        self.model.setColumnCount(len(headers))
        self.model.setHorizontalHeaderLabels(headers)

    def update_roi_data(self, roi_name: str, params: dict[str, float], status: str = "Ready") -> None:
        """
        Add or update a row for the specified ROI, populating parameter values and status.
        """
        row_index = self._find_row_by_roi_name(roi_name)
        items = [QStandardItem(roi_name)]

        for param in self.parameter_names:
            value = params[param]
            cell = QStandardItem(f"{value:.3f}")
            cell.setTextAlignment(Qt.AlignCenter)
            items.append(cell)

        status_item = QStandardItem(status)
        status_item.setTextAlignment(Qt.AlignCenter)
        items.append(status_item)

        if row_index is not None:
            for col, item in enumerate(items):
                self.model.setItem(row_index, col, item)
        else:
            self.model.appendRow(items)

        LOG.info("Export table updated: ROI=%s, Params=%s, Status=%s", roi_name, params, status)

    def _find_row_by_roi_name(self, roi_name: str) -> int | None:
        """
        Find the row index for a given ROI name. Returns None if not found.
        """
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).text() == roi_name:
                return row
        return None

    def clear_table(self) -> None:
        """
        Remove all rows from the table.
        """
        self.model.removeRows(0, self.model.rowCount())
        LOG.info("Export table cleared")
