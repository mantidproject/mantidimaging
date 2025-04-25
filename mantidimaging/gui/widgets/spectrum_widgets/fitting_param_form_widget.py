# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QPushButton


class FittingParamFormWidget(QWidget):
    """
    Scalable widget to display ROI parameters with Initial and Final values.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.params_layout = QVBoxLayout(self)
        self.layout().addLayout(self.params_layout)

        header = QHBoxLayout()
        header.addWidget(QLabel(""), 1)
        header.addWidget(QLabel("Initial"), 2)
        header.addWidget(QLabel("Final"), 2)
        self.params_layout.addLayout(header)
        self._rows: dict[str, tuple[QWidget, ...]] = {}

        self.from_roi_button = QPushButton("From ROI")
        self.layout().addWidget(self.from_roi_button)

    def set_parameters(self, params: list[str]) -> None:
        """
        Set parameters in the widget.
        :param params: Dict of label -> (initial, final)
        """
        self.clear_rows()

        for label in params:
            row_layout = QHBoxLayout()
            row_label = QLabel(str(label))
            initial_edit = QLineEdit(str(0.0))
            final_edit = QLineEdit(str(0.0))

            for widget in (initial_edit, final_edit):
                widget.setReadOnly(True)

            row_layout.addWidget(row_label, 1)
            row_layout.addWidget(initial_edit, 2)
            row_layout.addWidget(final_edit, 2)

            self.params_layout.addLayout(row_layout)
            self._rows[label] = (row_layout, row_label, initial_edit, final_edit)

    def set_parameter_values(self, values: dict[str, float]) -> None:
        for name, value in values.items():
            row = self._rows[name]
            row[2].setText(str(value))

    def clear_rows(self) -> None:
        """
        Remove all existing rows from the widget.
        """
        for row_layout, *widgets in self._rows.values():
            for widget in widgets:
                widget.setParent(None)
            self.params_layout.layout().removeItem(row_layout)
        self._rows.clear()
