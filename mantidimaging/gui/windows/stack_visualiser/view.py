import sys
from logging import getLogger
from typing import Tuple

from PyQt5 import Qt
from PyQt5.QtWidgets import QVBoxLayout

from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.external.pyqtgraph.imageview.ImageView import ImageView
from mantidimaging.gui.mvp_base import BaseMainWindowView
from .presenter import StackVisualiserPresenter


class StackVisualiserView(BaseMainWindowView):
    image_updated = Qt.pyqtSignal()
    roi_updated = Qt.pyqtSignal('PyQt_PyObject')
    image_selected = Qt.pyqtSignal(int)

    layout: QVBoxLayout

    def __init__(self, parent, dock, images, data_traversal_axis=0,
                 cmap='Greys_r', block=False):
        # enforce not showing a single image
        assert images.sample.ndim == 3, \
            "Data does NOT have 3 dimensions! Dimensions found: \
            {0}".format(images.sample.ndim)

        # We set the main window as the parent, the effect is the same as
        # having no parent, the window will be inside the QDockWidget. If the
        # dock is set as a parent the window will be an independent floating
        # window
        super(StackVisualiserView, self).__init__(parent, 'gui/ui/stack.ui')

        # capture the QDockWidget reference so that we can access the Qt widget
        # and change things like the title
        self.dock = dock
        # Swap out the dock close event with our own provided close event. This
        # is needed to manually delete the data reference, otherwise it is left
        # hanging in the presenter
        dock.closeEvent = self.closeEvent

        self.presenter = StackVisualiserPresenter(self, images, data_traversal_axis)

        self.image = ImageView(self)
        self.image.setImage(self.presenter.images.sample)
        self.layout.addWidget(self.image)

        def presenter_set_image_index(i):
            self.presenter.current_image_index = i

        self.image_selected.connect(presenter_set_image_index)

    @property
    def name(self):
        return self.dock.windowTitle()

    @property
    def current_roi(self) -> Tuple[int, int, int, int]:
        roi = SensibleROI.from_points(*self.image.get_roi())
        return roi.left, roi.top, roi.right, roi.bottom

    def show_current_image(self):
        self.image.setImage(self.presenter.images.sample)

    # def update_title_event(self):
    #     text, okPressed = Qt.QInputDialog.getText(
    #         self, "Rename window", "Enter new name", Qt.QLineEdit.Normal, "")
    #
    #     if okPressed:
    #         self.dock.setWindowTitle(text)
    #
    # def setup_shortcuts(self):
    #     self.histogram_shortcut = Qt.QShortcut(
    #         Qt.QKeySequence("Shift+C"), self.dock)
    #     self.histogram_shortcut.activated.connect(
    #         lambda: self.presenter.notify(StackWindowNotification.HISTOGRAM))
    #
    #     self.new_window_histogram_shortcut = Qt.QShortcut(
    #         Qt.QKeySequence("Ctrl+Shift+C"), self.dock)
    #     self.new_window_histogram_shortcut.activated.connect(
    #         lambda: self.presenter.notify(
    #             StackWindowNotification.NEW_WINDOW_HISTOGRAM))
    #
    #     self.rename_shortcut = Qt.QShortcut(Qt.QKeySequence("F2"), self.dock)
    #     self.rename_shortcut.activated.connect(
    #         lambda: self.presenter.notify(
    #             StackWindowNotification.RENAME_WINDOW))

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

    # def set_image_title_to_current_filename(self):
    #     self.image_axis.set_title(
    #         self.presenter.get_image_filename(
    #             self.presenter.current_image_index))


def see(data, data_traversal_axis=0, cmap='Greys_r', block=False):
    """
    This method provides an option to run an independent stack visualiser.
    It might be useful when using the MantidImaging package through IPython.

    Warning: This function will internally hide a QApplication in order to show
    the Stack Visualiser.  This can be accessed with see.q_application, and if
    modified externally it might crash the caller process.

    :param data: Data to be visualised
    :param data_traversal_axis: axis on which we're traversing the data
    :param cmap: Color map
    :param block: Whether to block the calling process, or not
    """
    getLogger(__name__).info("Running independent Stack Visualiser")

    # We cache the QApplication reference, otherwise the interpreter will
    # segfault when we try to create a second QApplication on a consecutive
    # call. We cache it as a parameter of this function, because we don't want
    # to expose the QApplication to the outside
    if not hasattr(see, 'q_application'):
        see.q_application = Qt.QApplication(sys.argv)

    dock = Qt.QDockWidget(None)
    s = StackVisualiserView(None, dock, data, data_traversal_axis, cmap, block)
    dock.setWidget(s)
    dock.show()
    see.q_application.exec_()
