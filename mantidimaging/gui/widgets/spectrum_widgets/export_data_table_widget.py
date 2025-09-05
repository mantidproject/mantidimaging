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
        headers = ["ROI Name"] + parameter_names + ["χ²", "Export Status"]
        self.model.setColumnCount(len(headers))
        self.model.setHorizontalHeaderLabels(headers)

    def update_roi_data(
        self,
        roi_name: str,
        params: dict[str, float],
        status: str = "Ready",
        chi2: float | None = None,
    ) -> None:
        """
        Add or update a row for the specified ROI, populating parameter values, χ², and status.
        """
        row_index = self._find_row_by_roi_name(roi_name)
        name_item = QStandardItem(roi_name)
        name_item.setData(roi_name)
        items = [name_item]

        for param in self.parameter_names:
            value = params[param]
            cell = QStandardItem(f"{value:.4g}")
            cell.setData(f"{value:.6g}")
            cell.setTextAlignment(Qt.AlignCenter)
            items.append(cell)

        chi2_item = self._make_chi2_item(chi2)
        items.append(chi2_item)
        status_item = QStandardItem(status)
        status_item.setData(status)
        status_item.setTextAlignment(Qt.AlignCenter)
        items.append(status_item)

        if row_index is not None:
            for col, item in enumerate(items):
                self.model.setItem(row_index, col, item)
        else:
            self.model.appendRow(items)

        LOG.info("Export table updated: ROI=%s, Params=%s, chi2=%s, Status=%s", roi_name, params, chi2, status)

    def set_chi2(self, roi_name: str, chi2: float | None) -> None:
        """
        Update only the χ² cell for the given ROI (if the row exists).
        """
        row_index = self._find_row_by_roi_name(roi_name)
        if row_index is None:
            return
        chi2_col = 1 + len(self.parameter_names)
        self.model.setItem(row_index, chi2_col, self._make_chi2_item(chi2))
        LOG.debug("Export table χ² updated: ROI=%s, chi2=%s", roi_name, chi2)

    def _make_chi2_item(self, chi2: float | None) -> QStandardItem:
        if chi2 is None:
            text, data = "N/A", "N/A"
        else:
            text, data = f"{chi2:.3g}", f"{chi2:.6g}"
        item = QStandardItem(text)
        item.setData(data)
        item.setTextAlignment(Qt.AlignCenter)
        return item

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
