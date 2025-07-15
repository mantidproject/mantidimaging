# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING

import numpy
from PyQt5.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QInputDialog, QPushButton, QSpinBox,
                             QVBoxLayout, QWidget, QTextEdit, QLabel, QApplication, QStyle, QCheckBox)
from PyQt5.QtCore import QSignalBlocker

from mantidimaging.core.data import ImageStack
from mantidimaging.core.net.help_pages import SECTION_USER_GUIDE, open_help_webpage
from mantidimaging.core.utility.cuda_check import CudaChecker
from mantidimaging.core.utility.data_containers import Degrees, ReconstructionParameters, ScalarCoR, Slope
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import INPUT_DIALOG_FLAGS
from mantidimaging.gui.widgets import RemovableRowTableView
from mantidimaging.gui.widgets.palette_changer.view import PaletteChangerView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from mantidimaging.gui.windows.recon.image_view import ReconImagesView
from mantidimaging.gui.windows.recon.point_table_model import Column, CorTiltPointQtModel
from mantidimaging.gui.windows.recon.presenter import AutoCorMethod
from mantidimaging.gui.windows.recon.presenter import Notifications as PresN
from mantidimaging.gui.windows.recon.presenter import ReconstructWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID

LOG = getLogger(__name__)


class ReconstructWindowView(BaseMainWindowView):
    # COR and Tilt tab

    resultsTab: QWidget

    stackSelector: DatasetSelectorWidgetView

    resultCorSpinBox: QDoubleSpinBox
    resultTiltSpinBox: QDoubleSpinBox
    resultSlopeSpinBox: QDoubleSpinBox
    calculateCorsButton: QPushButton

    correlateButton: QPushButton
    minimiseButton: QPushButton
    corHelpButton: QPushButton

    tableView: RemovableRowTableView
    removeButton: QPushButton
    addButton: QPushButton
    clearAllButton: QPushButton
    refineCorButton: QPushButton

    # BHC tab

    bhcTab: QWidget

    lbhcEnabledCheckBox: QCheckBox
    lbhcA0SpinBox: QDoubleSpinBox
    lbhcA1SpinBox: QDoubleSpinBox
    lbhcA2SpinBox: QDoubleSpinBox
    lbhcA3SpinBox: QDoubleSpinBox

    # Reconstruct tab

    reconTab: QWidget

    maxProjAngleSpinBox: QDoubleSpinBox
    algorithmNameComboBox: QComboBox
    filterNameComboBox: QComboBox
    numIterSpinBox: QSpinBox
    alphaSpinBox: QDoubleSpinBox

    nonNegativeCheckBox: QCheckBox
    stochasticCheckBox: QCheckBox

    subsetsSpinBox: QSpinBox
    regPercentSpinBox: QSpinBox
    pixelSizeSpinBox: QDoubleSpinBox

    refineIterationsButton: QPushButton
    reconHelpButton: QPushButton

    reconstructSliceButton: QPushButton
    reconstructVolumeButton: QPushButton

    # ----------------
    # Preview section

    previewProjectionIndexSpinBox: QSpinBox
    previewSliceIndexSpinBox: QSpinBox

    changeColourPaletteButton: QPushButton
    changeColourPaletteDialog: PaletteChangerView | None = None

    messageIconLabel: QLabel
    statusMessageTextEdit: QTextEdit

    # ----------------
    # Image section

    imageLayout: QVBoxLayout

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/recon_window.ui')

        self.main_window = main_window
        self.presenter = ReconstructWindowPresenter(self, main_window)

        self.algorithmNameComboBox.insertItem(1, "FBP_CUDA")
        self.algorithmNameComboBox.insertItem(2, "SIRT_CUDA")
        self.algorithmNameComboBox.insertItem(3, "CIL_PDHG-TV")
        self.algorithmNameComboBox.setCurrentIndex(1)
        if not CudaChecker().cuda_is_present():
            self.algorithmNameComboBox.model().item(1).setEnabled(False)
            self.algorithmNameComboBox.model().item(2).setEnabled(False)
            self.algorithmNameComboBox.model().item(3).setEnabled(False)
            self.algorithmNameComboBox.setCurrentIndex(0)
        self.algorithmNameComboBox.setEnabled(True)

        self.update_recon_hist_needed = False

        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_current_stack)

        # Handle preview image selection
        self.previewProjectionIndexSpinBox.valueChanged[int].connect(self.presenter.set_preview_projection_idx)
        self.previewSliceIndexSpinBox.valueChanged[int].connect(self.presenter.set_preview_slice_idx)

        self.image_view = ReconImagesView(self)
        self.imageLayout.addWidget(self.image_view)
        self.image_view.sigSliceIndexChanged.connect(self.presenter.set_preview_slice_idx)

        # Point table
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.cor_table_model.rowsInserted.connect(self.on_table_row_count_change)  # type: ignore
        self.cor_table_model.rowsRemoved.connect(self.on_table_row_count_change)  # type: ignore
        self.cor_table_model.modelReset.connect(self.on_table_row_count_change)  # type: ignore

        # Update previews when data in table changes
        def on_data_change(tl, br, _):
            # Should we auto fit on data change?
            if self.tableView.model().num_points >= 2:
                self.presenter.notify(PresN.COR_FIT)
            self.presenter.notify(PresN.UPDATE_PROJECTION)
            if tl == br and tl.column() == Column.CENTRE_OF_ROTATION.value:
                mdl = self.tableView.model()
                slice_idx = mdl.data(mdl.index(tl.row(), Column.SLICE_INDEX.value))
                self.presenter.notify(PresN.RECONSTRUCT_USER_CLICK, slice_idx)

        self.cor_table_model.dataChanged.connect(on_data_change)

        self.clearAllButton.clicked.connect(lambda: self.presenter.notify(PresN.CLEAR_ALL_CORS))
        self.removeButton.clicked.connect(lambda: self.presenter.notify(PresN.REMOVE_SELECTED_COR))
        self.addButton.clicked.connect(lambda: self.presenter.notify(PresN.ADD_COR))
        self.refineCorButton.clicked.connect(lambda: self.presenter.notify(PresN.REFINE_COR))
        self.refineIterationsButton.clicked.connect(lambda: self.presenter.notify(PresN.REFINE_ITERS))
        self.calculateCorsButton.clicked.connect(lambda: self.presenter.notify(PresN.CALCULATE_CORS_FROM_MANUAL_TILT))
        self.reconstructVolumeButton.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_VOLUME))
        self.reconstructSliceButton.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_STACK_SLICE))

        self.correlateButton.clicked.connect(lambda: self.presenter.notify(PresN.AUTO_FIND_COR_CORRELATE))
        self.minimiseButton.clicked.connect(lambda: self.presenter.notify(PresN.AUTO_FIND_COR_MINIMISE))

        self.changeColourPaletteButton.clicked.connect(self.on_change_colour_palette)

        def on_row_change(item, _):
            """
            Handles setting preview slice index from the currently selected row
            in the manual COR table.
            """
            if item.isValid():
                row_data = item.model().point(item.row())
                slice_idx = row_data.slice_index
                cor = row_data.cor
                self.presenter.set_row(item.row())
                self.presenter.set_last_cor(cor)
                self.presenter.set_preview_slice_idx(slice_idx)
                self.image_view.slice_line.setPos(slice_idx)
                self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE)

            # Only allow buttons which act on selected row to be clicked when a valid
            # row is selected
            for button in [self.refineCorButton, self.removeButton]:
                button.setEnabled(item.isValid())

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)  # type: ignore

        # Update initial UI state
        self.on_table_row_count_change()

        self.stackSelector.subscribe_to_main_window(main_window)
        self.stackSelector.stack_selected_uuid.connect(lambda: self.presenter.notify(PresN.SET_CURRENT_STACK))
        self.stackSelector.select_eligible_stack()

        self.maxProjAngleSpinBox.valueChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore
        self.algorithmNameComboBox.currentTextChanged.connect(
            lambda: self.presenter.notify(PresN.ALGORITHM_CHANGED))  # type: ignore
        self.presenter.notify(PresN.ALGORITHM_CHANGED)
        self.filterNameComboBox.currentTextChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore
        self.numIterSpinBox.valueChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore

        self.pixelSizeSpinBox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.alphaSpinBox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.nonNegativeCheckBox.stateChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.stochasticCheckBox.stateChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.subsetsSpinBox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.regPercentSpinBox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.reconHelpButton.clicked.connect(lambda: self.open_help_webpage("explanations/reconstructions/index"))
        self.corHelpButton.clicked.connect(
            lambda: self.open_help_webpage("explanations/reconstructions/center_of_rotation"))

        self.stochasticCheckBox.stateChanged.connect(self.subsetsSpinBox.setEnabled)
        self.stochasticCheckBox.stateChanged.connect(self.subsetsLabel.setEnabled)
        self.stochasticCheckBox.stateChanged.connect(self.regPercentSpinBox.setEnabled)
        self.stochasticCheckBox.stateChanged.connect(self.regPercentLabel.setEnabled)

        self.previewAutoUpdate.stateChanged.connect(self.handle_auto_update_preview_selection)
        self.updatePreviewButton.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_USER_CLICK))

        for spinbox in [self.lbhcA0SpinBox, self.lbhcA1SpinBox, self.lbhcA2SpinBox, self.lbhcA3SpinBox]:
            spinbox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
            self.lbhcEnabledCheckBox.toggled.connect(spinbox.setEnabled)
        self.lbhcEnabledCheckBox.toggled.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))

    def showEvent(self, e) -> None:
        super().showEvent(e)
        self.presenter.handle_show_event()
        self.activateWindow()

    def closeEvent(self, e) -> None:
        if self.presenter.recon_is_running:
            e.ignore()
        else:
            self.hide()

    def remove_selected_cor(self) -> None:
        return self.tableView.removeSelectedRows()

    def clear_cor_table(self) -> None:
        LOG.info("Cleared all COR table entries")
        return self.cor_table_model.removeAllRows()

    def cleanup(self) -> None:
        self.stackSelector.unsubscribe_from_main_window()
        self.image_view.cleanup()
        self.main_window.recon = None

    @property
    def cor_table_model(self) -> CorTiltPointQtModel:
        if self.tableView.model() is None:
            mdl = CorTiltPointQtModel(self.tableView)
            self.tableView.setModel(mdl)
        return self.tableView.model()  # type: ignore

    def set_results(self, cor: ScalarCoR, tilt: Degrees, slope: Slope) -> None:
        """
        Sets the numerical COR and tilt angle results.
        """
        self.rotation_centre = cor.value
        self.tilt = tilt.value
        self.slope = slope.value
        self.image_view.show_cor_line(tilt, cor.value)

    def preview_image_on_button_press(self, event) -> None:
        """
        Handles mouse button presses on the preview projection image.

        Used to set the preview slice when a user clicks on a given part of the
        image.
        """
        if event.button == 1 and event.ydata is not None:
            self.presenter.set_preview_slice_idx(int(event.ydata))

    def update_projection(self, image_data, preview_slice_index: int) -> None:
        """
        Updates the preview projection image and associated annotations.

        Region of interest sets the bounds of the image axes, it does not
        resize the data itself. The advantage of this is that the coordinates
        do not change.

        :param image_data: Projection image data (single/2D image)
        :param preview_slice_index: Y coordinate at which to draw the preview
                                    slice indicator
        :param tilt_angle: Angle of the tilt line
        """

        with QSignalBlocker(self.previewSliceIndexSpinBox):
            self.previewSliceIndexSpinBox.setValue(preview_slice_index)

        self.image_view.update_projection(image_data, preview_slice_index)

    def update_sinogram(self, image_data) -> None:
        self.image_view.update_sinogram(image_data)

    def is_auto_update_preview(self) -> bool:
        return self.previewAutoUpdate.isChecked()

    def handle_auto_update_preview_selection(self) -> None:
        if self.previewAutoUpdate.isChecked():
            self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE)

    def update_recon_preview(self, image_data: numpy.ndarray, reset_roi: bool = False) -> None:
        """
        Updates the reconstruction preview image with new data.
        """
        # Plot image
        self.image_view.update_recon(image_data, reset_roi)
        if self.update_recon_hist_needed:
            self.image_view.update_recon_hist()
            self.update_recon_hist_needed = False

    def reset_recon_and_sino_previews(self) -> None:
        """
        Resets the recon and sinogram preview images, forcing a complete redraw next time they
        are updated.
        """
        self.image_view.clear_recon()
        self.image_view.clear_sinogram()

    def reset_recon_line_profile(self) -> None:
        self.image_view.clear_recon_line_profile()

    def reset_projection_preview(self) -> None:
        self.image_view.clear_projection()

    def reset_slice_and_tilt(self, slice_index: int) -> None:
        self.image_view.reset_slice_and_tilt(slice_index)

    def on_table_row_count_change(self, _=None, __=None) -> None:
        """
        Called when rows have been added or removed from the point table.

        Used to conditionally enable UI controls that depend on a certain
        amount of entries in the table.
        """
        # Disable clear buttons when there are no rows in the table
        empty = self.tableView.model().empty
        self.removeButton.setEnabled(not empty)
        self.clearAllButton.setEnabled(not empty)

    def add_cor_table_row(self, row: int, slice_index: int, cor: float) -> None:
        """
        Adds a row to the manual COR table with a specified slice index.
        """
        self.cor_table_model.appendNewRow(row, slice_index, cor)
        self.tableView.selectRow(row)
        LOG.debug("Added COR table row: row=%d, slice=%d, COR=%.3f", row, slice_index, cor)

    def get_cor_table_selected_rows(self) -> list[int]:
        rows = self.tableView.selectionModel().selectedRows()
        return [row.row() for row in rows]

    @property
    def rotation_centre(self) -> float:
        return self.resultCorSpinBox.value()

    @rotation_centre.setter
    def rotation_centre(self, value: float) -> None:
        self.resultCorSpinBox.setValue(value)

    @property
    def tilt(self) -> float:
        return self.resultTiltSpinBox.value()

    @tilt.setter
    def tilt(self, value: float) -> None:
        self.resultTiltSpinBox.setValue(value)

    @property
    def slope(self) -> float:
        return self.resultSlopeSpinBox.value()

    @slope.setter
    def slope(self, value: float) -> None:
        self.resultSlopeSpinBox.setValue(value)

    @property
    def max_proj_angle(self) -> float:
        return self.maxProjAngleSpinBox.value()

    @property
    def algorithm_name(self) -> str:
        return self.algorithmNameComboBox.currentText()

    @property
    def filter_name(self) -> str:
        return self.filterNameComboBox.currentText()

    @property
    def num_iter(self) -> int:
        return self.numIterSpinBox.value()

    @num_iter.setter
    def num_iter(self, iters: int) -> None:
        self.numIterSpinBox.setValue(iters)

    @property
    def pixel_size(self) -> float:
        return self.pixelSizeSpinBox.value()

    @pixel_size.setter
    def pixel_size(self, value: int) -> None:
        with QSignalBlocker(self.pixelSizeSpinBox):
            self.pixelSizeSpinBox.setValue(value)

    @property
    def alpha(self) -> float:
        return self.alphaSpinBox.value()

    @property
    def gamma(self) -> float:
        return 1

    @property
    def non_negative(self) -> bool:
        return self.nonNegativeCheckBox.isChecked()

    @property
    def stochastic(self) -> bool:
        return self.stochasticCheckBox.isChecked()

    @property
    def projections_per_subset(self) -> int:
        return self.subsetsSpinBox.value()

    @property
    def regularisation_percent(self) -> int:
        return self.regPercentSpinBox.value()

    @property
    def regulariser(self) -> str:
        return "TV"

    @property
    def beam_hardening_coefs(self) -> list[float] | None:
        if not self.lbhcEnabledCheckBox.isChecked():
            return None
        params = []
        for spinbox in [self.lbhcA0SpinBox, self.lbhcA1SpinBox, self.lbhcA2SpinBox, self.lbhcA3SpinBox]:
            params.append(spinbox.value())
        if any(params):
            return params
        else:
            return None

    @property
    def current_stack_uuid(self) -> UUID | None:
        return self.stackSelector.current()

    def recon_params(self) -> ReconstructionParameters:
        return ReconstructionParameters(algorithm=self.algorithm_name,
                                        filter_name=self.filter_name,
                                        num_iter=self.num_iter,
                                        cor=ScalarCoR(self.rotation_centre),
                                        tilt=Degrees(self.tilt),
                                        pixel_size=self.pixel_size,
                                        alpha=self.alpha,
                                        gamma=self.gamma,
                                        non_negative=self.non_negative,
                                        stochastic=self.stochastic,
                                        projections_per_subset=self.projections_per_subset,
                                        max_projection_angle=self.max_proj_angle,
                                        regularisation_percent=self.regularisation_percent,
                                        regulariser=self.regulariser,
                                        beam_hardening_coefs=self.beam_hardening_coefs)

    def set_table_point(self, idx, slice_idx, cor) -> None:
        # reset_results=False stops the resetting of the data model on
        # changing a point from here - otherwise calculating the CoR
        # for each slice from tilt ends up resetting the model afterwards
        # (while it's containing the correct results)
        # Manual CoR typed by the user will still reset it, as that is
        # handled as an internal Qt event in the model
        self.cor_table_model.set_point(idx, slice_idx, cor, reset_results=False)

    def show_recon_volume(self, data: ImageStack, stack_id: UUID) -> None:
        self.main_window.add_recon_to_dataset(data, stack_id)

    def hide_tilt(self) -> None:
        self.image_view.hide_cor_line()

    def set_filters_for_recon_tool(self, filters: list[str]) -> None:
        self.filterNameComboBox.clear()
        self.filterNameComboBox.insertItems(0, filters)

    def get_number_of_cors(self) -> int | None:
        num, accepted = QInputDialog.getInt(self,
                                            "Number of slices",
                                            "On how many slices to run the automatic CoR finding?",
                                            value=6,
                                            min=2,
                                            max=30,
                                            step=1,
                                            flags=INPUT_DIALOG_FLAGS)
        if accepted:
            return num
        else:
            return None

    def get_auto_cor_method(self) -> AutoCorMethod:
        current = self.autoFindMethod.currentText()
        if current == "Correlation":
            return AutoCorMethod.CORRELATION
        else:
            return AutoCorMethod.MINIMISATION_SQUARE_SUM

    def set_correlate_buttons_enabled(self, enabled: bool) -> None:
        self.correlateButton.setEnabled(enabled)
        self.minimiseButton.setEnabled(enabled)

    def open_help_webpage(self, page: str) -> None:
        try:
            open_help_webpage(SECTION_USER_GUIDE, page)
        except RuntimeError as err:
            self.show_error_dialog(str(err))

    def change_refine_iterations(self) -> None:
        self.refineIterationsButton.setEnabled(self.algorithm_name == "SIRT_CUDA")

    def on_change_colour_palette(self) -> None:
        """
        Opens the Palette Changer window when the "Auto" button has been clicked.
        """
        self.changeColourPaletteDialog = PaletteChangerView(self,
                                                            self.image_view.imageview_recon.histogram,
                                                            self.image_view.imageview_recon.image_data,
                                                            recon_mode=True)
        self.changeColourPaletteDialog.show()

    def show_status_message(self, msg: str) -> None:
        """
        Shows a status message indicating that zero/negative/NaN pixels were found in the stack. If the msg argument is
        empty then this is taken to mean that no such pixels were found, so the warning message and icon are cleared.
        :param msg: The status message.
        """
        self.statusMessageTextEdit.setText(msg)
        if msg:
            self.messageIconLabel.setPixmap(QApplication.style().standardPixmap(QStyle.SP_MessageBoxCritical))
        else:
            self.messageIconLabel.clear()

    def set_recon_buttons_enabled(self, enabled: bool) -> None:
        self.reconstructSliceButton.setEnabled(enabled)
        self.reconstructVolumeButton.setEnabled(enabled)

    def set_max_projection_index(self, max_index: int) -> None:
        self.previewProjectionIndexSpinBox.setMaximum(max_index)

    def set_max_slice_index(self, max_index: int) -> None:
        self.previewSliceIndexSpinBox.setMaximum(max_index)
