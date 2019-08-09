from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QAbstractItemView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.core.cor_tilt import Field
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets import NavigationToolbarSimple
from .point_table_model import CorTiltPointQtModel
from .presenter import CORTiltWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class CORTiltWindowView(BaseMainWindowView):

    def __init__(self, main_window: 'MainWindowView', cmap='Greys_r'):
        super(CORTiltWindowView, self).__init__(
            main_window, 'gui/ui/cor_tilt_window.ui')

        self.main_window = main_window
        self.presenter = CORTiltWindowPresenter(self, main_window)

        self.cmap = cmap

        # Handle calculate button click
        self.autoCalculateButton.clicked.connect(lambda: self.presenter.notify(PresNotification.RUN_AUTOMATIC))

        # Handle stack selection
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)

        # Handle stack cropping
        self.setRoi.clicked.connect(lambda: self.presenter.notify(PresNotification.CROP_TO_ROI))

        # Handle preview image selection
        self.previewProjectionIndex.valueChanged[int].connect(self.presenter.set_preview_projection_idx)
        self.previewSliceIndex.valueChanged[int].connect(self.presenter.set_preview_slice_idx)

        # Handle calculation parameters
        self.projectionCountReset.clicked.connect(self.reset_projection_count)

        def add_mpl_figure(layout, toolbar=None):
            figure = Figure()
            canvas = FigureCanvasQTAgg(figure)
            canvas.setParent(self)
            if toolbar is not None:
                toolbar = toolbar(canvas, self)
                layout.addWidget(toolbar)
            layout.addWidget(canvas)
            return figure, canvas, toolbar

        # Image plot
        self.image_figure, self.image_canvas, _ = \
            add_mpl_figure(self.imageLayout)
        self.image_plot = self.image_figure.add_subplot(111)
        self.image_canvas.mpl_connect(
            'button_press_event', self.preview_image_on_button_press)

        # Reconstruction preview plot
        self.recon_figure, self.recon_canvas, self.recon_toolbar = \
            add_mpl_figure(self.reconPreviewLayout, NavigationToolbarSimple)
        self.recon_plot = self.recon_figure.add_subplot(111)
        self.recon_image = None

        # Linear fit plot
        self.fit_figure, self.fit_canvas, _ = add_mpl_figure(self.fitLayout)
        self.fit_plot = self.fit_figure.add_subplot(111)
        self.update_fit_plot(None, None, None)
        self.fit_canvas.mpl_connect(
            'button_press_event', self.handle_fit_plot_button_press)
        self.fit_canvas.setToolTip(
            'Double click to open a larger plot (requires at least '
            '2 points)')

        # Point table
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.tableView.model().rowsInserted.connect(
            self.on_table_row_count_change)
        self.tableView.model().rowsRemoved.connect(
            self.on_table_row_count_change)
        self.tableView.model().modelReset.connect(
            self.on_table_row_count_change)

        # Update previews when data in table changes
        def on_data_change(tl, br, _):
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)
            if tl == br and tl.column() == Field.CENTRE_OF_ROTATION.value:
                mdl = self.tableView.model()
                slice_idx = mdl.data(
                    mdl.index(tl.row(), Field.SLICE_INDEX.value))
                self.presenter.handle_cor_manually_changed(slice_idx)

        self.tableView.model().rowsRemoved.connect(
            lambda: self.presenter.notify(
                PresNotification.UPDATE_PREVIEWS))
        self.tableView.model().dataChanged.connect(on_data_change)

        self.manualClearAllButton.clicked.connect(
            self.tableView.model().removeAllRows)
        self.manualRemoveButton.clicked.connect(
            self.tableView.removeSelectedRows)
        self.manualAddButton.clicked.connect(
            lambda: self.presenter.notify(
                PresNotification.ADD_NEW_COR_TABLE_ROW))
        self.manualRefineCorButton.clicked.connect(
            lambda: self.presenter.notify(
                PresNotification.REFINE_SELECTED_COR))
        self.manualFitButton.clicked.connect(
            lambda: self.presenter.notify(
                PresNotification.RUN_MANUAL))

        def on_row_change(item, _):
            """
            Handles setting preview slice index from the currently selected row
            in the manual COR table.
            """
            if item.isValid():
                slice_idx = item.model().point(item.row())[
                    Field.SLICE_INDEX.value]
                self.presenter.set_preview_slice_idx(slice_idx)
                self.presenter.notify(
                    PresNotification.PREVIEW_RECONSTRUCTION_SET_COR)

            # Only allow the refine button to be clicked when a valid row is
            # selected
            self.manualRefineCorButton.setEnabled(item.isValid())

        self.tableView.selectionModel().currentRowChanged.connect(
            on_row_change)

        # Update initial UI state
        self.on_table_row_count_change()
        self.set_results(0, 0, 0)

        self.stackSelector.subscribe_to_main_window(main_window)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()

    @property
    def point_model(self):
        if self.tableView.model() is None:
            mdl = CorTiltPointQtModel(self.tableView)
            self.tableView.setModel(mdl)
        return self.tableView.model()

    def set_results(self, cor, tilt, gradient):
        """
        Sets the numerical COR and tilt angle results.
        """
        self.resultCor.setValue(cor)
        self.resultTilt.setValue(tilt)
        self.resultGradient.setValue(gradient)

    def update_image_preview(self,
                             image_data,
                             preview_slice_index,
                             tilt_line_points=None,
                             roi=None):
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
        self.image_plot.cla()

        self.previewSliceIndex.setValue(preview_slice_index)

        # Plot image
        if image_data is not None:
            self.image_plot.imshow(image_data, cmap=self.cmap)

            # Plot preview slice line
            x_max = image_data.shape[1] - 1
            self.image_plot.plot(
                [0, x_max],
                [preview_slice_index, preview_slice_index],
                c='y')

        # Plot tilt line
        if tilt_line_points is not None:
            self.image_plot.plot(*tilt_line_points, lw=1, c='r')

        # Set zoom level to ROI
        if roi is not None:
            self.image_plot.set_xlim((roi[0], roi[2]))
            self.image_plot.set_ylim((roi[3], roi[1]))

        self.image_canvas.draw()

    def preview_image_on_button_press(self, event):
        """
        Handles mouse button presses on the preview projection image.

        Used to set the preview slice when a user clicks on a given part of the
        image.
        """
        if event.button == 1 and event.ydata is not None:
            self.presenter.set_preview_slice_idx(int(event.ydata))

    def update_image_recon_preview(self, image_data):
        """
        Updates the reconstruction preview image with new data.
        """
        # Plot image
        if image_data is not None:
            # Cache image
            # Saves time when drawing and maintains image extents
            if self.recon_image is None:
                self.recon_image = self.recon_plot.imshow(
                    image_data, cmap=self.cmap)
            else:
                self.recon_image.set_data(image_data)
                self.recon_image.autoscale()

        self.recon_canvas.draw()

    def reset_image_recon_preview(self):
        """
        Resets the recon preview image, forcing a complete redraw next time it
        is updated.
        """
        self.recon_plot.cla()
        self.recon_image = None

    def update_fit_plot(self, x_axis, cor_data, fit_data):
        """
        Updates the fit result preview plot with the data provided.

        :param x_axis: Common x axis data (slice index)
        :param cor_data: Centre of rotation determined per slice
        :param fit_data: Result of linear fitting of per slice centre of
                         rotation
        """
        self.fit_plot.cla()

        # Plot COR data
        if cor_data is not None:
            self.fit_plot.plot(x_axis, cor_data)

        # Plot fit
        if fit_data is not None:
            self.fit_plot.plot(x_axis, fit_data)

        # Remove axes ticks to save screen space
        self.fit_plot.set_xticks([])
        self.fit_plot.set_yticks([])

        # Use tight layout to reduce unused canvas space
        # https://matplotlib.org/users/tight_layout_guide.html
        self.fit_figure.tight_layout()

        self.fit_canvas.draw()

    def handle_fit_plot_button_press(self, event):
        """
        Handle mouse button presses on the fit plot preview.

        Currently opens a larger version of the plot in a new window when the
        plot is double (left) clicked.
        """
        # Double left click
        if event.button == 1 and event.dblclick:
            self.presenter.notify(PresNotification.SHOW_COR_VS_SLICE_PLOT)

    def set_num_projections(self, count):
        """
        Set the number of projections in the input dataset.
        """
        # Preview image control
        self.previewProjectionIndex.setValue(0)
        self.previewProjectionIndex.setMaximum(max(count - 1, 0))

        # Projection downsample control
        self.projectionCount.setMaximum(count)
        self.projectionCount.setValue(int(count * 0.1))

    def set_num_slices(self, count):
        """
        Sets the number of slices (projection Y axis size) of the full input
        image.
        """
        # Preview image control
        self.previewSliceIndex.setValue(0)
        self.previewSliceIndex.setMaximum(max(count - 1, 0))

    def reset_projection_count(self):
        """
        Resets the number of projections to the maximum available.
        """
        self.projectionCount.setValue(self.projectionCount.maximum())

    def show_results(self):
        """
        Shows results after finding is complete.

        Specifically switch to the "Results" tab.
        """
        self.tabWidget.setCurrentWidget(self.resultsTab)

    def on_table_row_count_change(self):
        """
        Called when rows have been added or removed from the point table.

        Used to conditionally enable UI controls that depend on a certain
        amount of entries in the table.
        """
        # Disable clear buttons when there are no rows in the table
        empty = self.tableView.model().empty
        self.manualRemoveButton.setEnabled(not empty)
        self.manualClearAllButton.setEnabled(not empty)

        # Update previews when no data is left
        if empty:
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

        # Disable fit button when there are less than 2 rows (points)
        enough_to_fit = self.tableView.model().num_points >= 2
        self.manualFitButton.setEnabled(enough_to_fit)

    def add_cor_table_row(self, idx, cor):
        """
        Adds a row to the manual COR table with a specified slice index.
        """
        self.tableView.model().appendNewRow(idx, cor)

    @property
    def slice_count(self):
        """
        The number of slices/sinograms the user has selected for automatic
        COR/Tilt finding.
        """
        return self.sliceCount.value()

    @property
    def projection_count(self):
        """
        The number of projections the user has selected for automatic COR/Tilt
        finding.
        """
        return self.projectionCount.value()
