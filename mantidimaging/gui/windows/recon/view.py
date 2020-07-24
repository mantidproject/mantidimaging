from typing import TYPE_CHECKING, Optional, List

from PyQt5.QtWidgets import QAbstractItemView, QWidget, QDoubleSpinBox, QComboBox, QSpinBox, QPushButton, QVBoxLayout, \
    QInputDialog

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees, Slope, ReconstructionParameters
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets import RemovableRowTableView
from mantidimaging.gui.windows.recon.image_view import ReconImagesView
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel, Column
from mantidimaging.gui.windows.recon.presenter import ReconstructWindowPresenter, Notifications as PresN

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class ReconstructWindowView(BaseMainWindowView):
    tableView: RemovableRowTableView
    imageLayout: QVBoxLayout

    inputTab: QWidget
    calculateCors: QPushButton

    resultTab: QWidget
    addBtn: QPushButton
    refineCorBtn: QPushButton
    clearAllBtn: QPushButton
    removeBtn: QPushButton
    fitBtn: QPushButton

    autoBtn: QPushButton

    reconTab: QWidget

    # part of the Reconstruct tab
    algorithmName: QComboBox
    filterName: QComboBox
    numIter: QSpinBox
    maxProjAngle: QDoubleSpinBox
    resultCor: QDoubleSpinBox
    resultTilt: QDoubleSpinBox
    resultSlope: QDoubleSpinBox
    reconstructVolume: QPushButton

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/recon_window.ui')

        self.main_window = main_window
        self.presenter = ReconstructWindowPresenter(self, main_window)

        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)

        # Handle preview image selection
        self.previewProjectionIndex.valueChanged[int].connect(self.presenter.set_preview_projection_idx)
        self.previewSliceIndex.valueChanged[int].connect(self.presenter.set_preview_slice_idx)

        self.image_view = ReconImagesView(self)
        self.imageLayout.addWidget(self.image_view)

        # Point table
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.cor_table_model.rowsInserted.connect(self.on_table_row_count_change)
        self.cor_table_model.rowsRemoved.connect(self.on_table_row_count_change)
        self.cor_table_model.modelReset.connect(self.on_table_row_count_change)

        # Update previews when data in table changes
        def on_data_change(tl, br, _):
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
        self.fitBtn.clicked.connect(lambda: self.presenter.notify(PresN.COR_FIT))
        self.calculateCors.clicked.connect(lambda: self.presenter.notify(PresN.CALCULATE_CORS_FROM_MANUAL_TILT))
        self.reconstructVolume.clicked.connect(lambda: self.presenter.notify(PresN.RECONSTRUCT_VOLUME))

        self.autoBtn.clicked.connect(lambda: self.presenter.notify(PresN.AUTO_FIND_COR))

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
                self.presenter.notify(PresN.RECONSTRUCT_SLICE)

            # Only allow buttons which act on selected row to be clicked when a valid
            # row is selected
            for button in [self.refineCorBtn, self.removeBtn]:
                button.setEnabled(item.isValid())

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)

        # Update initial UI state
        self.on_table_row_count_change()

        self.stackSelector.subscribe_to_main_window(main_window)

        self.algorithmName.currentTextChanged.connect(lambda: self.presenter.notify(PresN.ALGORITHM_CHANGED))
        self.presenter.notify(PresN.ALGORITHM_CHANGED)

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
        return self.tableView.model()

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

        self.previewSliceIndex.setValue(preview_slice_index)

        self.image_view.update_projection(image_data, preview_slice_index, tilt_angle)

    def update_sinogram(self, image_data):
        self.image_view.update_sinogram(image_data)

    def update_recon_preview(self, image_data, refresh_recon_slice_histogram:bool):
        """
        Updates the reconstruction preview image with new data.
        """
        # Plot image
        if image_data is not None:
            self.image_view.update_recon(image_data, refresh_recon_slice_histogram)

    def reset_image_recon_preview(self):
        """
        Resets the recon preview image, forcing a complete redraw next time it
        is updated.
        """
        self.image_view.clear_recon()

    def reset_slice_and_tilt(self, slice_index):
        self.image_view.reset_slice_and_tilt(slice_index)

    def on_table_row_count_change(self):
        """
        Called when rows have been added or removed from the point table.

        Used to conditionally enable UI controls that depend on a certain
        amount of entries in the table.
        """
        # Disable clear buttons when there are no rows in the table
        empty = self.tableView.model().empty
        self.removeBtn.setEnabled(not empty)
        self.clearAllBtn.setEnabled(not empty)

        # Disable fit button when there are less than 2 rows (points)
        enough_to_fit = self.tableView.model().num_points >= 2
        self.fitBtn.setEnabled(enough_to_fit)

    def add_cor_table_row(self, row: Optional[int], slice_index: int, cor: float):
        """
        Adds a row to the manual COR table with a specified slice index.
        """
        self.cor_table_model.appendNewRow(row, slice_index, cor)

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

    def recon_params(self) -> ReconstructionParameters:
        return ReconstructionParameters(self.algorithm_name, self.filter_name, self.num_iter)

    def set_table_point(self, idx, slice_idx, cor):
        # reset_results=False stops the resetting of the data model on
        # changing a point from here - otherwise calculating the CoR
        # for each slice from tilt ends up resetting the model afterwards
        # (while it's containing the correct results)
        # Manual CoR typed by the user will still reset it, as that is
        # handled as an internal Qt event in the model
        self.cor_table_model.set_point(idx, slice_idx, cor, reset_results=False)

    def show_recon_volume(self, data: Images):
        self.main_window.create_new_stack(data, "Recon")

    def get_stack_visualiser(self, uuid):
        if uuid is not None:
            return self.main_window.get_stack_visualiser(uuid)

    def hide_tilt(self):
        self.image_view.hide_tilt()

    def set_filters_for_recon_tool(self, filters: List[str]):
        self.filterName.clear()
        self.filterName.insertItems(0, filters)

    def get_number_of_cors(self) -> int:
        num, accepted = QInputDialog.getInt(self, "Number of slices",
                                            "On how many slices to run the automatic CoR finding?",
                                            value=6, min=0, max=30, step=1)
        if accepted:
            return num
