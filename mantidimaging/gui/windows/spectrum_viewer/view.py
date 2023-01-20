# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog, QPushButton, QLabel, QAbstractItemView, QMessageBox

from mantidimaging.core.utility import finder
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .presenter import SpectrumViewerWindowPresenter
from mantidimaging.gui.widgets import RemovableRowTableView
from .spectrum_widget import SpectrumWidget
from mantidimaging.gui.windows.spectrum_viewer.roi_table_model import TableModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID
    import numpy as np


class SpectrumViewerWindowView(BaseMainWindowView):
    tableView: RemovableRowTableView
    sampleStackSelector: DatasetSelectorWidgetView
    normaliseStackSelector: DatasetSelectorWidgetView

    normaliseCheckBox: QCheckBox
    imageLayout: QVBoxLayout
    exportButton: QPushButton
    normaliseErrorIcon: QLabel
    _current_dataset_id: Optional['UUID']
    normalise_error_issue: str = ""

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window

        icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
        self.normalise_error_icon_pixmap = QPixmap(icon_path)

        self.presenter = SpectrumViewerWindowPresenter(self, main_window)

        self.spectrum = SpectrumWidget(self)
        self.imageLayout.addWidget(self.spectrum)

        self.spectrum.range_changed.connect(self.presenter.handle_range_slide_moved)
        # Where roi signal is omitted from spectrum_widget.py to be updated on change
        self.spectrum.roi_changed.connect(self.presenter.handle_roi_moved)

        self._current_dataset_id = None
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_normalise_stack_change)
        self.normaliseCheckBox.stateChanged.connect(self.set_normalise_dropdown_state)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_enable_normalised)

        # ROI action buttons
        self.addBtn.clicked.connect(self.set_new_roi)
        self.removeBtn.clicked.connect(self.remove_roi)

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.normaliseStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.try_to_select_relevant_normalise_stack("Flat")

        self.exportButton.clicked.connect(self.presenter.handle_export_csv)

        # Point table
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.tableView.setAlternatingRowColors(True)

        self.selected_row_data: list = []
        self.selected_row: int = 0
        self.current_roi: str = ""

        self.roi_table_model  # Initialise model

        def on_row_change(item, _) -> None:
            """
            Handle cell change in table view and update selected ROI and
            toggle visibility of action buttons

            @param item: item in table
            """
            self.removeBtn.setEnabled(False)
            self.selected_row_data = self.roi_table_model.row_data(item.row())

            if self.selected_row_data[0] != 'roi':
                self.removeBtn.setEnabled(True)
                self.selected_row = item.row()
                self.current_roi = self.selected_row_data[0]

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)

        def on_data_change() -> None:
            """
            Handle ROI name change for a selected ROI and update the ROI name in the spectrum widget

            If the ROI name is empty or already exists in the table that is not the selected row,
            a warning popup will be displayed and the ROI name will be reverted to the previous name
            """

            if self.selected_row_data[0].lower() not in ["", "all", "roi"]:
                for roi_item in range(self.roi_table_model.rowCount()):
                    existing_roi_name = self.roi_table_model.row_data(roi_item)[0].lower()
                    if existing_roi_name == self.selected_row_data[0].lower() and roi_item != self.selected_row:
                        QMessageBox.warning(self, "Duplication Warning", "ROI name already exists")
                        self.selected_row_data[0] = self.current_roi
                        return
                self.presenter.rename_roi(self.current_roi, str(self.selected_row_data[0]))
                return
            QMessageBox.warning(self, "ROI Name Warning",
                                "ROI name cannot be empty or equal to default names: 'all', 'roi'")
            self.selected_row_data[0] = self.current_roi

        self.roi_table_model.dataChanged.connect(on_data_change)

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.normaliseStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    @property
    def roi_table_model(self):
        default_state = self.presenter.get_default_table_state()
        if self.tableView.model() is None:
            mdl = TableModel([default_state])
            self.tableView.setModel(mdl)
        return self.tableView.model()

    @property
    def current_dataset_id(self) -> Optional['UUID']:
        return self._current_dataset_id

    @current_dataset_id.setter
    def current_dataset_id(self, uuid: Optional['UUID']) -> None:
        self._current_dataset_id = uuid

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView) -> None:
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)

    def set_normalise_dropdown_state(self) -> None:
        if self.normaliseCheckBox.isChecked():
            self.normaliseStackSelector.setEnabled(True)
        else:
            self.normaliseStackSelector.setEnabled(False)

    def try_to_select_relevant_normalise_stack(self, name: str) -> None:
        self.normaliseStackSelector.try_to_select_relevant_stack(name)

    def get_normalise_stack(self) -> Optional['UUID']:
        return self.normaliseStackSelector.current()

    def get_csv_filename(self) -> Optional[Path]:
        path = QFileDialog.getSaveFileName(self, "Save CSV file", "", "CSV file (*.csv)")[0]
        if path:
            return Path(path)
        else:
            return None

    def set_image(self, image_data: Optional['np.ndarray'], autoLevels: bool = True):
        self.spectrum.image.setImage(image_data, autoLevels=autoLevels)

    def set_spectrum(self, spectrum_data: 'np.ndarray'):
        self.spectrum.spectrum.clearPlots()
        self.spectrum.spectrum.plot(spectrum_data)

    def clear(self) -> None:
        self.spectrum.clear_data()

    def auto_range_image(self):
        self.spectrum.image.vb.autoRange()

    def set_normalise_error(self, norm_issue: str):
        self.normalise_error_issue = norm_issue

        self.display_normalise_error()

    def display_normalise_error(self):
        if self.normalise_error_issue and self.normaliseCheckBox.isChecked():
            self.normaliseErrorIcon.setPixmap(self.normalise_error_icon_pixmap)
            self.normaliseErrorIcon.setToolTip(self.normalise_error_issue)
        else:
            self.normaliseErrorIcon.setPixmap(QPixmap())
            self.normaliseErrorIcon.setToolTip("")

    def set_new_roi(self) -> None:
        """
        Set a new ROI on the image
        """
        self.presenter.do_add_roi()

    def set_export_button_enabled(self, enabled: bool):
        """
        Toggle enabled state of the export button

        @param enabled: True to enable the button, False to disable it
        """
        self.exportButton.setEnabled(enabled)

    def add_roi_table_row(self, row: int, name: str, colour: str):
        """
        Add a new row to the ROI table

        @param row: The row number
        @param name: The name of the ROI
        @param colour: The colour of the ROI
        """
        circle_label = QLabel()
        circle_label.setStyleSheet(f"background-color: {colour}; border-radius: 5px;")
        self.roi_table_model.appendNewRow(name, colour)
        self.tableView.selectRow(row)

    def remove_roi(self) -> None:
        """
        Clear the selected ROI in the table view
        """
        if self.selected_row_data:
            self.roi_table_model.remove_row(self.selected_row)
            self.presenter.do_remove_roi(self.selected_row_data[0])
            self.removeBtn.setEnabled(False)

    def clear_all_rois(self) -> None:
        """
        Clear all ROIs from the table view
        """
        self.roi_table_model.clear_table()
