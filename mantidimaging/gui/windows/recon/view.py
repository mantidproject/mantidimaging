from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QAbstractItemView, QWidget, QDoubleSpinBox, QComboBox, QSpinBox, QPushButton, QVBoxLayout

from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets import RemovableRowTableView
from mantidimaging.gui.windows.recon.image_view import ReconImagesView
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel, Column
from mantidimaging.gui.windows.recon.presenter import Notification as PresNotification
from mantidimaging.gui.windows.recon.presenter import ReconstructWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class ReconstructWindowView(BaseMainWindowView):
    tableView: RemovableRowTableView
    imageLayout: QVBoxLayout
    inputTab: QWidget
    setRoiBtn: QPushButton
    autoCalculateBtn: QPushButton
    corFindingMethod: QComboBox

    resultTab: QWidget
    addBtn: QPushButton
    refineCorBtn: QPushButton
    clearAllBtn: QPushButton
    removeBtn: QPushButton
    fitBtn: QPushButton

    reconTab: QWidget

    # part of the Reconstruct tab
    algorithmName: QComboBox
    filterName: QComboBox
    numIter: QSpinBox
    maxProjAngle: QDoubleSpinBox
    resultCor: QDoubleSpinBox
    resultTilt: QDoubleSpinBox
    reconstructSlice: QPushButton
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

        self.tableView.model().rowsInserted.connect(self.on_table_row_count_change)
        self.tableView.model().rowsRemoved.connect(self.on_table_row_count_change)
        self.tableView.model().modelReset.connect(self.on_table_row_count_change)

        # Update previews when data in table changes
        def on_data_change(tl, br, _):
            self.presenter.do_update_projection()
            if tl == br and tl.column() == Column.CENTRE_OF_ROTATION.value:
                mdl = self.tableView.model()
                slice_idx = mdl.data(mdl.index(tl.row(), Column.SLICE_INDEX.value))
                self.presenter.do_user_click_recon(slice_idx)

        self.tableView.model().rowsRemoved.connect(lambda: self.presenter.do_update_projection())
        self.tableView.model().dataChanged.connect(on_data_change)

        self.clearAllBtn.clicked.connect(lambda: self.presenter.do_clear_all_cors())
        self.removeBtn.clicked.connect(lambda: self.presenter.do_remove_selected_cor())
        self.addBtn.clicked.connect(lambda: self.presenter.do_add_cor())
        self.refineCorBtn.clicked.connect(lambda: self.presenter.do_refine_selected_cor())
        self.setAllButton.clicked.connect(lambda: self.presenter.do_set_all_row_values())
        self.fitBtn.clicked.connect(lambda: self.presenter.do_cor_fit())
        self.setRoiBtn.clicked.connect(lambda: self.presenter.do_crop_to_roi())
        self.reconstructSlice.clicked.connect(lambda: self.presenter.do_reconstruct_slice())
        self.reconstructVolume.clicked.connect(lambda: self.presenter.do_reconstruct_volume())

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
                self.presenter.do_reconstruct_slice()

            # Only allow buttons which act on selected row to be clicked when a valid
            # row is selected
            for button in [self.refineCorBtn, self.setAllButton, self.removeBtn]:
                button.setEnabled(item.isValid())

        self.tableView.selectionModel().currentRowChanged.connect(on_row_change)

        # Update initial UI state
        self.on_table_row_count_change()

        self.stackSelector.subscribe_to_main_window(main_window)

        self.algorithmName.currentTextChanged.connect(lambda: self.presenter.do_algorithm_changed())
        self.presenter.do_algorithm_changed()

    def remove_selected_cor(self):
        return self.tableView.removeSelectedRows()

    def clear_cor_table(self):
        return self.tableView.model().removeAllRows()

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        self.main_window.recon = None

    @property
    def point_model(self):
        if self.tableView.model() is None:
            mdl = CorTiltPointQtModel(self.tableView)
            self.tableView.setModel(mdl)
        return self.tableView.model()

    def set_results(self, cor: ScalarCoR, tilt: Degrees):
        """
        Sets the numerical COR and tilt angle results.
        """
        self.rotation_centre = cor.value
        self.tilt = tilt.value
        self.image_view.set_tilt(tilt)

    def preview_image_on_button_press(self, event):
        """
        Handles mouse button presses on the preview projection image.

        Used to set the preview slice when a user clicks on a given part of the
        image.
        """
        if event.button == 1 and event.ydata is not None:
            self.presenter.set_preview_slice_idx(int(event.ydata))

    def update_image_preview(self, image_data, preview_slice_index, tilt_line_points=None, roi=None):
        """
        Updates the preview projection image and associated annotations.

        Region of interest sets the bounds of the image axes, it does not
        resize the data itself. The advantage of this is that the coordinates
        do not change.

        :param image_data: Projection image data (single/2D image)
        :param preview_slice_index: Y coordinate at which to draw the preview
                                    slice indicator
        :param tilt_line_points: Tuple of (X, Y) data points for tilt preview
                                 line
        :param roi: Region of interest to crop the image to
        """

        self.previewSliceIndex.setValue(preview_slice_index)

        self.image_view.update_projection(image_data, preview_slice_index, tilt_line_points, roi)

    def update_image_recon_preview(self, image_data):
        """
        Updates the reconstruction preview image with new data.
        """
        # Plot image
        if image_data is not None:
            self.image_view.update_recon(image_data)

    def reset_image_recon_preview(self):
        """
        Resets the recon preview image, forcing a complete redraw next time it
        is updated.
        """
        self.image_view.clear_recon()

    def reset_slice_and_tilt(self, slice_index):
        self.image_view.reset_slice_and_tilt(slice_index)

    def handle_fit_plot_button_press(self, event):
        """
        Handle mouse button presses on the fit plot preview.

        Currently opens a larger version of the plot in a new window when the
        plot is double (left) clicked.
        """
        # Double left click
        if event.button == 1 and event.dblclick:
            self.presenter.notify(PresNotification.SHOW_COR_VS_SLICE_PLOT)

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

        # Update previews when no data is left
        if empty:
            self.presenter.do_update_projection()

        # Disable fit button when there are less than 2 rows (points)
        enough_to_fit = self.tableView.model().num_points >= 2
        self.fitBtn.setEnabled(enough_to_fit)

    def add_cor_table_row(self, row: Optional[int], slice_index: int, cor: float):
        """
        Adds a row to the manual COR table with a specified slice index.
        """
        self.tableView.model().appendNewRow(row, slice_index, cor)

    @property
    def rotation_centre(self):
        return self.resultCor.value()

    @rotation_centre.setter
    def rotation_centre(self, value):
        self.resultCor.setValue(value)

    @property
    def tilt(self):
        return self.resultTilt.value()

    @tilt.setter
    def tilt(self, value):
        self.resultTilt.setValue(value)

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
        return self.numIter.value() if self.numIter.isVisible() else None
