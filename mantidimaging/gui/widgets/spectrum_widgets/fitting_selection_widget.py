# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import inspect

from mantidimaging.core.fitting import fitting_functions
from PyQt5 import QtWidgets, QtCore

from mantidimaging.core.fitting.fitting_functions import BaseFittingFunction
import logging

LOG = logging.getLogger(__name__)


class FitSelectionWidget(QtWidgets.QGroupBox):
    """
    A custom Qt widget for selecting an Fitting Model.
    Attributes:
        fitDropdown: A dropdown menu for selecting fits.
        func_dict: A dictionary for storing fitting functions available in the viewer.
        selectionChanged: Signal emitted when the fit selection changes.
    """
    func_dict: dict[str, type[BaseFittingFunction]] = {}
    selectionChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__("Select Fitting Function", parent)

        self.setFixedHeight(60)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        self.fitDropdown = QtWidgets.QComboBox(self)
        self.fitDropdown.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.fitDropdown)
        self.previous_selection = None

        for _, obj in inspect.getmembers(fitting_functions):
            if inspect.isclass(obj) and (issubclass(obj, fitting_functions.BaseFittingFunction)
                                         and obj is not fitting_functions.BaseFittingFunction):
                self.func_dict.update({obj.function_name: obj})

        self.set_available_fitting_functions()

    def _on_selection_changed(self) -> None:
        """ Handle dropdown selection change and emit signal. """
        selected_fit = self.fitDropdown.currentText()
        self.selectionChanged.emit(self.func_dict[selected_fit])
        LOG.info("Fit function selected: %s", self.fitDropdown.currentText())

    def set_available_fitting_functions(self) -> None:
        """ Update the dropdown and trigger selection change if needed. """
        self.fitDropdown.blockSignals(True)
        self.fitDropdown.clear()
        self.fitDropdown.addItems(list(self.func_dict.keys()))
        self.fitDropdown.blockSignals(False)

    @property
    def current_fit_name(self) -> str:
        """Returns the currently selected fit from the dropdown."""
        return self.fitDropdown.currentText()
