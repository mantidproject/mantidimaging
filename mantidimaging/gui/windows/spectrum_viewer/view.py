# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog, QPushButton, QLabel, QAbstractItemView, QHeaderView, \
    QTabWidget, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QGroupBox, QActionGroup, QAction, QWidget
from PyQt5.QtCore import QSignalBlocker, Qt, QModelIndex

from mantidimaging.core.utility import finder
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .model import ROI_RITS, allowed_modes, SensibleROI
from .presenter import SpectrumViewerWindowPresenter, ExportMode
from mantidimaging.gui.widgets import RemovableRowTableView
from .spectrum_widget import SpectrumWidget
from mantidimaging.gui.windows.spectrum_viewer.roi_table_model import TableModel
from mantidimaging.gui.widgets.spectrum_widgets.tof_properties import ExperimentSetupFormWidget
import numpy as np

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID


class ROIPropertiesTableWidget(QWidget):
    """
    A class to represent the ROI properties table widget in the spectrum viewer window.
    This class helps improve modularity of the spectrum viewer UI components by moving
    the ROI properties table widget to its own class.
    """

    roiPropertiesTableWidget: QTableWidget
    roiPropertiesGroupBox: QGroupBox
    roiPropertiesSpinBoxes: dict[str, QSpinBox]
    roiPropertiesLabels: dict[str, QLabel]

    def __init__(self, parent=None, roiPropertiesTableWidget=QTableWidget, roiPropertiesGroupBox=QGroupBox):
        super().__init__(parent)
        self.roi_table_properties = ["Top", "Bottom", "Left", "Right"]
        self.roi_table_properties_secondary = ["Width", "Height"]

        self.roiPropertiesTableWidget = roiPropertiesTableWidget
        self.roiPropertiesGroupBox = roiPropertiesGroupBox
        self.roiPropertiesSpinBoxes = {}
        self.roiPropertiesLabels = {}
        self.initialize_roi_properties()
        self.initialize_roi_properties_labels()

        self.initialise_roi_properties_table()

    def initialize_roi_properties(self) -> None:
        self.roiPropertiesSpinBoxes["Left"] = QSpinBox()
        self.roiPropertiesSpinBoxes["Right"] = QSpinBox()
        self.roiPropertiesSpinBoxes["Top"] = QSpinBox()
        self.roiPropertiesSpinBoxes["Bottom"] = QSpinBox()

    def initialize_roi_properties_labels(self) -> None:
        self.roiPropertiesLabels["Width"] = QLabel()
        self.roiPropertiesLabels["Height"] = QLabel()

    def set_roi_spinbox_ranges(self) -> None:
        self.roiPropertiesSpinBoxes["Left"].setMaximum(self.roiPropertiesSpinBoxes["Right"].value() - 1)
        self.roiPropertiesSpinBoxes["Right"].setMinimum(self.roiPropertiesSpinBoxes["Left"].value() + 1)
        self.roiPropertiesSpinBoxes["Top"].setMaximum(self.roiPropertiesSpinBoxes["Bottom"].value() - 1)
        self.roiPropertiesSpinBoxes["Bottom"].setMinimum(self.roiPropertiesSpinBoxes["Top"].value() + 1)

    def initialise_roi_properties_table(self) -> None:
        self.roiPropertiesTableWidget.setColumnCount(3)
        self.roiPropertiesTableWidget.setRowCount(3)
        self.roiPropertiesTableWidget.setColumnWidth(0, 80)
        self.roiPropertiesTableWidget.setColumnWidth(1, 50)
        self.roiPropertiesTableWidget.setColumnWidth(2, 50)

        self.roiPropertiesTableWidget.horizontalHeader().hide()
        self.roiPropertiesTableWidget.verticalHeader().hide()
        self.roiPropertiesTableWidget.setShowGrid(False)

    def populate_roi_properties_table_text(self) -> None:
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

    def setup_roi_properties_spinboxes(self, spectrum_widget: SpectrumWidget, do_adjust_roi: Callable) -> None:
        assert spectrum_widget.image.image_data is not None
        for prop in self.roi_table_properties:
            spin_box = QSpinBox()
            if prop == "Top" or prop == "Bottom":
                spin_box.setMaximum(spectrum_widget.image.image_data.shape[0])
            if prop == "Left" or prop == "Right":
                spin_box.setMaximum(spectrum_widget.image.image_data.shape[1])
            spin_box.valueChanged.connect(do_adjust_roi)  # THis will need moving out of presenter in
            self.roiPropertiesSpinBoxes[prop] = spin_box
        for prop in self.roi_table_properties_secondary:
            label = QLabel()
            self.roiPropertiesLabels[prop] = label

    def disable_roi_properties(self) -> None:
        self.roiPropertiesGroupBox.setTitle("Roi Properties: None selected")
        for _, spinbox in self.roiPropertiesSpinBoxes.items():
            with QSignalBlocker(spinbox):
                spinbox.setMinimum(0)
                spinbox.setValue(0)
                spinbox.setDisabled(True)
        for _, label in self.roiPropertiesLabels.items():
            label.setText("0")

    def refresh_roi_spinboxes(self, roi: SensibleROI, roi_name: str) -> None:
        """ Refresh the spinboxes for the ROI properties """
        self.roiPropertiesGroupBox.setTitle(f"Roi Properties: {roi_name}")
        roi_iter_order = ["Left", "Top", "Right", "Bottom"]
        for row, pos in enumerate(roi):
            with QSignalBlocker(self.roiPropertiesSpinBoxes[roi_iter_order[row]]):
                self.roiPropertiesSpinBoxes[roi_iter_order[row]].setValue(pos)
        self.set_roi_spinbox_ranges()

    def update_roi_dimensions(self, width: int, height: int) -> None:
        """ Update the width and height of the ROI """
        self.roiPropertiesLabels["Width"].setText(str(width))
        self.roiPropertiesLabels["Height"].setText(str(height))

    def set_roi_spinboxes_enabled(self, enabled: bool = True) -> None:
        """ Enable or disable the spinboxes for the ROI properties """
        for spinbox in self.roiPropertiesSpinBoxes.values():
            spinbox.setEnabled(enabled)


