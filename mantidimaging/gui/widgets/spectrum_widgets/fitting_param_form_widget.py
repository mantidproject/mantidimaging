# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QPushButton, QComboBox)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import pyqtSignal

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter

LOG = getLogger(__name__)


class FittingParamFormWidget(QWidget):
    """
    Scalable widget to display ROI parameters with Initial and Final values.
    """
    metric_changed = pyqtSignal(str)

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
        self.params_layout.addLayout(header)
        self._rows: dict[str, tuple[QWidget, ...]] = {}

        self.from_roi_button = QPushButton("From ROI")
        self.layout().addWidget(self.from_roi_button)
        self.from_roi_button.clicked.connect(self.presenter.get_init_params_from_roi)

        self.run_fit_button = QPushButton("Run fit")
        self.layout().addWidget(self.run_fit_button)
        self.run_fit_button.clicked.connect(self.presenter.run_region_fit)
        self._param_values_logged = False

        self.chi2_label = QLabel("Fitting Quality (χ²): N/A")
        main_layout.addWidget(self.chi2_label)
        self.metric_picker = QComboBox(self)
        self.metric_picker.addItems([
            "χ² (SSE)",
            "Reduced χ² (unweighted)",
            "Reduced χ² (σ-weighted)",
        ])
        try:
            self.metric_picker.setCurrentIndex(1)
        except Exception:
            pass
        self.metric_picker.currentTextChanged.connect(self.metric_changed)
        main_layout.addWidget(self.metric_picker)

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
            initial_edit.setReadOnly(False)
            final_edit.setReadOnly(True)
            initial_edit.setValidator(QDoubleValidator())

            row_layout.addWidget(row_label, 1)
            row_layout.addWidget(initial_edit, 2)
            row_layout.addWidget(final_edit, 2)

            self.params_layout.addLayout(row_layout)
            self._rows[label] = (row_layout, row_label, initial_edit, final_edit)

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

    def get_fitted_param_values(self) -> list[float]:
        params = [float(row[3].text()) for row in self._rows.values()]
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

    def set_chi_squared(self, chi2: float) -> None:
        if np.isnan(chi2) or np.isinf(chi2):
            self.chi2_label.setText("Fitting Quality (χ²): N/A")
        else:
            self.chi2_label.setText(f"Fitting Quality (χ²): {chi2:.2f}")
    set_fit_quality = set_chi_squared

    def current_metric(self) -> str:
        """Return the currently selected metric label from the picker."""
        try:
            return self.metric_picker.currentText()
        except Exception:
            return "χ² (SSE)"
