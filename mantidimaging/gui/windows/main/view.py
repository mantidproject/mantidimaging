from logging import getLogger
from typing import Optional

import matplotlib
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QLabel

from mantidimaging.core.data import Images
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.cor_tilt import CORTiltWindowView
from mantidimaging.gui.windows.filters import FiltersWindowView
from mantidimaging.gui.windows.main.load_dialog import MWLoadDialog
from mantidimaging.gui.windows.main.presenter import MainWindowPresenter
from mantidimaging.gui.windows.main.presenter import Notification as PresNotification
from mantidimaging.gui.windows.main.save_dialog import MWSaveDialog
from mantidimaging.gui.windows.savu_filters.preparation import BackgroundService
from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowView
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.gui.windows.tomopy_recon import TomopyReconWindowView

LOG = getLogger(__file__)


class MainWindowView(BaseMainWindowView):
    active_stacks_changed = Qt.pyqtSignal()
    backend_message = Qt.pyqtSignal(bytes)

    actionCorTilt: QAction
    actionFilters: QAction
    actionSavuFilters: QAction
    actionTomopyRecon: QAction

    load_dialogue: MWLoadDialog
    save_dialogue: MWSaveDialog

    def __init__(self):
        super(MainWindowView, self).__init__(None, "gui/ui/main_window.ui")

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Mantid Imaging")

        self.presenter = MainWindowPresenter(self)

        self.filters: Optional[FiltersWindowView] = None
        self.savu_filters: Optional[SavuFiltersWindowView] = None
        self.cor_tilt: Optional[CORTiltWindowView] = None
        self.tomopy_recon: Optional[TomopyReconWindowView] = None
        self.save_dialogue: Optional[MWSaveDialog] = None
        self.load_dialogue: Optional[MWLoadDialog] = None

        status_bar = self.statusBar()
        self.status_bar_label = QLabel("", self)
        status_bar.addPermanentWidget(self.status_bar_label)

        self.setup_shortcuts()
        self.update_shortcuts()

    def setup_shortcuts(self):
        self.actionLoad.triggered.connect(self.show_load_dialogue)
        self.actionSave.triggered.connect(self.show_save_dialogue)
        self.actionExit.triggered.connect(self.close)

        self.actionOnlineDocumentation.triggered.connect(self.open_online_documentation)
        self.actionAbout.triggered.connect(self.show_about)

        self.actionFilters.triggered.connect(self.show_filters_window)
        self.actionFilters.setShortcut("Ctrl+F")
        self.actionSavuFilters.triggered.connect(self.show_savu_filters_window)
        self.actionSavuFilters.setShortcut("Ctrl+Shift+F")
        self.actionCorTilt.triggered.connect(self.show_cor_tilt_window)
        self.actionCorTilt.setShortcut("Ctrl+R")
        self.actionTomopyRecon.triggered.connect(self.show_tomopy_recon_window)
        self.actionTomopyRecon.setShortcut("Ctrl+Shift+R")

        self.active_stacks_changed.connect(self.update_shortcuts)

    def update_shortcuts(self):
        self.actionSave.setEnabled(len(self.presenter.stack_names) > 0)

    @staticmethod
    def open_online_documentation():
        url = QtCore.QUrl("https://mantidproject.github.io/mantidimaging/")
        QtGui.QDesktopServices.openUrl(url)

    def show_about(self):
        from mantidimaging import __version__ as version_no

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("About MantidImaging")
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(
            '<a href="https://github.com/mantidproject/mantidimaging">MantidImaging</a>'
            '<br>Version: <a href="https://github.com/mantidproject/mantidimaging/releases/tag/{0}">{0}</a>'.format(
                version_no))
        msg_box.show()

    def show_load_dialogue(self):
        self.load_dialogue = MWLoadDialog(self)
        self.load_dialogue.show()

    def execute_save(self):
        self.presenter.notify(PresNotification.SAVE)

    def execute_load(self):
        self.presenter.notify(PresNotification.LOAD)

    def show_save_dialogue(self):
        self.save_dialogue = MWSaveDialog(self, self.stack_list)
        self.save_dialogue.show()

    def show_cor_tilt_window(self):
        if not self.cor_tilt:
            self.cor_tilt = CORTiltWindowView(self)
            self.cor_tilt.show()
        else:
            self.cor_tilt.activateWindow()
            self.cor_tilt.raise_()

    def show_filters_window(self):
        if not self.filters:
            self.filters = FiltersWindowView(self)
            self.filters.show()
        else:
            self.filters.activateWindow()
            self.filters.raise_()

    def show_savu_filters_window(self):
        if not self.savu_filters:
            try:
                self.savu_filters = SavuFiltersWindowView(self)
                self.savu_filters.show()
            except RuntimeError as e:
                QtWidgets.QMessageBox.warning(self, "Savu Backend not available", str(e))
        else:
            self.savu_filters.activateWindow()
            self.savu_filters.raise_()

    def show_tomopy_recon_window(self):
        if not self.tomopy_recon:
            self.tomopy_recon = TomopyReconWindowView(self)
            self.tomopy_recon.show()
        else:
            self.tomopy_recon.activateWindow()
            self.tomopy_recon.raise_()

    @property
    def stack_list(self):
        return self.presenter.stack_list

    @property
    def stack_names(self):
        return self.presenter.stack_names

    def get_stack_visualiser(self, stack_uuid):
        return self.presenter.get_stack_visualiser(stack_uuid)

    def get_stack_history(self, stack_uuid):
        return self.presenter.get_stack_history(stack_uuid)

    def create_stack_window(self,
                            stack: Images,
                            title: str,
                            position=QtCore.Qt.TopDockWidgetArea,
                            floating=False) -> Qt.QDockWidget:
        dock_widget = Qt.QDockWidget(title, self)

        # this puts the new stack window into the centre of the window
        self.setCentralWidget(dock_widget)

        # add the dock widget into the main window
        self.addDockWidget(position, dock_widget)

        # we can get the stack visualiser widget with dock_widget.widget
        dock_widget.setWidget(StackVisualiserView(self, dock_widget, stack))

        # proof of concept above
        assert isinstance(dock_widget.widget(),
                          StackVisualiserView), "Widget inside dock_widget is not an StackVisualiserView!"

        dock_widget.setFloating(floating)

        return dock_widget

    def remove_stack(self, obj: StackVisualiserView):
        getLogger(__name__).debug("Removing stack with uuid %s", obj.uuid)
        self.presenter.remove_stack(obj.uuid)

    def closeEvent(self, event):
        """
        Handles a request to quit the application from the user.
        """
        should_close = True

        if self.presenter.have_active_stacks:
            # Show confirmation box asking if the user really wants to quit if
            # they have data loaded
            msg_box = QtWidgets.QMessageBox.question(self,
                                                     "Quit",
                                                     "Are you sure you want to quit?",
                                                     defaultButton=QtWidgets.QMessageBox.No)
            should_close = msg_box == QtWidgets.QMessageBox.Yes

        if should_close:
            # Close all matplotlib PyPlot windows when exiting.
            getLogger(__name__).debug("Closing all PyPlot windows")
            matplotlib.pyplot.close("all")
            self.backend_process.close()
            self.backend_process.join()

            # Pass close event to parent
            super(MainWindowView, self).closeEvent(event)

        else:
            # Ignore the close event, keeping window open
            event.ignore()

    def uncaught_exception(self, user_error_msg, log_error_msg):
        QtWidgets.QMessageBox.critical(self, "Uncaught exception", f"{user_error_msg}: ")
        getLogger(__name__).error(log_error_msg)

    def print_backend_output(self, output: bytes):
        getLogger(__name__).debug(output)

    def error_callback(self, err_code, output):
        self.status_bar_label.setText("SAVU Backend: Error")
        getLogger(__name__).error("".join([out.decode("utf-8") for out in output]))

    def set_background_service(self, process: BackgroundService):
        if process.process and process.process.poll() is not None:
            self.status_bar_label.setText("SAVU Backend: Starting")
        self.backend_message.connect(self.print_backend_output)
        self.backend_process = process
        process.callback = lambda output: self.backend_message.emit(output)
        process.success_callback = lambda: self.status_bar_label.setText("SAVU Backend: OK")
        process.error_callback = self.error_callback

    def create_new_stack(self, data, title):
        self.presenter.create_new_stack(data, title)
