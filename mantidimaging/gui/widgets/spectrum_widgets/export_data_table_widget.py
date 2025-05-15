# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class ExportDataTableWidget(QWidget):
    """
    A scalable table widget to display export-relevant data for each ROI.
    Intended for integration with the fitting/export tab in the spectrum viewer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(0, 4, self)
        self.model.setHorizontalHeaderLabels(["ROI Name", "μ (mu)", "σ (sigma)", "Export Status"])
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)

        layout.addWidget(self.table_view)

    def update_roi_data(self, roi_name: str, params: dict[str, float], status: str = "Ready") -> None:
        """
        Add or update a row for the given ROI.
        """
        existing_row = self._find_row_by_roi_name(roi_name)
        items = [
            QStandardItem(roi_name),
            QStandardItem(f"{params.get('mu', 0):.3f}"),
            QStandardItem(f"{params.get('sigma', 0):.3f}"),
            QStandardItem(status),
        ]
        for item in items:
            item.setTextAlignment(Qt.AlignCenter)

        if existing_row is not None:
            for col, item in enumerate(items):
                self.model.setItem(existing_row, col, item)
        else:
            self.model.appendRow(items)

    def _find_row_by_roi_name(self, roi_name: str) -> int | None:
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).text() == roi_name:
                return row
        return None

    def clear_table(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
