from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtCore
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector, Slider

from isis_imaging.core.algorithms import gui_compile_ui
from isis_imaging.core.io import Images
from isis_imaging.gui.stack_visualiser import sv_histogram
from isis_imaging.gui.stack_visualiser.sv_presenter import Notification as StackWindowNotification
from isis_imaging.gui.stack_visualiser.sv_presenter import StackViewerPresenter


class StackVisualiserView(Qt.QMainWindow):
    def __init__(self, parent, dock, images: Images, axis=0, cmap='Greys_r', block=False, **kwargs):
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
        self.presenter = StackViewerPresenter(self, images, axis)

        self.figure = Figure()

        self.initialise_canvas()
        self.current_roi = None

        self.toolbar = NavigationToolbar2QT(self.canvas, self, coordinates=True)

        self.initialise_slider(axis, images)
        self.initialise_image(cmap, kwargs)

        self.rectangle_selector = self.create_rectangle_selector(self.image_axis, 1)

        self.mplvl.addWidget(self.toolbar)
        self.mplvl.addWidget(self.canvas)

        self.setup_shortcuts()

    def initialise_image(self, cmap, kwargs):
        """
        Initialises the image axis and the image object
        :param cmap: The color map which is to be used
        :param kwargs: Any additional kwargs are forwarded to imshow
        """
        self.image_axis = self.figure.add_subplot(111)
        self.image = self.image_axis.imshow(self.presenter.get_image(0), cmap=cmap, **kwargs)
        self.set_image_title_to_current_filename()

    def initialise_canvas(self):
        """
        Creates the canvas object from the figure
        """
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.rectanglecolor = QtCore.Qt.yellow
        self.canvas.setParent(self)
        self.canvas.mpl_connect('button_press_event', self.remove_any_selected_roi)

    def initialise_slider(self, axis, images):
        """
        Creates the axis for the slider and initialises the slider
        :param axis:
        :param images:
        :return:
        """
        self.slider_axis = self.figure.add_axes(
            [0.25, 0.01, 0.5, 0.03], facecolor='lightgoldenrodyellow')
        self.slider = self.create_slider(self.slider_axis, images.get_sample().shape[axis] - 1)

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
        print(region)

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

    def apply_to_data(self, func, *args, **kwargs):
        # TODO maybe we should separate out actions on data / GUI stuff
        self.presenter.apply_to_data(func, *args, **kwargs)

    def closeEvent(self, event):
        # this removes all references to the data, allowing it to be GC'ed
        # otherwise there is a hanging reference
        self.presenter.delete_data()

        # setting floating to false makes window() to return the MainWindow
        # because the window will be docked in, however we delete it
        # immediately after so no visible change occurs
        self.parent().setFloating(False)
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
            button=[1, 3],  # don't use middle button
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
        TODO plot the histogram of only the current image ROI, however there doesnt seem to be a way of getting the
        state of the rectangle selector, so we can't know if the user has actually selected a ROI or not. Need to find
        a workaround around this or a better rectangle selector

        :return: The selected region of the currently visualised image
        """
        image = self.current_image()
        left, top, right, bottom = self.current_roi
        return image[top:bottom, left:right]

    def show_histogram_of_current_image(self, new_window=False):
        # This can work with sv_histogram.show_transparent or sv_histogram.show
        current_index = self.current_index()
        current_filename = self.presenter.get_image_filename(current_index)
        title = self.dock.windowTitle()
        common_label = "Index: {current_index}, {current_filename}"
        legend = self._create_label(common_label, current_filename, current_index)
        histogram_function = sv_histogram.show_transparent if not new_window else sv_histogram.show_floating_transparent
        histogram_function(self.current_image(), legend=legend, title=title)

    def _create_label(self, common_label, current_filename, current_index):
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

# def show_3d(data, axis=0, cmap='Greys_r', block=False, **kwargs):
#     s = StackVisualiserView(data, axis, cmap, block)
