# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog, QPushButton, QLabel, QAbstractItemView, QHeaderView, \
    QTabWidget, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QGroupBox
from PyQt5.QtCore import QSignalBlocker, Qt

from mantidimaging.core.utility import finder
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .model import ROI_RITS, ToFUnitMode
from .presenter import SpectrumViewerWindowPresenter, ExportMode
from mantidimaging.gui.widgets import RemovableRowTableView
from .spectrum_widget import SpectrumWidget
from mantidimaging.gui.windows.spectrum_viewer.roi_table_model import TableModel
from mantidimaging.core.utility.sensible_roi import SensibleROI

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
    exportTabs: QTabWidget
    normaliseErrorIcon: QLabel
    _current_dataset_id: UUID | None
    normalise_error_issue: str = ""
    image_output_mode_combobox: QComboBox
    transmission_error_mode_combobox: QComboBox
    bin_size_spinBox: QSpinBox
    bin_step_spinBox: QSpinBox

    roiPropertiesTableWidget: QTableWidget
    roiPropertiesGroupBox: QGroupBox

    last_clicked_roi: str

    spectrum_widget: SpectrumWidget

    number_roi_properties_procced: int = 0

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window

        icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
        self.normalise_error_icon_pixmap = QPixmap(icon_path)

        self.selected_row: int = 0
        self.current_roi: str = ""
        self.selected_row_data: list | None = None
        self.roiPropertiesSpinBoxes: dict[str, QSpinBox] = {}
        self.roiPropertiesLabels: dict[str, QLabel] = {}
        self.old_table_names: list = []

        self.presenter = SpectrumViewerWindowPresenter(self, main_window)

        self.spectrum_widget = SpectrumWidget()
        self.spectrum = self.spectrum_widget.spectrum_plot_widget

        self.imageLayout.addWidget(self.spectrum_widget)

        self.spectrum.range_changed.connect(self.presenter.handle_range_slide_moved)

        self.spectrum_widget.roi_clicked.connect(self.presenter.handle_roi_clicked)
        self.spectrum_widget.roi_changed.connect(self.presenter.handle_roi_moved)
        self.spectrum_widget.roiColorChangeRequested.connect(self.presenter.change_roi_colour)

        self._current_dataset_id = None
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_button_enabled)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_normalise_stack_change)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_button_enabled)
        self.normaliseCheckBox.stateChanged.connect(self.normaliseStackSelector.setEnabled)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_enable_normalised)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_button_enabled)

        self.exportTabs.currentChanged.connect(self.presenter.handle_export_tab_change)
        self.image_output_mode_combobox.currentTextChanged.connect(self.set_binning_visibility)
        self.set_binning_visibility()

        # ROI action buttons
        self.addBtn.clicked.connect(self.set_new_roi)
        self.removeBtn.clicked.connect(self.remove_roi)

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.normaliseStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.try_to_select_relevant_normalise_stack("Flat")
        self.presenter.handle_tof_unit_change()

        self.exportButton.clicked.connect(self.presenter.handle_export_csv)
        self.exportButtonRITS.clicked.connect(self.presenter.handle_rits_export)

        # Point table
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.clicked.connect(self.handle_table_click)

        # Roi Prop table
        self.roi_table_properties = ["Top", "Bottom", "Left", "Right"]
        self.roi_table_properties_secondary = ["Width", "Height"]
        self.roiPropertiesTableWidget.setColumnCount(3)
        self.roiPropertiesTableWidget.setRowCount(3)
        self.roiPropertiesTableWidget.setColumnWidth(0, 80)
        self.roiPropertiesTableWidget.setColumnWidth(1, 50)
        self.roiPropertiesTableWidget.setColumnWidth(2, 50)

        for prop in self.roi_table_properties:
            spin_box = QSpinBox()
            if prop == "Top" or prop == "Bottom":
                spin_box.setMaximum(self.spectrum_widget.image.image_data.shape[0])
            if prop == "Left" or prop == "Right":
                spin_box.setMaximum(self.spectrum_widget.image.image_data.shape[1])
            spin_box.valueChanged.connect(self.adjust_roi)
            self.roiPropertiesSpinBoxes[prop] = spin_box
        for prop in self.roi_table_properties_secondary:
            label = QLabel()
            self.roiPropertiesLabels[prop] = label

        self.roiPropertiesTableWidget.horizontalHeader().hide()
        self.roiPropertiesTableWidget.verticalHeader().hide()
        self.roiPropertiesTableWidget.setShowGrid(False)

        roiPropertiesTableText = ["x1, x2", "y1, y2", "Size"]
        self.roiPropertiesTableTextDict = {}
        for text in roiPropertiesTableText:
            item = QTableWidgetItem(text)
            item.setFlags(Qt.ItemIsSelectable)
            self.roiPropertiesTableTextDict[text] = item

        self.roiPropertiesTableWidget.setItem(0, 0, self.roiPropertiesTableTextDict["x1, x2"])
        self.roiPropertiesTableWidget.setCellWidget(0, 1, self.roiPropertiesSpinBoxes["Left"])
        self.roiPropertiesTableWidget.setCellWidget(0, 2, self.roiPropertiesSpinBoxes["Right"])
        self.roiPropertiesTableWidget.setItem(1, 0, self.roiPropertiesTableTextDict["y1, y2"])
        self.roiPropertiesTableWidget.setCellWidget(1, 1, self.roiPropertiesSpinBoxes["Top"])
        self.roiPropertiesTableWidget.setCellWidget(1, 2, self.roiPropertiesSpinBoxes["Bottom"])
        self.roiPropertiesTableWidget.setItem(2, 0, self.roiPropertiesTableTextDict["Size"])
        self.roiPropertiesTableWidget.setCellWidget(2, 1, self.roiPropertiesLabels["Width"])
        self.roiPropertiesTableWidget.setCellWidget(2, 2, self.roiPropertiesLabels["Height"])

        self.spectrum_widget.roi_changed.connect(self.set_roi_properties)

        _ = self.roi_table_model  # Initialise model
        self.current_roi = self.last_clicked_roi = self.roi_table_model.roi_names()[0]
        self.set_roi_properties()

        print(f"{self.presenter.model.get_stack_time_of_flight()=}")
        print(f"{self.presenter.model.get_stack_time_of_flight_wavelength()=}")
        print(f"{self.presenter.model.get_stack_time_of_flight_energy()=}")

        def on_row_change(item, _) -> None:
            """
            Handle cell change in table view and update selected ROI and
            toggle visibility of action buttons

            @param item: item in table
            """
            selected_row_data = self.roi_table_model.row_data(item.row())
            self.selected_row = item.row()
            self.current_roi = selected_row_data[0]
            self.set_roi_properties()

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)

        def on_data_in_table_change() -> None:
            """
            Check if an ROI name has changed in the table or if the visibility of an ROI has changed.
            If the ROI name has changed, update the ROI name in the spectrum widget.
            If the visibility of an ROI has changed, update the visibility of the ROI in the spectrum widget.
            """
            selected_row_data = self.roi_table_model.row_data(self.selected_row)
            if selected_row_data[0].lower() not in ["", " ", "all"] and selected_row_data[0] != self.current_roi:
                if selected_row_data[0] in self.presenter.get_roi_names():
                    selected_row_data[0] = self.old_table_names[self.selected_row]
                    self.current_roi = selected_row_data[0]
                    self.last_clicked_roi = self.current_roi
                else:
                    self.presenter.rename_roi(self.current_roi, selected_row_data[0])
                    self.current_roi = selected_row_data[0]
                    self.last_clicked_roi = self.current_roi
                    self.set_roi_properties()
            else:
                selected_row_data[0] = self.old_table_names[self.selected_row]

            self.set_old_table_names()
            self.on_visibility_change()
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

    def on_visibility_change(self) -> None:
        """
        When the visibility of an ROI is changed, update the visibility of the ROI in the spectrum widget
        """
        if self.presenter.export_mode == ExportMode.ROI_MODE:
            if self.current_roi in self.old_table_names and self.last_clicked_roi in self.old_table_names:
                pass
            elif self.current_roi == ROI_RITS and self.last_clicked_roi in self.old_table_names:
                self.current_roi = self.last_clicked_roi
            elif self.current_roi == ROI_RITS and self.last_clicked_roi not in self.old_table_names:
                self.current_roi = self.roi_table_model.row_data(self.selected_row)[0]
            else:
                self.last_clicked_roi = self.current_roi
            if self.roi_table_model.rowCount() == 0:
                self.disable_roi_properties()
            if not self.roi_table_model.rowCount() == 0:
                self.set_roi_properties()
            for roi_name, _, roi_visible in self.roi_table_model:
                if roi_visible is False:
                    self.set_roi_alpha(0, roi_name)
                else:
                    self.set_roi_alpha(255, roi_name)
                    self.presenter.redraw_spectrum(roi_name)
        else:
            for roi_name, _, _ in self.roi_table_model:
                self.set_roi_alpha(0, roi_name)

        if self.presenter.export_mode == ExportMode.IMAGE_MODE:
            self.set_roi_alpha(255, ROI_RITS)
            self.presenter.redraw_spectrum(ROI_RITS)
            if self.current_roi != ROI_RITS:
                self.last_clicked_roi = self.current_roi
            self.current_roi = ROI_RITS
            for _, spinbox in self.roiPropertiesSpinBoxes.items():
                spinbox.setEnabled(True)
            self.set_roi_properties()
        else:
            self.set_roi_alpha(0, ROI_RITS)

    @property
    def roi_table_model(self) -> TableModel:
        if self.tableView.model() is None:
            mdl = TableModel()
            self.tableView.setModel(mdl)
        return self.tableView.model()

    @property
    def current_dataset_id(self) -> UUID | None:
        return self._current_dataset_id

    @current_dataset_id.setter
    def current_dataset_id(self, uuid: UUID | None) -> None:
        self._current_dataset_id = uuid

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView) -> None:
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)

    def try_to_select_relevant_normalise_stack(self, name: str) -> None:
        self.normaliseStackSelector.try_to_select_relevant_stack(name)

    def get_normalise_stack(self) -> UUID | None:
        return self.normaliseStackSelector.current()

    def get_csv_filename(self) -> Path | None:
        path = QFileDialog.getSaveFileName(self, "Save CSV file", "", "CSV file (*.csv)")[0]
        if path:
            return Path(path)
        else:
            return None

    def get_rits_export_directory(self) -> Path | None:
        """
        Get the path to save the RITS file too
        """
        path = QFileDialog.getExistingDirectory(self, "Select Directory", "", QFileDialog.ShowDirsOnly)
        if path:
            return Path(path)
        else:
            return None

    def get_rits_export_filename(self) -> Path | None:
        """
        Get the path to save the RITS file too
        """
        path = QFileDialog.getSaveFileName(self, "Save DAT file", "", "DAT file (*.dat)")[0]
        if path:
            return Path(path)
        else:
            return None

    def set_image(self, image_data: np.ndarray, autoLevels: bool = True):
        self.spectrum_widget.image.setImage(image_data, autoLevels=autoLevels)

    def set_spectrum(self, name: str, spectrum_data: np.ndarray):
        """
        Try to set the spectrum data for a given ROI assuming the
        roi may not exist in the spectrum widget yet depending on when method is called
        """
        self.spectrum_widget.spectrum_data_dict[name] = spectrum_data
        self.spectrum_widget.spectrum.clearPlots()

        self.show_visible_spectrums()

    def clear(self) -> None:
        self.spectrum_widget.spectrum_data_dict = {}
        self.spectrum_widget.image.setImage(np.zeros((1, 1)))
        self.spectrum_widget.spectrum.clearPlots()

    def auto_range_image(self):
        self.spectrum_widget.image.vb.autoRange()

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
        for _, spinbox in self.roiPropertiesSpinBoxes.items():
            if not spinbox.isEnabled():
                spinbox.setEnabled(True)
        self.set_roi_properties()

    def handle_table_click(self, index):
        if index.isValid() and index.column() == 1:
            roi_name = self.roi_table_model.index(index.row(), 0).data()
            self.set_spectum_roi_color(roi_name)

    def set_spectum_roi_color(self, roi_name: str) -> None:
        spectrum_roi = self.spectrum_widget.roi_dict[roi_name]
        spectrum_roi.change_color_action.trigger()

    def update_roi_color(self, roi_name: str, new_color: tuple) -> None:
        """
        Finds ROI by name in table and updates colour.
        @param roi_name: Name of the ROI to update.
        @param new_color: The new color for the ROI in (R, G, B) format.
        """
        row = self.find_row_for_roi(roi_name)
        if row is not None:
            self.roi_table_model.update_color(row, new_color)

    def find_row_for_roi(self, roi_name: str) -> int | None:
        """
        Returns row index for ROI name, or None if not found.
        @param roi_name: Name ROI find.
        @return: Row index ROI or None.
        """
        for row in range(self.roi_table_model.rowCount()):
            if self.roi_table_model.index(row, 0).data() == roi_name:
                return row
        return None

    def set_roi_alpha(self, alpha: float, roi_name: str) -> None:
        """
        Set the alpha value for the selected ROI and update the spectrum to reflect the change.
        A check is made on the spectrum to see if it exists as it may not have been created yet.

        @param alpha: The alpha value
        """
        self.spectrum_widget.set_roi_alpha(roi_name, alpha)
        if alpha == 0:
            self.spectrum_widget.spectrum_data_dict[roi_name] = None

        self.spectrum_widget.spectrum.clearPlots()
        self.spectrum_widget.spectrum.update()
        self.show_visible_spectrums()

    def show_visible_spectrums(self):
        for key, value in self.spectrum_widget.spectrum_data_dict.items():
            if value is not None and key in self.spectrum_widget.roi_dict:
                if self.presenter.model.tof_mode == ToFUnitMode.IMAGE_NUMBER:
                    self.spectrum_widget.spectrum.plot(value, name=key, pen=self.spectrum_widget.roi_dict[key].colour)
                else:
                    self.spectrum_widget.spectrum.plot(self.presenter.model.tof_data, value, name=key, pen=self.spectrum_widget.roi_dict[key].colour)




    def add_roi_table_row(self, name: str, colour: tuple[int, int, int]):
        """
        Add a new row to the ROI table

        @param name: The name of the ROI
        @param colour: The colour of the ROI
        """
        self.roi_table_model.appendNewRow(name, colour, True)
        self.selected_row = self.roi_table_model.rowCount() - 1
        self.tableView.selectRow(self.selected_row)
        self.current_roi = name
        self.removeBtn.setEnabled(True)
        self.set_old_table_names()

    def remove_roi(self) -> None:
        """
        Clear the selected ROI in the table view
        """
        selected_row = self.roi_table_model.row_data(self.selected_row)
        if selected_row:
            self.roi_table_model.remove_row(self.selected_row)
            self.presenter.do_remove_roi(selected_row[0])
            self.spectrum_widget.spectrum_data_dict.pop(selected_row[0])
            self.spectrum_widget.spectrum.removeItem(selected_row[0])
            self.presenter.handle_roi_moved()
            self.selected_row = 0
            self.tableView.selectRow(0)

        if self.roi_table_model.rowCount() == 0:
            self.removeBtn.setEnabled(False)
            self.disable_roi_properties()
        else:
            self.set_old_table_names()
            self.current_roi = self.roi_table_model.row_data(self.selected_row)[0]
            self.set_roi_properties()

    def clear_all_rois(self) -> None:
        """
        Clear all ROIs from the table view
        """
        self.roi_table_model.clear_table()
        self.spectrum_widget.spectrum_data_dict = {}
        self.spectrum_widget.spectrum.clearPlots()
        self.removeBtn.setEnabled(False)
        self.disable_roi_properties()

    @property
    def transmission_error_mode(self) -> str:
        return self.transmission_error_mode_combobox.currentText()

    @property
    def image_output_mode(self) -> str:
        return self.image_output_mode_combobox.currentText()

    @property
    def bin_size(self) -> int:
        return self.bin_size_spinBox.value()

    @property
    def bin_step(self) -> int:
        return self.bin_step_spinBox.value()

    def set_binning_visibility(self) -> None:
        hide_binning = self.image_output_mode != "2D Binned"
        self.bin_size_label.setHidden(hide_binning)
        self.bin_size_spinBox.setHidden(hide_binning)
        self.bin_step_label.setHidden(hide_binning)
        self.bin_step_spinBox.setHidden(hide_binning)

    def set_roi_properties(self) -> None:
        if self.presenter.export_mode == ExportMode.IMAGE_MODE:
            self.current_roi = ROI_RITS
        if self.current_roi not in self.presenter.model.get_list_of_roi_names() or not self.roiPropertiesSpinBoxes:
            return
        else:
            current_roi = self.presenter.model.get_roi(self.current_roi)
        self.roiPropertiesGroupBox.setTitle(f"Roi Properties: {self.current_roi}")
        roi_iter_order = ["Left", "Top", "Right", "Bottom"]
        for row, pos in enumerate(current_roi):
            with QSignalBlocker(self.roiPropertiesSpinBoxes[roi_iter_order[row]]):
                self.roiPropertiesSpinBoxes[roi_iter_order[row]].setValue(pos)
        self.set_roi_spinbox_ranges()
        self.presenter.redraw_spectrum(self.current_roi)
        self.roiPropertiesLabels["Width"].setText(str(current_roi.width))
        self.roiPropertiesLabels["Height"].setText(str(current_roi.height))
        for spinbox in self.roiPropertiesSpinBoxes.values():
            spinbox.setEnabled(True)

    def adjust_roi(self) -> None:
        roi_iter_order = ["Left", "Top", "Right", "Bottom"]
        new_points = [self.roiPropertiesSpinBoxes[prop].value() for prop in roi_iter_order]
        new_roi = SensibleROI().from_list(new_points)
        self.presenter.model.set_roi(self.current_roi, new_roi)
        self.spectrum_widget.adjust_roi(new_roi, self.current_roi)

    def set_roi_spinbox_ranges(self):
        self.roiPropertiesSpinBoxes["Left"].setMaximum(self.roiPropertiesSpinBoxes["Right"].value() - 1)
        self.roiPropertiesSpinBoxes["Right"].setMinimum(self.roiPropertiesSpinBoxes["Left"].value() + 1)
        self.roiPropertiesSpinBoxes["Top"].setMaximum(self.roiPropertiesSpinBoxes["Bottom"].value() - 1)
        self.roiPropertiesSpinBoxes["Bottom"].setMinimum(self.roiPropertiesSpinBoxes["Top"].value() + 1)

    def disable_roi_properties(self):
        self.roiPropertiesGroupBox.setTitle("Roi Properties: None selected")
        self.last_clicked_roi = "roi"
        for _, spinbox in self.roiPropertiesSpinBoxes.items():
            with QSignalBlocker(spinbox):
                spinbox.setMinimum(0)
                spinbox.setValue(0)
                spinbox.setDisabled(True)
        for _, label in self.roiPropertiesLabels.items():
            label.setText("0")

    def get_roi_properties_spinboxes(self):
        return self.roiPropertiesSpinBoxes

    def set_old_table_names(self):
        self.old_table_names = self.presenter.get_roi_names()
        if 'all' in self.old_table_names:
            self.old_table_names.remove('all')
        if 'rits_roi' in self.old_table_names:
            self.old_table_names.remove('rits_roi')