class ROITableWidget(RemovableRowTableView):
    """
    A class to represent the ROI table widget in the spectrum viewer window.
    """
    ElementType = str | tuple[int, int, int] | bool
    RowType = list[ElementType]
    old_table_names: list[str]
    selected_row: int
    last_clicked_roi: str
    current_roi_name: str

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is not None:
            layout = parent.layout()
            if layout is not None:
                layout.addWidget(self)

        self.old_table_names = []
        self.selected_row = 0
        self.last_clicked_roi = ""
        self.current_roi_name = ""

        # Point table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)

        # Initialise model
        mdl = TableModel()
        self.setModel(mdl)
        self._roi_table_model = mdl

        # Configure up the table view
        self.setVisible(True)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        if self._roi_table_model.rowCount() > 0:
            self.current_roi_name = self.last_clicked_roi = self._roi_table_model.roi_names()[0]

    @property
    def roi_table_model(self) -> TableModel:
        """The model for the ROI table"""
        return self._roi_table_model

    def get_roi_names(self) -> list[str]:
        return self._roi_table_model.roi_names()

    def get_row_data(self, row: int) -> RowType:
        """
        Get the data for a specific row in the ROI table.
        """
        name, data, visible = self._roi_table_model.row_data(row)
        return [name, data, visible]

    def get_roi_name_by_row(self, row: int) -> str:
        """
        Retrieve the name an ROI by its row index.
        """
        return self._roi_table_model.get_element(row, 0)

    def get_roi_visibility_by_row(self, row: int) -> bool:
        """
        Retrieve the visibility status of an ROI by its row index.
        """
        return self._roi_table_model.get_element(row, 2)

    def row_count(self) -> int:
        """
        Returns the number of rows in the ROI table model.
        """
        return self._roi_table_model.rowCount()

    def find_row_for_roi(self, roi_name: str) -> int | None:
        """
        Returns row index for ROI name, or None if not found.
        """
        for row in range(self._roi_table_model.rowCount()):
            if self._roi_table_model.index(row, 0).data() == roi_name:
                return row
        return None

    def set_roi_name_by_row(self, row: int, name: str) -> None:
        """
        Set the name of the ROI for a given row in the ROI table.
        """
        self._roi_table_model.set_element(row, 0, name)

    def set_old_table_names(self, old_table_names) -> None:
        """
        Updates the list of old table names by removing specific entries if they exist.
        """
        self.old_table_names = old_table_names
        if 'all' in self.old_table_names:
            self.old_table_names.remove('all')
        if 'rits_roi' in self.old_table_names:
            self.old_table_names.remove('rits_roi')

    def update_roi_color(self, roi_name: str, new_color: tuple[int, int, int]) -> None:
        """
        Finds ROI by name in table and updates it's colour (R, G, B) format.
        """
        row = self.find_row_for_roi(roi_name)
        if row is not None:
            self._roi_table_model.update_color(row, new_color)

    def add_row(self, name: str, colour: tuple[int, int, int], roi_names: list[str]) -> None:
        """
        Add a new row to the ROI table
        """
        self._roi_table_model.appendNewRow(name, colour, True)
        self.selected_row = self._roi_table_model.rowCount() - 1
        self.selectRow(self.selected_row)
        self.current_roi_name = name
        self.set_old_table_names(roi_names)

    def remove_row(self, row: int) -> None:
        """
        Remove a row from the ROI table
        """
        self._roi_table_model.remove_row(row)
        self.selectRow(0)

    def clear_table(self) -> None:
        """
        Clears the ROI table in the spectrum viewer.
        """
        self._roi_table_model.clear_table()


