# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from mantidimaging.core.utility.sensible_roi import ROIBinner
from mantidimaging.gui.windows.spectrum_viewer.model import ROI_RITS
from PyQt5 import QtWidgets, QtCore
from logging import getLogger

from mantidimaging.gui.windows.spectrum_viewer.presenter import ExportMode

LOG = getLogger(__name__)


class ROISelectionWidget(QtWidgets.QGroupBox):
    """
    A custom Qt widget for selecting an ROI.
    Attributes:
        roiDropdown: A dropdown menu for selecting ROIs.
        selectionChanged: Signal emitted when the ROI selection changes.
    """

    selectionChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__("Select ROI", parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        self.roiDropdown = QtWidgets.QComboBox(self)
        self.roiDropdown.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.roiDropdown)
        self.previous_selection = None

        self.subroiRow = QtWidgets.QWidget()
        subroi_row_layout = QtWidgets.QHBoxLayout(self.subroiRow)
        self.sub_roi_x_input = QtWidgets.QSpinBox()
        self.sub_roi_y_input = QtWidgets.QSpinBox()
        subroi_row_layout.addWidget(QtWidgets.QLabel("Roi bin"))
        subroi_row_layout.addWidget(self.sub_roi_x_input)
        subroi_row_layout.addWidget(self.sub_roi_y_input)
        self.sub_roi_x_input.setToolTip("Bin x coordinate (from left)")
        self.sub_roi_y_input.setToolTip("Bin y coordinate (from top)")
        self.sub_roi_x_input.valueChanged.connect(self._on_sub_roi_changed)
        self.sub_roi_y_input.valueChanged.connect(self._on_sub_roi_changed)
        layout.addWidget(self.subroiRow)
        self.subroiRow.hide()

    def _on_selection_changed(self) -> None:
        """ Handle dropdown selection change and emit signal. """
        selected_roi = self.roiDropdown.currentText()
        if selected_roi != self.previous_selection:
            self.previous_selection = selected_roi
            LOG.info("ROI selected: %s", selected_roi)
            self.selectionChanged.emit(selected_roi)

    def update_roi_list(self, roi_names: list[str]) -> None:
        """ Update the dropdown and trigger selection change if needed. """
        current_selection = self.roiDropdown.currentText()
        self.roiDropdown.blockSignals(True)
        self.roiDropdown.clear()
        filtered_rois = [name for name in roi_names if str(name) != str(ROI_RITS)]
        self.roiDropdown.addItems(filtered_rois)
        if current_selection in filtered_rois:
            self.roiDropdown.setCurrentText(current_selection)
        elif filtered_rois:
            self.roiDropdown.setCurrentIndex(0)
            self._on_selection_changed()
            self._on_selection_changed()
        self.roiDropdown.blockSignals(False)
        LOG.debug("ROI dropdown updated: %s", filtered_rois)

    def set_selected_roi(self, roi_name: str) -> None:
        """ Set the dropdown selection to the given ROI name. """
        index = self.roiDropdown.findText(roi_name)
        if index != -1:
            self.roiDropdown.setCurrentIndex(index)

    def _on_sub_roi_changed(self) -> None:
        """ Handle sub-ROI coordinate changes and emit selection change signal. """
        self.selectionChanged.emit(self.current_roi_name)

    @property
    def current_roi_name(self) -> str:
        """Returns the currently selected ROI name from the dropdown."""
        return self.roiDropdown.currentText()

    @property
    def current_sub_roi_coordinates(self) -> tuple[int, int]:
        """Returns the current sub-ROI coordinates from the spin boxes."""
        return self.sub_roi_x_input.value(), self.sub_roi_y_input.value()

    def handle_mode_change(self, mode: ExportMode) -> None:
        self.roiDropdown.setVisible(mode == ExportMode.ROI_MODE)
        self.subroiRow.setVisible(mode == ExportMode.IMAGE_MODE)

    def handle_binning_changed(self, binner: ROIBinner) -> None:
        x_len, y_len = binner.lengths()
        max_x = max(0, x_len - 1)
        max_y = max(0, y_len - 1)
        self.sub_roi_x_input.setMaximum(max_x)
        self.sub_roi_y_input.setMaximum(max_y)
