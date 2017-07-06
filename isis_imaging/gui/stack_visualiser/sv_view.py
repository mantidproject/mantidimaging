from __future__ import absolute_import, division, print_function

from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from matplotlib.figure import Figure
from matplotlib import pyplot
from matplotlib.widgets import RectangleSelector, Slider
from PyQt5 import Qt, QtCore

from isis_imaging.core.algorithms import gui_compile_ui
from isis_imaging.gui.stack_visualiser.sv_presenter import StackViewerPresenter
from isis_imaging.gui.stack_visualiser.sv_presenter import Notification as StackWindowNotification
from isis_imaging.gui.stack_visualiser import sv_histogram


class StackVisualiserView(Qt.QMainWindow):
    def __init__(self,
                 parent,
                 dock,
                 data,
                 axis=0,
                 cmap='Greys_r',
                 block=False,
                 **kwargs):

        # enforce not showing a single image
        assert data.ndim == 3, "Data does NOT have 3 dimensions! Dimensions found: {0}".format(
            data.ndim)

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
        self.presenter = StackViewerPresenter(self, data, axis)

        self.mplfig = Figure()
        self.image_axis = self.mplfig.add_subplot(111)

        self.canvas = FigureCanvasQTAgg(self.mplfig)
        self.canvas.rectanglecolor = QtCore.Qt.yellow
        self.canvas.setParent(self)
        self.previous_region = (100, 100, 200, 200)

        self.toolbar = NavigationToolbar2QT(
            self.canvas, self, coordinates=True)

        self.slider_axis = self.mplfig.add_axes(
            [0.25, 0.01, 0.5, 0.03], facecolor='lightgoldenrodyellow')

        # initialise the slider
        self.slider = self.create_slider(self.slider_axis,
                                         data.shape[axis] - 1)
        self.image = self.image_axis.imshow(
            self.presenter.get_image(0), cmap=cmap, **kwargs)

        self.rectangle_selector = self.create_rectangle_selector(self.image_axis, 1)

        self.mplvl.addWidget(self.toolbar)
        self.mplvl.addWidget(self.canvas)

        self.setup_shortcuts()


    def update_title_event(self):
        text, okPressed = Qt.QInputDialog.getText(self, "Rename window", "Enter new name", Qt.QLineEdit.Normal, "")

        if okPressed:
            self.dock.setWindowTitle(text)

    def setup_shortcuts(self):
        self.histogram_shortcut = Qt.QShortcut(Qt.QKeySequence("Shift+C"), self.dock)
        self.histogram_shortcut.activated.connect(lambda: self.presenter.notify(StackWindowNotification.HISTOGRAM))

        self.rename_shortcut = Qt.QShortcut(Qt.QKeySequence("F2"), self.dock)
        self.rename_shortcut.activated.connect(
            lambda: self.presenter.notify(StackWindowNotification.RENAME_WINDOW))

        # self.remove_roi_shortcut = Qt.QMouseEvent(Qt.QEvent.MouseButtonPress, self.mapToGlobal(QtCore.QPoint(0,0)), QtCore.Qt.RightButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
        # self.remove_roi_shortcut.activated.connect(self.mouse_button_pressed)
        # self.mousePressEvent(self.remove_roi_shortcut)
        # doesn't work, the pressing the key doesn't seem to call the function
        # self.canvas.mpl_connect('key_press_event', self.toggle_selector)

    def remove_roi_on_right_click(self, event):
        print("In removing roi")
        if event.button() == QtCore.Qt.RightButton:
            self.rectangle_selector_visible(False)
        else:
            self.rectangle_selector_visible(True)

    def rectangle_selector_visible(self, visible):
        self.rectangle_selector.set_active(visible)

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
        self.parent().deleteLater() # refers to the QDockWidget within which the stack is contained

    def create_rectangle_selector(self, axis, button=1):
        # drawtype is 'box' or 'line' or 'none', we could use 'line' to show COR, but the line
        # doesn't want to flip horizontally so it only ends up leaning right
        return RectangleSelector(
            axis,
            self.region_select_callback,
            drawtype='box',
            useblit=True,
            button=[1, 3],  # don't use middle button
            spancoords='pixels',
            minspanx=3,
            minspany=3,
            interactive=True)

    def create_slider(self, slider_axis, length):
        slider = Slider(
            slider_axis, 'Slices', 0, length, valinit=0, valfmt='%i')

        slider.on_changed(self.show_current_image)
        return slider

    def toggle_selector(self, event):
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and self.rectangle_selector.active:
            print(' RectangleSelector deactivated.')
            self.rectangle_selector.set_active(False)
        if event.key in ['A', 'a'] and not self.rectangle_selector.active:
            print(' RectangleSelector activated.')
            self.rectangle_selector.set_active(True)


    def region_select_callback(self, eclick, erelease):
        print(eclick)
        print(erelease)
        # eclick and erelease are the press and release events
        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata
        # different order here, than in how we handle it
        # this is because the unpacking for draw_rect is different
        self.previous_region = (x0, x1, y0, y1)
        region = "%i %i %i %i" % (x0, y0, x1, y1)
        print(region)

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

    def show_histogram_of_current_image(self):
        current_image = self.current_image()
        # import random
        # if random.random() <= 0.5:
        #     sv_histogram.show(current_image)
        # else:
        sv_histogram.show_transparent(current_image)

    def show_current_image(self, val=None):
        """
        :param val: Unused, but required so that the function has the same signature as the expected one
        """
        self.image.set_data(self.current_image())
        self.rectangle_selector.

    def change_value_range(self, low, high):
        self.image.set_clim((low, high))



# def show_3d(data, axis=0, cmap='Greys_r', block=False, **kwargs):
#     s = StackVisualiserView(data, axis, cmap, block)
