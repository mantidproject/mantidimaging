from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.utility import BlockQtSignals
from mantidimaging.gui.widgets import NavigationToolbarSimple

from .presenter import (CORInspectionDialogPresenter, Notification as PresNotification)


class CORInspectionDialogView(BaseDialogView):
    def __init__(self, parent, cmap='Greys_r', **args):
        super(CORInspectionDialogView, self).__init__(parent, 'gui/ui/cor_inspection_dialog.ui')

        self.presenter = CORInspectionDialogPresenter(self, **args)
        self.cmap = cmap

        # Completed button action
        self.finishButton.clicked.connect(self.accept)

        # Image canvas
        self.image_figure = Figure(tight_layout=True)
        self.image_canvas = FigureCanvasQTAgg(self.image_figure)
        self.image_canvas.setParent(self)
        self.imagePlotLayout.addWidget(self.image_canvas)
        self.image_plots = self.image_figure.subplots(1, 3, sharex=True, sharey=True)

        # Common image toolbar (attached to centre image)
        self.plot_toolbar = NavigationToolbarSimple(self.image_canvas, self)
        self.plotToolbarLayout.addWidget(self.plot_toolbar)
        #
        # # Handle best image selection
        # self.lessButton.pressed.connect(lambda: self.presenter.notify(PresNotification.IMAGE_CLICKED_LESS))
        # self.currentButton.pressed.connect(lambda: self.presenter.notify(PresNotification.IMAGE_CLICKED_CURRENT))
        # self.moreButton.pressed.connect(lambda: self.presenter.notify(PresNotification.IMAGE_CLICKED_MORE))

        # Handle parameter updates
        # self.step.valueChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PARAMETERS_FROM_UI))

        self._image_cache = [None, None, None]

        # Ensure initial state
        self.presenter.notify(PresNotification.LOADED)

    def set_image(self, image_type, data, title):
        """
        Sets the image displayed in a given position and it's title.
        """
        plot = self.image_plots[image_type.value]
        image = self._image_cache[image_type.value]

        # Cache the image object so that subsequent plots only have to replace
        # the data
        if image is None:
            self._image_cache[image_type.value] = \
                    plot.imshow(data, cmap=self.cmap)
        else:
            image.set_data(data)
            image.autoscale()

        plot.set_title(title)

    def image_canvas_draw(self):
        self.image_canvas.draw()

    def set_maximum_cor(self, cor):
        """
        Set the maximum valid rotation centre.
        """
        self.step.setMaximum(cor)

    @property
    def step_size(self):
        return self.step.value()

    @step_size.setter
    def step_size(self, value):
        with BlockQtSignals([self.step]):
            self.step.setValue(value)

    @property
    def optimal_rotation_centre(self):
        return self.presenter.optimal_rotation_centre