class ROIFormWidget(QGroupBox):
    """
    A class to represent the export tabs and ROI action buttons in the spectrum viewer window.
    """

    table_view: ROITableWidget
    roi_properties_widget: ROIPropertiesTableWidget

    def __init__(self,
                 table_view: RemovableRowTableView,
                 roiPropertiesTableWidget: QTableWidget,
                 roiPropertiesGroupBox: QGroupBox,
                 exportTabs=None,
                 add_btn: QPushButton = None,
                 remove_btn: QPushButton = None,
                 export_btn: QPushButton = None,
                 export_button_rits: QPushButton = None,
                 parent=None):
        super().__init__(parent)
        if parent is not None:
            layout = parent.layout()
            if layout is not None:
                layout.addWidget(self)
        self.table_view = ROITableWidget(table_view)
        self.roi_properties_widget = ROIPropertiesTableWidget(parent, roiPropertiesTableWidget, roiPropertiesGroupBox)
        self.exportTabs = exportTabs
        self.add_btn = add_btn
        self.remove_btn = remove_btn
        self.export_btn = export_btn
        self.export_button_rits = export_button_rits


class SpectrumViewerWindowView(BaseMainWindowView):
    roiTableView: RemovableRowTableView
    sampleStackSelector: DatasetSelectorWidgetView
    normaliseStackSelector: DatasetSelectorWidgetView

    normaliseCheckBox: QCheckBox
    normalise_ShutterCount_CheckBox: QCheckBox
    imageLayout: QVBoxLayout
    fittingLayout: QVBoxLayout
    exportLayout: QVBoxLayout
    exportButton: QPushButton
    exportTabs: QTabWidget
    normaliseErrorIcon: QLabel
    shuttercountErrorIcon: QLabel
    _current_dataset_id: UUID | None
    normalise_error_issue: str = ""
    shuttercount_error_issue: str = ""
    image_output_mode_combobox: QComboBox
    transmission_error_mode_combobox: QComboBox
    bin_size_spinBox: QSpinBox
    bin_step_spinBox: QSpinBox

    roiPropertiesTableWidget: QTableWidget
    roiPropertiesGroupBox: QGroupBox
    roi_properties_widget: ROIPropertiesTableWidget

    spectrum_widget: SpectrumWidget

    number_roi_properties_procced: int = 0

    experimentSetupGroupBox: QGroupBox
    experimentSetupFormWidget: ExperimentSetupFormWidget

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window

        icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
        self.normalise_error_icon_pixmap = QPixmap(icon_path)

        self.roi_form_widget = ROIFormWidget(table_view=self.roiTableView,
                                             roiPropertiesTableWidget=self.roiPropertiesTableWidget,
                                             roiPropertiesGroupBox=self.roiPropertiesGroupBox,
                                             exportTabs=self.exportTabs,
                                             add_btn=self.addBtn,
                                             remove_btn=self.removeBtn,
                                             export_btn=self.exportButton,
                                             export_button_rits=self.exportButtonRITS,
                                             parent=self)

        self.table_view = self.roi_form_widget.table_view
        self.roi_properties_widget = self.roi_form_widget.roi_properties_widget

        self.presenter = SpectrumViewerWindowPresenter(self, main_window)

        self.spectrum_widget = SpectrumWidget(main_window)
        self.spectrum = self.spectrum_widget.spectrum_plot_widget

        self.imageLayout.addWidget(self.spectrum_widget)
        self.fittingLayout.addWidget(QLabel("fitting"))
        self.exportLayout.addWidget(QLabel("export"))

        self.spectrum.range_changed.connect(self.presenter.handle_range_slide_moved)

        self.spectrum_widget.roi_clicked.connect(self.presenter.handle_roi_clicked)
        self.spectrum_widget.roi_changed.connect(self.presenter.handle_roi_moved)
        self.spectrum_widget.roiColorChangeRequested.connect(self.presenter.change_roi_colour)

        self.spectrum_right_click_menu = self.spectrum.spectrum_viewbox.menu
        self.units_menu = self.spectrum_right_click_menu.addMenu("Units")
        self.tof_mode_select_group = QActionGroup(self)

        for mode in allowed_modes.keys():
            action = QAction(mode, self.tof_mode_select_group)
            action.setCheckable(True)
            action.setObjectName(mode)
            self.units_menu.addAction(action)
            action.triggered.connect(self.presenter.handle_tof_unit_change_via_menu)
            if mode == "Image Index":
                action.setChecked(True)
        if self.presenter.model.tof_data is None:
            self.tof_mode_select_group.setEnabled(False)

        self._current_dataset_id = None
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_button_enabled)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_normalise_stack_change)
        self.normaliseStackSelector.stack_selected_uuid.connect(self.presenter.handle_button_enabled)
        self.normaliseCheckBox.stateChanged.connect(self.normaliseStackSelector.setEnabled)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_enable_normalised)
        self.normaliseCheckBox.stateChanged.connect(self.presenter.handle_button_enabled)
        self.normalise_ShutterCount_CheckBox.stateChanged.connect(self.presenter.set_shuttercount_error)
        self.normalise_ShutterCount_CheckBox.stateChanged.connect(self.presenter.handle_button_enabled)

        self.roi_form_widget.exportTabs.currentChanged.connect(self.presenter.handle_export_tab_change)
        self.roi_form_widget.add_btn.clicked.connect(self.set_new_roi)
        self.roi_form_widget.remove_btn.clicked.connect(self.remove_roi)
        self.roi_form_widget.export_btn.clicked.connect(self.presenter.handle_export_csv)
        self.roi_form_widget.export_button_rits.clicked.connect(self.presenter.handle_rits_export)

        self.set_binning_visibility()

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.normaliseStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.try_to_select_relevant_normalise_stack("Flat")
        self.presenter.handle_tof_unit_change()

        self.table_view.clicked.connect(self.handle_table_click)

        self.roi_properties_widget.setup_roi_properties_spinboxes(self.spectrum_widget, self.presenter.do_adjust_roi)
        self.roi_properties_widget.populate_roi_properties_table_text()

        self.spectrum_widget.roi_changed.connect(self.set_roi_properties)

        self.set_roi_properties()

        self.experimentSetupFormWidget = ExperimentSetupFormWidget(self.experimentSetupGroupBox)
        self.experimentSetupFormWidget.flight_path = 56.4
        self.experimentSetupFormWidget.connect_value_changed(self.presenter.handle_experiment_setup_properties_change)

        def on_row_change(item: QModelIndex, _: Any) -> None:
            """
            Handle cell change in table view and update selected ROI and
            toggle visibility of action buttons

            @param item: item in table
            """

            self.table_view.selected_row = item.row()
            self.table_view.current_roi_name = self.table_view.get_roi_name_by_row(item.row())
            self.set_roi_properties()

        self.table_view.selectionModel().currentRowChanged.connect(on_row_change)

        def on_data_in_table_change() -> None:
            """
            Check if an ROI name has changed in the table or if the visibility of an ROI has changed.
            If the ROI name has changed, update the ROI name in the spectrum widget.
            If the visibility of an ROI has changed, update the visibility of the ROI in the spectrum widget.
            """
            entered_name = self.table_view.get_roi_name_by_row(self.table_view.selected_row).strip()
            if not entered_name:
                self.table_view.set_roi_name_by_row(self.table_view.selected_row, self.table_view.current_roi_name)
                self.table_view.last_clicked_roi = self.table_view.current_roi_name
                self.table_view.set_old_table_names(self.presenter.get_roi_names())
                return
            if entered_name.lower() not in ["", " ", "all"] and entered_name != self.table_view.current_roi_name:
                if entered_name in self.presenter.get_roi_names():
                    entered_name = self.table_view.old_table_names[self.table_view.selected_row]
                    self.table_view.roi_table_model.set_element(
                        self.table_view.selected_row, 0, self.table_view.old_table_names[self.table_view.selected_row])
                    self.table_view.current_roi_name = entered_name
                    self.table_view.last_clicked_roi = self.table_view.current_roi_name
                else:
                    self.presenter.rename_roi(self.table_view.current_roi_name, entered_name)
                    self.table_view.current_roi_name = entered_name
                    self.table_view.last_clicked_roi = self.table_view.current_roi_name
                    self.set_roi_properties()
            else:
                self.table_view.roi_table_model.set_element(
                    self.table_view.selected_row, 0, self.table_view.old_table_names[self.table_view.selected_row])

            self.table_view.set_old_table_names(self.presenter.get_roi_names())
            self.on_visibility_change()
            return

        self.table_view.roi_table_model.dataChanged.connect(on_data_in_table_change)
        self.formTabs.currentChanged.connect(self.handle_change_tab)

    def show(self) -> None:
        super().show()
        self.activateWindow()

    def cleanup(self) -> None:
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.normaliseStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    def handle_change_tab(self, tab_index: int):
        self.imageTabs.setCurrentIndex(tab_index)

    def on_visibility_change(self) -> None:
        """
        When the visibility of an ROI is changed, update the visibility of the ROI in the spectrum widget
        """

        self.presenter.handle_storing_current_roi_name_on_tab_change()

        if self.presenter.export_mode == ExportMode.ROI_MODE:
            self.set_roi_visibility_flags(ROI_RITS, visible=False)

            if self.table_view.row_count() == 0:
                self.disable_roi_properties()
            else:
                self.set_roi_properties()

            for row in range(self.table_view.row_count()):
                roi_name = self.table_view.get_roi_name_by_row(row)
                roi_visible = self.table_view.get_roi_visibility_by_row(row)
                self.set_roi_visibility_flags(roi_name, visible=roi_visible)
                if roi_visible:
                    self.presenter.redraw_spectrum(roi_name)

        elif self.presenter.export_mode == ExportMode.IMAGE_MODE:
            for row in range(self.table_view.row_count()):
                roi_name = self.table_view.get_roi_name_by_row(row)
                self.set_roi_visibility_flags(roi_name, visible=False)

            self.set_roi_visibility_flags(ROI_RITS, visible=True)
            self.presenter.redraw_spectrum(ROI_RITS)
            self.table_view.current_roi_name = ROI_RITS

            for _, spinbox in self.roi_properties_widget.roiPropertiesSpinBoxes.items():
                spinbox.setEnabled(False)
            self.set_roi_properties()

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

    def set_image(self, image_data: np.ndarray, autoLevels: bool = True) -> None:
        self.spectrum_widget.image.setImage(image_data, autoLevels=autoLevels)

    def set_spectrum(self, name: str, spectrum_data: np.ndarray) -> None:
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

    def auto_range_image(self) -> None:
        self.spectrum_widget.image.vb.autoRange()

    def set_normalise_error(self, norm_issue: str) -> None:
        self.normalise_error_issue = norm_issue
        self.display_normalise_error()

    def display_normalise_error(self) -> None:
        if self.normalise_error_issue and self.normalisation_enabled():
            self.normaliseErrorIcon.setPixmap(self.normalise_error_icon_pixmap)
            self.normaliseErrorIcon.setToolTip(self.normalise_error_issue)
        else:
            self.normaliseErrorIcon.setPixmap(QPixmap())
            self.normaliseErrorIcon.setToolTip("")

    def normalisation_enabled(self) -> bool:
        return self.normaliseCheckBox.isChecked()

    def set_shuttercount_error(self, shuttercount_issue: str) -> None:
        self.shuttercount_error_issue = shuttercount_issue
        self.display_shuttercount_error()

    def handle_shuttercount_change(self) -> None:
        self.presenter.set_shuttercount_error(self.normalise_ShutterCount_CheckBox.isChecked())
        self.normalise_ShutterCount_CheckBox.setEnabled(self.shuttercount_error_issue == "")

    def display_shuttercount_error(self) -> None:
        if (self.shuttercount_error_issue and self.normalisation_enabled() and self.shuttercount_norm_enabled()
                and self.normalise_error_issue == ""):
            self.shuttercountErrorIcon.setPixmap(self.normalise_error_icon_pixmap)
            self.shuttercountErrorIcon.setToolTip(self.shuttercount_error_issue)
        else:
            self.shuttercountErrorIcon.setPixmap(QPixmap())
            self.shuttercountErrorIcon.setToolTip("")

    def shuttercount_norm_enabled(self) -> bool:
        return self.normalise_ShutterCount_CheckBox.isChecked()

    def set_new_roi(self) -> None:
        """
        Set a new ROI on the image
        """
        self.presenter.do_add_roi()
        self.roi_properties_widget.set_roi_spinboxes_enabled(True)
        self.set_roi_properties()

    def handle_table_click(self, index: QModelIndex) -> None:
        if index.isValid() and index.column() == 1:
            roi_name = self.table_view.get_roi_name_by_row(index.row())
            self.set_spectum_roi_color(roi_name)

    def set_spectum_roi_color(self, roi_name: str) -> None:
        spectrum_roi = self.spectrum_widget.roi_dict[roi_name]
        spectrum_roi.change_color_action.trigger()

    def set_roi_visibility_flags(self, roi_name: str, visible: bool) -> None:
        """
        Set the visibility for the selected ROI and update the spectrum to reflect the change.
        A check is made on the spectrum to see if it exists as it may not have been created yet.
        @param visible: Whether the ROI is visible.
        """
        self.spectrum_widget.set_roi_visibility_flags(roi_name, visible=visible)

        if not visible:
            self.spectrum_widget.spectrum_data_dict[roi_name] = None

        self.spectrum_widget.spectrum.clearPlots()
        self.spectrum_widget.spectrum.update()
        self.show_visible_spectrums()

    def show_visible_spectrums(self) -> None:
        for key, value in self.spectrum_widget.spectrum_data_dict.items():
            if value is not None and key in self.spectrum_widget.roi_dict:
                self.spectrum_widget.spectrum.plot(self.presenter.model.tof_data,
                                                   value,
                                                   name=key,
                                                   pen=self.spectrum_widget.roi_dict[key].colour)

    def add_roi_table_row(self, name: str, colour: tuple[int, int, int]) -> None:
        """
        Add a new row to the ROI table

        @param name: The name of the ROI
        @param colour: The colour of the ROI
        """
        self.table_view.add_row(name, colour, self.presenter.get_roi_names())
        self.removeBtn.setEnabled(True)

    def remove_roi(self) -> None:
        """
        Clear the selected ROI in the table view
        """
        roi_name, selected_row, _ = self.table_view.get_row_data(self.table_view.selected_row)
        assert isinstance(roi_name, str)
        if selected_row:
            self.table_view.remove_row(self.table_view.selected_row)
            self.presenter.do_remove_roi(roi_name)
            self.spectrum_widget.spectrum_data_dict.pop(roi_name)
            self.spectrum_widget.spectrum.removeItem(roi_name)
            self.presenter.handle_roi_moved()
            self.table_view.selected_row = 0

        if self.table_view.row_count() == 0:
            self.removeBtn.setEnabled(False)
            self.disable_roi_properties()
        else:
            self.table_view.set_old_table_names(self.presenter.get_roi_names())
            self.table_view.current_roi_name = self.table_view.get_roi_name_by_row(self.table_view.selected_row)
            self.set_roi_properties()

    def clear_all_rois(self) -> None:
        """
        Clear all ROIs from the table view
        """
        self.table_view.clear_table()
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

    @property
    def tof_units_mode(self) -> str:
        return self.tof_mode_select_group.checkedAction().text()

    def set_roi_properties(self) -> None:
        if self.presenter.export_mode == ExportMode.IMAGE_MODE:
            self.table_view.current_roi_name = ROI_RITS
        if (self.table_view.current_roi_name not in self.presenter.view.spectrum_widget.roi_dict
                or not self.roi_properties_widget.roiPropertiesSpinBoxes):
            return
        current_roi = self.presenter.view.spectrum_widget.get_roi(self.table_view.current_roi_name)
        self.roi_properties_widget.refresh_roi_spinboxes(current_roi, self.table_view.current_roi_name)
        self.presenter.redraw_spectrum(self.table_view.current_roi_name)
        self.roi_properties_widget.update_roi_dimensions(current_roi.width, current_roi.height)

        self.roi_properties_widget.set_roi_spinboxes_enabled(True)

    def disable_roi_properties(self) -> None:
        self.table_view.last_clicked_roi = "roi"
        self.roi_properties_widget.disable_roi_properties()

    def get_checked_menu_option(self) -> QAction:
        return self.tof_mode_select_group.checkedAction()
