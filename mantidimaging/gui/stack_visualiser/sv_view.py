from __future__ import absolute_import, division, print_function

import sys

from logging import getLogger
from PyQt5 import Qt, QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector, Slider

from mantidimaging.core.algorithms import gui_compile_ui
from mantidimaging.gui.stack_visualiser import sv_histogram
from mantidimaging.gui.stack_visualiser.sv_presenter import Notification as StackWindowNotification
from mantidimaging.gui.stack_visualiser.sv_presenter import StackVisualiserPresenter


class StackVisualiserView(Qt.QMainWindow):
    def __init__(self, parent, dock, images, data_traversal_axis=0, cmap='Greys_r', block=False):
        # enforce not showing a single image
        assert images.get_sample().ndim == 3, "Data does NOT have 3 dimensions! Dimensions found: {0}".format(
            images.get_sample().ndim)

        # We set the main window as the parent, the effect is the same as having no parent, the window
        # will be inside the QDockWidget. If the dock is set as a parent the window will be an independent
        # floating window
        super(StackVisualiserView, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/stack.ui', self)

        # capture the QDockWidget reference so that we can access the Qt widget and change things like the title
        self.dock = dock
        # Swap out the dock close event with our own provided close event. This is needed to manually
        # delete the data reference, otherwise it is left hanging in the presenter
        dock.closeEvent = self.closeEvent

        # View doesn't take ownership of the data!
        self.presenter = StackVisualiserPresenter(self, images, data_traversal_axis)

        self.figure = Figure()

        self.initialise_canvas()
        self._current_roi = None

        self.toolbar = NavigationToolbar2QT(self.canvas, self, coordinates=True)

        self.initialise_slider(data_traversal_axis, images)
        self.initialise_image(cmap)

        self.rectangle_selector = self.create_rectangle_selector(self.image_axis, 1)

        self.matplotlib_layout.addWidget(self.toolbar)
        self.matplotlib_layout.addWidget(self.canvas)

        self.setup_shortcuts()

    def initialise_image(self, cmap):
        """
        Initialises the image axis and the image object
        :param cmap: The color map which is to be used
        """
        self.image_axis = self.figure.add_subplot(111)
        self.image = self.image_axis.imshow(self.presenter.get_image(0), cmap=cmap)
        self.set_image_title_to_current_filename()

    def initialise_canvas(self):
        """
        Creates the canvas object from the figure
        """
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.rectanglecolor = QtCore.Qt.yellow
        self.canvas.setParent(self)

        # connect an event that will clear the ROI if the user clicks but does not drag a new ROI rectangle
        self.canvas.mpl_connect('button_press_event', self.remove_any_selected_roi)

    def initialise_slider(self, data_traversal_axis, images):
        """
        Creates the axis for the slider and initialises the slider
        :param data_traversal_axis:
        :param images:
        :return:
        """
        self.slider_axis = self.figure.add_axes(
            [0.25, 0.01, 0.5, 0.03], facecolor='lightgoldenrodyellow')
        self.slider = self.create_slider(self.slider_axis, images.get_sample().shape[data_traversal_axis] - 1)

    @property
    def current_roi(self):
        return self._current_roi

    @current_roi.setter
    def current_roi(self, value):
        self._current_roi = value

    def remove_any_selected_roi(self, event):
        """
        This removes the previously selected ROI. This function is called on a single
        button click and 2 things can happen:

        - If a rectangle selection is present and the user just single clicked, the ROI will be kept,
          because region_select_callback will be called afterwards

        - If a rectangle selection is no longer present the region_select_callback will not be called and the ROI will
          be deleted

        This assumes that the order will always be matplotlib on click event first,
        and then the rectangle selector callback.
        This might be a wrong assumption which could cause weird plotting issues. For now I have not seen an issue and
        the order seems to always be correct
        """
        self.current_roi = None

    def region_select_callback(self, eclick, erelease):
        # eclick and erelease are the press and release events
        left, top = eclick.xdata, eclick.ydata
        bottom, right = erelease.xdata, erelease.ydata

        self.current_roi = (int(left), int(top), int(right), int(bottom))
        region = "%i %i %i %i" % self.current_roi
        getLogger(__name__).info(region)

    def update_title_event(self):
        text, okPressed = Qt.QInputDialog.getText(
            self, "Rename window", "Enter new name", Qt.QLineEdit.Normal, "")

        if okPressed:
            self.dock.setWindowTitle(text)

    def setup_shortcuts(self):
        self.histogram_shortcut = Qt.QShortcut(
            Qt.QKeySequence("Shift+C"), self.dock)
        self.histogram_shortcut.activated.connect(
            lambda: self.presenter.notify(StackWindowNotification.HISTOGRAM))

        self.new_window_histogram_shortcut = Qt.QShortcut(
            Qt.QKeySequence("Ctrl+Shift+C"), self.dock)

        self.new_window_histogram_shortcut.activated.connect(
            lambda: self.presenter.notify(StackWindowNotification.NEW_WINDOW_HISTOGRAM))

        self.rename_shortcut = Qt.QShortcut(Qt.QKeySequence("F2"), self.dock)
        self.rename_shortcut.activated.connect(
            lambda: self.presenter.notify(StackWindowNotification.RENAME_WINDOW))

    def apply_to_data(self, algorithm_dialog):
        self.presenter.apply_to_data(algorithm_dialog)

    def closeEvent(self, event):
        # this removes all references to the data, allowing it to be GC'ed
        # otherwise there is a hanging reference
        self.presenter.delete_data()

        # setting floating to false makes window() to return the MainWindow
        # because the window will be docked in, however we delete it
        # immediately after so no visible change occurs
        self.parent().setFloating(False)

        # this could happen if run without a parent through see(..)
        if not isinstance(self.window(), Qt.QDockWidget):
            self.window().remove_stack(self)  # refers to MainWindow

        self.deleteLater()
        # refers to the QDockWidget within which the stack is contained
        self.parent().deleteLater()

    def create_rectangle_selector(self, axis, button=1):
        # drawtype is 'box' or 'line' or 'none', we could use 'line' to show COR, but the line
        # doesn't want to flip horizontally so it only ends up leaning right
        return RectangleSelector(
            axis,
            self.region_select_callback,
            drawtype='box',
            useblit=False,
            button=[1],  # don't use middle button
            spancoords='pixels',
            minspanx=20,
            minspany=20,
            interactive=True)

    def create_slider(self, slider_axis, length):
        slider = Slider(slider_axis, "Images", 0, length, valinit=0, valfmt='%i')

        slider.on_changed(self.show_current_image)
        return slider

    def current_index(self):
        """
        :return: Current selected index as integer
        """
        return int(self.slider.val)

    def current_image(self):
        """
        :return: The currently visualised image
        """
        return self.presenter.get_image(self.current_index())

    def current_image_roi(self):
        """
        :return: The selected region of the currently visualised image
        """
        image = self.current_image()
        left, top, right, bottom = self.current_roi
        return image[top:bottom, left:right]

    def show_histogram_of_current_image(self, new_window=False):
        """
        Event that will show a histogram of the current image (full or the selected ROI).

        :param new_window: Whether to put the new histogram into a new floating window,
                           or append to the last focused plotting window
        """
        # This can work with sv_histogram.show_transparent or sv_histogram.show
        current_index = self.current_index()
        current_filename = self.presenter.get_image_filename(current_index)
        title = self.dock.windowTitle()
        legend = self._create_label(current_filename, current_index)

        # Choose plotting function depending on whether we're creating a histogram in the same window, or a new window.
        # The last window that was focused will be considered the 'active' window.
        histogram_function = sv_histogram.show_transparent if not new_window else sv_histogram.show_floating_transparent

        if self.current_roi:
            histogram_function(self.current_image_roi(), legend=legend, title=title)
        else:
            histogram_function(self.current_image(), legend=legend, title=title)

    def _create_label(self, current_filename, current_index):
        common_label = "Index: {current_index}, {current_filename}"
        if self.current_roi:
            legend = (common_label + " {current_roi}").format(
                current_filename=current_filename, current_index=current_index, current_roi=self.current_roi)
        else:
            legend = common_label.format(current_filename=current_filename,
                                         current_index=current_index)
        return legend

    def show_current_image(self, val=None):
        """
        :param val: Unused, but required so that the function has the same signature as the expected one
        """
        self.set_image_title_to_current_filename()
        self.image.set_data(self.current_image())

    def set_image_title_to_current_filename(self):
        self.image_axis.set_title(self.presenter.get_image_filename(self.current_index()))

    def change_value_range(self, low, high):
        self.image.set_clim((low, high))

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QtWidgets.QMessageBox.critical(self, "Error", msg)


def see(data, data_traversal_axis=0, cmap='Greys_r', block=False):
    """
    This method provides an option to run an independent stack visualiser.
    It might be useful when using the MantidImaging package through IPython.

    Warning: This function will internally hide a QApplication in order to show the Stack Visualiser.
    This can be accessed with see.q_application, and if modified externally it might crash the caller process.

    :param data: Data to be visualised
    :param data_traversal_axis: axis on which we're traversing the data
    :param cmap: Color map
    :param block: Whether to block the calling process, or not
    """
    getLogger(__name__).info("Running independent Stack Visualiser")

    # We cache the QApplication reference, otherwise the interpreter will segfault when we try to create
    # a second QApplication on a consecutive call. We cache it as a parameter of this function, because we don't
    # want to expose the QApplication to the outside
    if not hasattr(see, 'q_application'):
        see.q_application = Qt.QApplication(sys.argv)

    dock = Qt.QDockWidget(None)
    s = StackVisualiserView(None, dock, data, data_traversal_axis, cmap, block)
    dock.setWidget(s)
    dock.show()
    see.q_application.exec_()
