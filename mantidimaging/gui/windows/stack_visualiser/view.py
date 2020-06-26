from typing import TYPE_CHECKING, Tuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (QAction, QDockWidget, QInputDialog, QMenu, QMessageBox, QVBoxLayout, QWidget)

from mantidimaging.core.data import Images
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.external.pyqtgraph.imageview.ImageView import ImageView
from mantidimaging.gui.dialogs.op_history_copy.view import OpHistoryCopyDialogView
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.stack_visualiser.presenter import StackVisualiserPresenter
from .metadata_dialog import MetadataDialog
from .presenter import SVNotification
from ...utility.common import operation_in_progress

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class StackVisualiserView(BaseMainWindowView):
    # Signal that signifies when the ROI is updated. Used to update previews in Filter views
    roi_updated = pyqtSignal(SensibleROI)

    image_view: ImageView
    presenter: StackVisualiserPresenter
    dock: QDockWidget
    layout: QVBoxLayout

    def __init__(self, parent: 'MainWindowView', dock: QDockWidget, images: Images):
        # enforce not showing a single image
        assert images.sample.ndim == 3, \
            "Data does NOT have 3 dimensions! Dimensions found: {0}".format(images.sample.ndim)

        # We set the main window as the parent, the effect is the same as
        # having no parent, the window will be inside the QDockWidget. If the
        # dock is set as a parent the window will be an independent floating
        # window
        super(StackVisualiserView, self).__init__(parent, None)
        self.central_widget = QWidget(self)
        self.layout = QVBoxLayout(self)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        self.parent_create_stack = self.parent().create_new_stack

        # capture the QDockWidget reference so that we can access the Qt widget
        # and change things like the title
        self.dock = dock
        # Swap out the dock close event with our own provided close event. This
        # is needed to manually delete the data reference, otherwise it is left
        # hanging in the presenter
        setattr(dock, 'closeEvent', self.closeEvent)

        self.presenter = StackVisualiserPresenter(self, images)

        self.image_view = ImageView(self)
        self.image_view.imageItem.menu = self.build_context_menu()
        self.actionCloseStack = QAction("Close window", self)
        self.actionCloseStack.triggered.connect(self.close_view)
        self.actionCloseStack.setShortcut("Ctrl+W")
        self.dock.addAction(self.actionCloseStack)
        self.image_view.setImage(self.presenter.images.sample)
        self.image_view.imageItem.setAutoDownsample(True)
        self.image_view.roi_changed_callback = self.roi_changed_callback
        self.layout.addWidget(self.image_view)

    @property
    def name(self):
        return self.dock.windowTitle()

    @name.setter
    def name(self, name: str):
        self.dock.setWindowTitle(name)

    @property
    def current_roi(self) -> Tuple[int, int, int, int]:
        roi = SensibleROI.from_points(*self.image_view.get_roi())
        return roi.left, roi.top, roi.right, roi.bottom

    @property
    def image(self):
        return self.image_view.imageItem

    @image.setter
    def image(self, to_display):
        self.image_view.setImage(to_display)

    @property
    def main_window(self):
        return self.parent().parent()

    def closeEvent(self, event):
        with operation_in_progress("Closing image view", "Freeing image memory"):
            # the image view renderer itself holds a reference to the sample data
            # make sure to clear that first, so that freeing the memory in the presenter
            self.image_view.clear()
            self.image_view.close()

            # this removes all references to the data, allowing it to be GC'ed
            # otherwise there is a hanging reference
            self.presenter.delete_data()

            # this could happen if run without a parent through see(..)
            if not isinstance(self.window(), QDockWidget):
                self.window().remove_stack(self)  # refers to MainWindow

            # setting floating to false makes window() to return the MainWindow
            # because the window will be docked in, however we delete it
            # immediately after so no visible change occurs
            self.dock.setFloating(False)

            self.deleteLater()
            # refers to the QDockWidget within which the stack is contained
            self.dock.deleteLater()

    def roi_changed_callback(self, roi: SensibleROI):
        self.roi_updated.emit(roi)

    def close_view(self):
        self.close()

    def build_context_menu(self) -> QMenu:
        actions = [
            ("Set ROI", self.set_roi),
            ("Copy ROI to clipboard", self.copy_roi_to_clipboard),
            ("Change window name", self.change_window_name_clicked),
            ("Toggle show averaged image", lambda: self.presenter.notify(SVNotification.TOGGLE_IMAGE_MODE)),
            ("Show history", self.show_image_metadata),
            ("Create sinograms from stack", lambda: self.presenter.notify(SVNotification.SWAP_AXES)),
            ("Apply history from another stack", self.show_op_history_copy_dialog),
        ]

        menu = QMenu(self)

        for (menu_text, func) in actions:
            action = QAction(menu_text, menu)
            action.triggered.connect(func)
            menu.addAction(action)

        return menu

    def set_roi(self):
        roi, accepted = QInputDialog.getText(self, "Manual ROI",
                                             "Enter ROI in order left, top, right, bottom, with commas in-between each number",
                                             text="0, 0, 50, 50")
        if accepted:
            roi = [int(r.strip()) for r in roi.split(",")]
            self.image_view.roi.setSize((roi[2], roi[3]))
            self.image_view.roi.setPos((roi[0], roi[1]))
            self.image_view.roiChanged()

    def copy_roi_to_clipboard(self):
        pos, size = self.image_view.get_roi()
        QGuiApplication.clipboard().setText(f"{pos.x}, {pos.y}, {size.x}, {size.y}")

    def change_window_name_clicked(self):
        input_window = QInputDialog()
        new_window_name, ok = input_window.getText(self, "Change window name", "Name:", text=self.name)
        if ok:
            if new_window_name not in self.main_window.stack_names:
                self.main_window.presenter.rename_stack_by_name(self.name, new_window_name)
            else:
                error = QMessageBox(self)
                error.setWindowTitle("Stack name conflict")
                error.setText(f"There is already a window named {new_window_name}")
                error.exec()

    def show_image_metadata(self):
        dialog = MetadataDialog(self, self.presenter.images)
        dialog.show()

    def show_op_history_copy_dialog(self):
        dialog = OpHistoryCopyDialogView(self, self.presenter.images, self.main_window)
        dialog.show()
