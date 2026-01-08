# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QPushButton, QCheckBox, \
     QGroupBox
from PyQt5.QtGui import QDoubleValidator

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter

LOG = getLogger(__name__)

BoundType = tuple[float | None, float | None]


class FittingParamFormWidget(QWidget):
    """
    From for inputting and viewing fitting parameters.

    Shows a row for each parameter in the current fitting model, with initial and final values, and controls to fix
    and set ranges.
    Has controls for getting initial parameters and running a fit.
    Has space to show goodness of fit measures.
    """

    def __init__(self, presenter: SpectrumViewerWindowPresenter, parent=None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        main_layout = QVBoxLayout(self)
        self.params_layout = QVBoxLayout()
        main_layout.addLayout(self.params_layout)

        header = QHBoxLayout()
        header.addWidget(QLabel(""), 1)
        header.addWidget(QLabel("Initial"), 2)
        header.addWidget(QLabel("Final"), 2)
        header.addWidget(QLabel("Fix"), 1)
        header.addWidget(QLabel("Range"), 1)
        self.params_layout.addLayout(header)
        self._rows: dict[str, tuple[QWidget, ...]] = {}

        self.from_roi_button = QPushButton("From ROI")
        self.layout().addWidget(self.from_roi_button)
        self.from_roi_button.clicked.connect(self.presenter.get_init_params_from_roi)

        self.run_fit_button = QPushButton("Run fit")
        self.layout().addWidget(self.run_fit_button)
        self.run_fit_button.clicked.connect(self.presenter.run_region_fit)
        self._param_values_logged = False

        self.rss_label = QLabel("RSS:")
        self.reduced_rss_label = QLabel("RSS/DoF:")
        main_layout.addWidget(self.rss_label)
        main_layout.addWidget(self.reduced_rss_label)

    def set_parameters(self, params: list[str]) -> None:
        """
        Set parameters in the widget.
        :param params: List of parameter names
        """
        self.clear_rows()

        for label in params:
            row_layout = QHBoxLayout()
            row_label = QLabel(str(label))
            initial_edit = QLineEdit(str(0.0))
            final_edit = QLineEdit(str(0.0))
            initial_edit.setReadOnly(False)
            final_edit.setReadOnly(True)
            initial_edit.setValidator(QDoubleValidator())
            fix_checkbox = QCheckBox()
            range_checkbox = QCheckBox()
            range_checkbox.stateChanged.connect(self.show_range_edit_fields)
            fix_checkbox.stateChanged.connect(self.set_fixed_parameters)

            row_layout.addWidget(row_label, 1)
            row_layout.addWidget(initial_edit, 2)
            row_layout.addWidget(final_edit, 2)
            row_layout.addWidget(fix_checkbox, 1)
            row_layout.addWidget(range_checkbox, 1)

            self.params_layout.addLayout(row_layout)

            min_label = QLabel("min " + str(label) + ":")
            min_edit = QLineEdit(str(0.0))
            min_edit.setValidator(QDoubleValidator())
            max_label = QLabel("max " + str(label) + ":")
            max_edit = QLineEdit(str(0.0))
            max_edit.setValidator(QDoubleValidator())

            range_row_box = QGroupBox()
            range_row_box_layout = QHBoxLayout()

            range_row_box_layout.addWidget(min_label, 1)
            range_row_box_layout.addWidget(min_edit, 2)
            range_row_box_layout.addWidget(max_label, 1)
            range_row_box_layout.addWidget(max_edit, 2)

            range_row_box.setLayout(range_row_box_layout)

            self.params_layout.addWidget(range_row_box)
            range_row_box.hide()

            self._rows[label] = (row_layout, row_label, initial_edit, final_edit, fix_checkbox, range_checkbox,
                                 range_row_box)

            initial_edit.editingFinished.connect(self.presenter.on_initial_params_edited)

    def set_parameter_values(self, values: dict[str, float]) -> None:
        for name, value in values.items():
            row = self._rows[name]
            row[2].setText(f"{value:f}")

        if not self._param_values_logged:
            LOG.info("Final fit parameter values updated: %s", values)
            self._param_values_logged = True

    def set_fitted_parameter_values(self, values: dict[str, float]) -> None:
        for name, value in values.items():
            row = self._rows[name]
            row[3].setText(f"{value:f}")
        LOG.debug("Final fit parameter values updated: %s", values)

    def get_initial_param_values(self) -> list[float]:
        params = [float(row[2].text()) for row in self._rows.values()]
        return params

    def clear_rows(self) -> None:
        """
        Remove all existing rows from the widget.
        """
        for row_layout, *widgets in self._rows.values():
            for widget in widgets:
                widget.setParent(None)
            self.params_layout.layout().removeItem(row_layout)
        self._rows.clear()
        LOG.debug("Parameter form rows cleared")

    def set_fit_quality(self, rss: float, rss_per_dof: float) -> None:
        """
        Update the fit quality display with raw and reduced residual sum of squares.
        """
        self.rss_label.setText(f"RSS: {rss:.2g}")
        self.reduced_rss_label.setText(f"RSS/DoF: {rss_per_dof:.2g}")

    def show_range_edit_fields(self) -> None:
        for row in self._rows.values():
            if row[5].isChecked():
                row[4].setChecked(False)
                row[6].show()
            else:
                row[6].hide()

    def set_fixed_parameters(self) -> None:
        for row in self._rows.values():
            if row[4].isChecked():
                row[5].setChecked(False)

    def get_bound_parameters(self) -> list[BoundType]:
        return [self.get_bound(row) for row in self._rows.values()]

    def get_bound(self, row: tuple[QWidget, ...]) -> BoundType:
        if row[4].isChecked():
            return float(row[2].text()), float(row[2].text())
        elif row[5].isChecked():
            return float(row[6].layout().itemAt(1).widget().text()), float(row[6].layout().itemAt(3).widget().text())
        else:
            return None, None
