# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog, QPushButton, QLabel, QAbstractItemView, QHeaderView

from mantidimaging.core.utility import finder
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .presenter import SpectrumViewerWindowPresenter
from mantidimaging.gui.widgets import RemovableRowTableView
from .spectrum_widget import SpectrumWidget
from mantidimaging.gui.windows.spectrum_viewer.roi_table_model import TableModel

import numpy as np

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID


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

        self.spectrum = SpectrumWidget()
        self.imageLayout.addWidget(self.spectrum)

        self.spectrum.range_changed.connect(self.presenter.handle_range_slide_moved)
        self.spectrum.roi_changed.connect(self.presenter.handle_roi_moved)

        self._current_dataset_id = None
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_normalise_stack_change)
        self.normaliseCheckBox.stateChanged.connect(self.normaliseStackSelector.setEnabled)
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
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setAlternatingRowColors(True)

        self.selected_row: int = 0
        self.current_roi: str = ""
        self.selected_row_data: Optional[list] = None

        _ = self.roi_table_model  # Initialise model

        def on_row_change(item, _) -> None:
            """
            Handle cell change in table view and update selected ROI and
            toggle visibility of action buttons

            @param item: item in table
            """
            selected_row_data = self.roi_table_model.row_data(item.row())
            self.selected_row = item.row()
            self.current_roi = selected_row_data[0]

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)

        def on_visibility_change() -> None:
            """
            When the visibility of an ROI is changed, update the visibility of the ROI in the spectrum widget
            """
            for roi_item in range(self.roi_table_model.rowCount()):
                if self.roi_table_model.row_data(roi_item)[2] is False:
                    self.set_roi_alpha(0, roi_item)
                else:
                    self.set_roi_alpha(255, roi_item)
                    self.presenter.redraw_spectrum(self.roi_table_model.row_data(roi_item)[0])
            return

        def on_data_in_table_change() -> None:
            """
            Check if an ROI name has changed in the table or if the visibility of an ROI has changed.
            If the ROI name has changed, update the ROI name in the spectrum widget.
            If the visibility of an ROI has changed, update the visibility of the ROI in the spectrum widget.
            """
            selected_row_data = self.roi_table_model.row_data(self.selected_row)
            if self.current_roi in ["", " "]:
                self.current_roi = selected_row_data[0]
            if selected_row_data[0].lower() not in ["", " ", "all"] and selected_row_data[0] != self.current_roi:
                if selected_row_data[0] in self.presenter.get_roi_names():
                    selected_row_data[0] = self.current_roi
                    return
                else:
                    self.presenter.rename_roi(self.current_roi, selected_row_data[0])
                    self.current_roi = selected_row_data[0]
                    return
            else:
                selected_row_data[0] = self.current_roi

            selected_row_data[0] = self.current_roi
            on_visibility_change()
            return

        self.roi_table_model.dataChanged.connect(on_data_in_table_change)
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def show(self):
        super().show()
        self.activateWindow()

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.normaliseStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    @property
    def roi_table_model(self) -> TableModel:
        if self.tableView.model() is None:
            mdl = TableModel()
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

    def set_spectrum(self, name: str, spectrum_data: 'np.ndarray'):
        """
        Try to set the spectrum data for a given ROI assuming the
        roi may not exist in the spectrum widget yet depending on when method is called
        """
        self.spectrum.spectrum_data_dict[name] = spectrum_data
        self.spectrum.spectrum.clearPlots()

        for key, value in self.spectrum.spectrum_data_dict.items():
            if key in self.spectrum.roi_dict:
                self.spectrum.spectrum.plot(value, name=key, pen=self.spectrum.roi_dict[key].colour)

    def clear(self) -> None:
        self.spectrum.spectrum_data_dict = {}
        self.spectrum.image.setImage(np.zeros((1, 1)))
        self.spectrum.spectrum.clearPlots()

    def auto_range_image(self):
        self.spectrum.image.vb.autoRange()

    def set_normalise_error(self, norm_issue: str):
        self.normalise_error_issue = norm_issue

        self.display_normalise_error()

    def display_normalise_error(self):
        if self.normalise_error_issue and self.normalisation_enabled():
            self.normaliseErrorIcon.setPixmap(self.normalise_error_icon_pixmap)
            self.normaliseErrorIcon.setToolTip(self.normalise_error_issue)
        else:
            self.normaliseErrorIcon.setPixmap(QPixmap())
            self.normaliseErrorIcon.setToolTip("")

    def normalisation_enabled(self):
        return self.normaliseCheckBox.isChecked()

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
        self.addBtn.setEnabled(enabled)

    def set_roi_alpha(self, alpha: float, roi) -> None:
        """
        Set the alpha value for the selected ROI and update the spectrum to reflect the change.
        A check is made on the spectrum to see if it exists as it may not have been created yet.

        @param alpha: The alpha value
        """
        self.presenter.do_set_roi_alpha(self.roi_table_model.row_data(roi)[0], alpha)
        if alpha == 0:
            self.spectrum.spectrum_data_dict[self.roi_table_model.row_data(roi)[0]] = np.zeros(
                self.spectrum.spectrum_data_dict[self.roi_table_model.row_data(roi)[0]].shape)
        else:
            self.spectrum.spectrum_data_dict[self.roi_table_model.row_data(roi)[0]] = self.spectrum.spectrum_data_dict[
                self.roi_table_model.row_data(roi)[0]]

        self.spectrum.spectrum.clearPlots()
        self.spectrum.spectrum.update()
        for key, value in self.spectrum.spectrum_data_dict.items():
            if key in self.spectrum.roi_dict:
                self.spectrum.spectrum.plot(value, name=key, pen=self.spectrum.roi_dict[key].colour)

    def add_roi_table_row(self, name: str, colour: tuple[int, int, int]):
        """
        Add a new row to the ROI table

        @param name: The name of the ROI
        @param colour: The colour of the ROI
        """
        circle_label = QLabel()
        circle_label.setStyleSheet(f"background-color: {colour}; border-radius: 5px;")
        self.roi_table_model.appendNewRow(name, colour, True)
        self.tableView.selectRow(0)
        self.removeBtn.setEnabled(True)

    def remove_roi(self) -> None:
        """
        Clear the selected ROI in the table view
        """
        selected_row = self.roi_table_model.row_data(self.selected_row)
        if selected_row:
            self.roi_table_model.remove_row(self.selected_row)
            self.presenter.do_remove_roi(selected_row[0])
            self.spectrum.spectrum_data_dict.pop(selected_row[0])
            self.spectrum.spectrum.removeItem(selected_row[0])
            self.presenter.handle_roi_moved()
            self.selected_row = 0
            self.tableView.selectRow(0)

        if self.roi_table_model.rowCount() == 0:
            self.removeBtn.setEnabled(False)

    def clear_all_rois(self) -> None:
        """
        Clear all ROIs from the table view
        """
        self.roi_table_model.clear_table()
        self.spectrum.spectrum_data_dict = {}
        self.spectrum.spectrum.clearPlots()
        self.removeBtn.setEnabled(False)
