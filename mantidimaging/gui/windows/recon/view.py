# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from logging import getLogger
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

import numpy
from PyQt5.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QInputDialog, QPushButton, QSpinBox,
                             QVBoxLayout, QWidget, QMessageBox, QTextEdit, QLabel, QApplication, QStyle, QCheckBox)
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

LOG = getLogger(__name__)


class ReconstructWindowView(BaseMainWindowView):
    tableView: RemovableRowTableView
    imageLayout: QVBoxLayout

    inputTab: QWidget
    calculateCors: QPushButton

    resultTab: QWidget
    addBtn: QPushButton
    refineCorBtn: QPushButton
    refineIterationsBtn: QPushButton
    clearAllBtn: QPushButton
    removeBtn: QPushButton

    correlateBtn: QPushButton
    minimiseBtn: QPushButton
    corHelpButton: QPushButton

    reconTab: QWidget

    # part of the Reconstruct tab
    algorithmName: QComboBox
    filterName: QComboBox
    numIter: QSpinBox
    maxProjAngle: QDoubleSpinBox
    pixelSize: QDoubleSpinBox
    alphaSpinbox: QDoubleSpinBox
    nonNegativeCheckBox: QCheckBox
    resultCor: QDoubleSpinBox
    resultTilt: QDoubleSpinBox
    resultSlope: QDoubleSpinBox
    reconstructVolume: QPushButton
    reconstructSlice: QPushButton

    lbhc_enabled: QCheckBox
    lbhc_a0: QDoubleSpinBox
    lbhc_a1: QDoubleSpinBox
    lbhc_a2: QDoubleSpinBox
    lbhc_a3: QDoubleSpinBox

    statusMessageTextEdit: QTextEdit
    messageIcon: QLabel

    changeColourPaletteButton: QPushButton
    change_colour_palette_dialog: Optional[PaletteChangerView] = None

    stackSelector: DatasetSelectorWidgetView

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/recon_window.ui')

        self.main_window = main_window
        self.presenter = ReconstructWindowPresenter(self, main_window)

        if CudaChecker().cuda_is_present():
            self.algorithmName.insertItem(0, "FBP_CUDA")
            self.algorithmName.insertItem(1, "SIRT_CUDA")
            self.algorithmName.insertItem(2, "CIL: PDHG-TV")
            self.algorithmName.setCurrentIndex(0)
            self.algorithmName.setEnabled(True)

        self.update_recon_hist_needed = False
        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)

        # Handle preview image selection
        self.previewProjectionIndex.valueChanged[int].connect(self.presenter.set_preview_projection_idx)
        self.previewSliceIndex.valueChanged[int].connect(self.presenter.set_preview_slice_idx)

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

        self.clearAllBtn.clicked.connect(lambda: self.presenter.notify(PresN.CLEAR_ALL_CORS))
        self.removeBtn.clicked.connect(lambda: self.presenter.notify(PresN.REMOVE_SELECTED_COR))
        self.addBtn.clicked.connect(lambda: self.presenter.notify(PresN.ADD_COR))
        self.refineCorBtn.clicked.connect(lambda: self.presenter.notify(PresN.REFINE_COR))
        self.refineIterationsBtn.clicked.connect(lambda: self.presenter.notify(PresN.REFINE_ITERS))
        self.calculateCors.clicked.connect(lambda: self.presenter.notify(PresN.CALCULATE_CORS_FROM_MANUAL_TILT))
        self.reconstructVolume.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_VOLUME))
        self.reconstructSlice.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_STACK_SLICE))

        self.correlateBtn.clicked.connect(lambda: self.presenter.notify(PresN.AUTO_FIND_COR_CORRELATE))
        self.minimiseBtn.clicked.connect(lambda: self.presenter.notify(PresN.AUTO_FIND_COR_MINIMISE))

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
            for button in [self.refineCorBtn, self.removeBtn]:
                button.setEnabled(item.isValid())

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)  # type: ignore

        # Update initial UI state
        self.on_table_row_count_change()

        self.stackSelector.subscribe_to_main_window(main_window)
        self.stackSelector.stack_selected_uuid.connect(self.check_stack_for_invalid_180_deg_proj)
        self.stackSelector.select_eligible_stack()

        self.maxProjAngle.valueChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore
        self.algorithmName.currentTextChanged.connect(
            lambda: self.presenter.notify(PresN.ALGORITHM_CHANGED))  # type: ignore
        self.presenter.notify(PresN.ALGORITHM_CHANGED)
        self.filterName.currentTextChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore
        self.numIter.valueChanged.connect(
            lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))  # type: ignore

        self.pixelSize.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.alphaSpinbox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.nonNegativeCheckBox.stateChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
        self.reconHelpButton.clicked.connect(lambda: self.open_help_webpage("reconstructions/index"))
        self.corHelpButton.clicked.connect(lambda: self.open_help_webpage("reconstructions/center_of_rotation"))

        self.previewAutoUpdate.stateChanged.connect(self.handle_auto_update_preview_selection)
        self.updatePreviewButton.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_USER_CLICK))

        for spinbox in [self.lbhc_a0, self.lbhc_a1, self.lbhc_a2, self.lbhc_a3]:
            spinbox.valueChanged.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))
            self.lbhc_enabled.toggled.connect(spinbox.setEnabled)
        self.lbhc_enabled.toggled.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE))

    def showEvent(self, e):
        if self.presenter.stack_changed_pending:
            self.presenter.handle_stack_changed()
            self.presenter.stack_changed_pending = False

    def closeEvent(self, e):
        if self.presenter.recon_is_running:
            e.ignore()
        else:
            self.hide()

    def check_stack_for_invalid_180_deg_proj(self, uuid: UUID):
        try:
            selected_images = self.main_window.get_images_from_stack_uuid(uuid)
        except KeyError:
            # Likely due to stack no longer existing, e.g. when all stacks closed
            LOG.debug("UUID did not match open stack")
            return
        if selected_images.has_proj180deg() and \
                not self.presenter.proj_180_degree_shape_matches_images(selected_images):
            self.warn_user(
                "Potential Failure",
                "The shapes of the selected stack and it's 180 degree projections do not match! This is "
                "going to cause an error when calculating the COR. Fix the shape before continuing!")

    def warn_user(self, title, message):
        QMessageBox.warning(self, title, message)

    def remove_selected_cor(self):
        return self.tableView.removeSelectedRows()

    def clear_cor_table(self):
        return self.cor_table_model.removeAllRows()

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        self.main_window.recon = None

    @property
    def cor_table_model(self) -> CorTiltPointQtModel:
        if self.tableView.model() is None:
            mdl = CorTiltPointQtModel(self.tableView)
            self.tableView.setModel(mdl)
        return self.tableView.model()  # type: ignore

    def set_results(self, cor: ScalarCoR, tilt: Degrees, slope: Slope):
        """
        Sets the numerical COR and tilt angle results.
        """
        self.rotation_centre = cor.value
        self.tilt = tilt.value
        self.slope = slope.value
        self.image_view.set_tilt(tilt)

    def preview_image_on_button_press(self, event):
        """
        Handles mouse button presses on the preview projection image.

        Used to set the preview slice when a user clicks on a given part of the
        image.
        """
        if event.button == 1 and event.ydata is not None:
            self.presenter.set_preview_slice_idx(int(event.ydata))

    def update_projection(self, image_data, preview_slice_index: int, tilt_angle: Optional[Degrees]):
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

        with QSignalBlocker(self.previewSliceIndex):
            self.previewSliceIndex.setValue(preview_slice_index)

        self.image_view.update_projection(image_data, preview_slice_index, tilt_angle)

    def update_sinogram(self, image_data):
        self.image_view.update_sinogram(image_data)

    def is_auto_update_preview(self) -> bool:
        return self.previewAutoUpdate.isChecked()

    def handle_auto_update_preview_selection(self):
        if self.previewAutoUpdate.isChecked():
            self.presenter.notify(PresN.RECONSTRUCT_PREVIEW_SLICE)

    def update_recon_preview(self, image_data: numpy.ndarray):
        """
        Updates the reconstruction preview image with new data.
        """
        # Plot image
        self.image_view.update_recon(image_data)
        if self.update_recon_hist_needed:
            self.image_view.update_recon_hist()
            self.update_recon_hist_needed = False

    def reset_recon_and_sino_previews(self):
        """
        Resets the recon and sinogram preview images, forcing a complete redraw next time they
        are updated.
        """
        self.image_view.clear_recon()
        self.image_view.clear_sinogram()

    def reset_projection_preview(self):
        self.image_view.clear_projection()

    def reset_slice_and_tilt(self, slice_index):
        self.image_view.reset_slice_and_tilt(slice_index)

    def on_table_row_count_change(self, _=None, __=None):
        """
        Called when rows have been added or removed from the point table.

        Used to conditionally enable UI controls that depend on a certain
        amount of entries in the table.
        """
        # Disable clear buttons when there are no rows in the table
        empty = self.tableView.model().empty
        self.removeBtn.setEnabled(not empty)
        self.clearAllBtn.setEnabled(not empty)

    def add_cor_table_row(self, row: int, slice_index: int, cor: float):
        """
        Adds a row to the manual COR table with a specified slice index.
        """
        self.cor_table_model.appendNewRow(row, slice_index, cor)
        self.tableView.selectRow(row)

    def get_cor_table_selected_rows(self) -> List[int]:
        rows = self.tableView.selectionModel().selectedRows()
        return [row.row() for row in rows]

    @property
    def rotation_centre(self):
        return self.resultCor.value()

    @rotation_centre.setter
    def rotation_centre(self, value: float):
        self.resultCor.setValue(value)

    @property
    def tilt(self):
        return self.resultTilt.value()

    @tilt.setter
    def tilt(self, value: float):
        self.resultTilt.setValue(value)

    @property
    def slope(self):
        return self.resultSlope.value()

    @slope.setter
    def slope(self, value: float):
        self.resultSlope.setValue(value)

    @property
    def max_proj_angle(self):
        return self.maxProjAngle.value()

    @property
    def algorithm_name(self):
        return self.algorithmName.currentText()

    @property
    def filter_name(self):
        return self.filterName.currentText()

    @property
    def num_iter(self):
        return self.numIter.value()

    @num_iter.setter
    def num_iter(self, iters: int):
        self.numIter.setValue(iters)

    @property
    def pixel_size(self):
        return self.pixelSize.value()

    @pixel_size.setter
    def pixel_size(self, value: int):
        with QSignalBlocker(self.pixelSize):
            self.pixelSize.setValue(value)

    @property
    def alpha(self):
        return self.alphaSpinbox.value()

    @alpha.setter
    def alpha(self, value: float):
        self.alphaSpinbox.setValue(value)

    @property
    def non_negative(self):
        return self.nonNegativeCheckBox.isChecked()

    @property
    def beam_hardening_coefs(self) -> Optional[List[float]]:
        if not self.lbhc_enabled.isChecked():
            return None
        params = []
        for spinbox in [self.lbhc_a0, self.lbhc_a1, self.lbhc_a2, self.lbhc_a3]:
            params.append(spinbox.value())
        if any(params):
            return params
        else:
            return None

    def recon_params(self) -> ReconstructionParameters:
        return ReconstructionParameters(algorithm=self.algorithm_name,
                                        filter_name=self.filter_name,
                                        num_iter=self.num_iter,
                                        cor=ScalarCoR(self.rotation_centre),
                                        tilt=Degrees(self.tilt),
                                        pixel_size=self.pixel_size,
                                        alpha=self.alpha,
                                        non_negative=self.non_negative,
                                        max_projection_angle=self.max_proj_angle,
                                        beam_hardening_coefs=self.beam_hardening_coefs)

    def set_table_point(self, idx, slice_idx, cor):
        # reset_results=False stops the resetting of the data model on
        # changing a point from here - otherwise calculating the CoR
        # for each slice from tilt ends up resetting the model afterwards
        # (while it's containing the correct results)
        # Manual CoR typed by the user will still reset it, as that is
        # handled as an internal Qt event in the model
        self.cor_table_model.set_point(idx, slice_idx, cor, reset_results=False)

    def show_recon_volume(self, data: ImageStack, stack_id: uuid.UUID):
        self.main_window.add_recon_to_dataset(data, stack_id)

    def get_stack(self, uuid) -> Optional['ImageStack']:
        if uuid is not None:
            return self.main_window.get_stack(uuid)
        return None

    def hide_tilt(self):
        self.image_view.hide_tilt()

    def set_filters_for_recon_tool(self, filters: List[str]):
        self.filterName.clear()
        self.filterName.insertItems(0, filters)

    def get_number_of_cors(self) -> Optional[int]:
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

    def set_correlate_buttons_enabled(self, enabled: bool):
        self.correlateBtn.setEnabled(enabled)
        self.minimiseBtn.setEnabled(enabled)

    def open_help_webpage(self, page: str):
        try:
            open_help_webpage(SECTION_USER_GUIDE, page)
        except RuntimeError as err:
            self.show_error_dialog(str(err))

    def change_refine_iterations(self):
        self.refineIterationsBtn.setEnabled(self.algorithm_name == "SIRT_CUDA")

    def on_change_colour_palette(self):
        """
        Opens the Palette Changer window when the "Auto" button has been clicked.
        """
        self.change_colour_palette_dialog = PaletteChangerView(
            self, self.image_view.imageview_recon.histogram, self.image_view.imageview_recon.image_data,
            [self.image_view.imageview_sinogram.histogram, self.image_view.imageview_projection.histogram], True)
        self.change_colour_palette_dialog.show()

    def show_status_message(self, msg: str):
        """
        Shows a status message indicating that zero/negative/NaN pixels were found in the stack. If the msg argument is
        empty then this is taken to mean that no such pixels were found, so the warning message and icon are cleared.
        :param msg: The status message.
        """
        self.statusMessageTextEdit.setText(msg)
        if msg:
            self.messageIcon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_MessageBoxCritical))
        else:
            self.messageIcon.clear()
