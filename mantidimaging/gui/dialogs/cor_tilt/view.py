from __future__ import absolute_import, division, print_function

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.gui.mvp_base import BaseDialogView

from .presenter import CORTiltDialogPresenter
from .presenter import Notification as PresNotification


class CORTiltDialogView(BaseDialogView):

    def __init__(self, main_window, cmap='Greys_r'):
        super(CORTiltDialogView, self).__init__(
                main_window, 'gui/ui/cor_tilt_dialog.ui')

        self.presenter = CORTiltDialogPresenter(self, main_window)

        self.cmap = cmap

        # Handle calculate button click
        self.calculateButton.clicked.connect(
                lambda: self.presenter.notify(PresNotification.RUN))

        # Handle stack selection
        self.stackSelector.subscribe_to_main_window(main_window)
        self.stackSelector.stack_selected_uuid.connect(
                self.presenter.set_stack_uuid)

        # Handle stack cropping
        self.setRoi.clicked.connect(
                lambda: self.presenter.notify(PresNotification.CROP_TO_ROI))

        # Handle preview image selection
        self.previewStackIndex.valueChanged[int].connect(
                self.presenter.set_preview_idx)

        # Handle index definition
        self.sliceCount.valueChanged[int].connect(
                lambda: self.presenter.notify(PresNotification.UPDATE_INDICES))
        self.projectionCount.valueChanged[int].connect(
                lambda: self.presenter.notify(
                    PresNotification.UPDATE_PROJECTIONS))

        def add_mpl_figure(layout):
            figure = Figure()
            canvas = FigureCanvasQTAgg(figure)
            canvas.setParent(self)
            layout.addWidget(canvas)
            return (figure, canvas)

        # Image plot
        self.image_figure, self.image_canvas = add_mpl_figure(self.imageLayout)
        self.image_plot = self.image_figure.add_subplot(111)

        # Linear fit plot
        self.fit_figure, self.fit_canvas = add_mpl_figure(self.fitLayout)
        self.fit_plot = self.fit_figure.add_subplot(111)
        self.update_fit_plot(None, None, None)

        self.set_results(0, 0)

    def set_results(self, cor, tilt):
        self.resultCor.setValue(cor)
        self.resultTilt.setValue(tilt)

    def update_image_preview(self,
                             image_data,
                             tilt_line_points=None,
                             roi=None):
        self.image_plot.cla()

        # Plot image
        if image_data is not None:
            self.image_plot.imshow(image_data, cmap=self.cmap)

        # Plot tilt line
        if tilt_line_points is not None:
            self.image_plot.plot(*tilt_line_points, lw=2, c='y')

        # Set zoom level to ROI
        if roi is not None:
            self.image_plot.set_xlim((roi[0], roi[2]))
            self.image_plot.set_ylim((roi[3], roi[1]))

        self.image_canvas.draw()

    def update_fit_plot(self, x_axis, cor_data, fit_data):
        self.fit_plot.cla()

        # Set axes labels
        self.fit_plot.set_xlabel('Slice')
        self.fit_plot.set_ylabel('COR')

        # Plot COR data
        if cor_data is not None:
            self.fit_plot.plot(x_axis, cor_data)

        # Plot fit
        if fit_data is not None:
            self.fit_plot.plot(x_axis, fit_data)

        self.fit_canvas.draw()

    def set_max_preview_idx(self, max_idx):
        self.previewStackIndex.setValue(0)
        self.previewStackIndex.setMaximum(max_idx)

    @property
    def slice_count(self):
        return self.sliceCount.value()

    @property
    def projection_count(self):
        return self.projectionCount.value()
