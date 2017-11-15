from __future__ import absolute_import, division, print_function

import matplotlib

from logging import getLogger
from PyQt5 import Qt, QtCore, QtGui

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.dialogs.cor_tilt import CORTiltDialogView
from mantidimaging.gui.dialogs.filters import FiltersDialogView
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

from .load_dialog import MWLoadDialog
from .presenter import MainWindowPresenter
from .presenter import Notification as PresNotification
from .save_dialog import MWSaveDialog


class MainWindowView(BaseMainWindowView):

    active_stacks_changed = Qt.pyqtSignal()

    def __init__(self, config):
        super(MainWindowView, self).__init__(None, 'gui/ui/main_window.ui')

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("MantidImaging")

        # filter and algorithm communications will be funneled through this
        self.presenter = MainWindowPresenter(self, config)

        self.filters_window = FiltersDialogView(self)
        self.cor_tilt_window = CORTiltDialogView(self)

        self.setup_shortcuts()
        self.update_shortcuts()

    def setup_shortcuts(self):
        self.actionLoad.triggered.connect(self.show_load_dialogue)
        self.actionSave.triggered.connect(self.show_save_dialogue)
        self.actionExit.triggered.connect(Qt.qApp.quit)

        self.actionOnlineDocumentation.triggered.connect(
                self.open_online_documentation)

        self.actionCorTilt.triggered.connect(self.show_cor_tilt_window)
        self.actionFilters.triggered.connect(self.show_filters_window)

        self.active_stacks_changed.connect(self.update_shortcuts)

    def update_shortcuts(self):
        self.actionSave.setEnabled(len(self.presenter.stack_names()) > 0)

    def open_online_documentation(self):
        url = QtCore.QUrl('https://mantidproject.github.io/mantidimaging/')
        QtGui.QDesktopServices.openUrl(url)

    def show_load_dialogue(self):
        self.load_dialogue = MWLoadDialog(self)
        self.load_dialogue.show()

    def execute_save(self):
        self.presenter.notify(PresNotification.SAVE)

    def execute_load(self):
        self.presenter.notify(PresNotification.LOAD)

    def show_save_dialogue(self):
        self.save_dialogue = MWSaveDialog(self, self.stack_list())
        self.save_dialogue.show()

    def show_cor_tilt_window(self):
        self.cor_tilt_window.show()

    def show_filters_window(self):
        self.filters_window.show()

    def stack_list(self):
        return self.presenter.stack_list()

    def stack_names(self):
        return self.presenter.stack_names()

    def stack_uuids(self):
        return self.presenter.stack_uuids()

    def get_stack_visualiser(self, stack_uuid):
        return self.presenter.get_stack_visualiser(stack_uuid)

    def create_stack_window(self,
                            stack,
                            title,
                            position=QtCore.Qt.TopDockWidgetArea,
                            floating=False):
        dock_widget = Qt.QDockWidget(title, self)

        # this puts the new stack window into the centre of the window
        self.setCentralWidget(dock_widget)

        # add the dock widget into the main window
        self.addDockWidget(position, dock_widget)

        # we can get the stack visualiser widget with dock_widget.widget
        dock_widget.setWidget(
            StackVisualiserView(self, dock_widget, stack))

        # proof of concept above
        assert isinstance(
            dock_widget.widget(), StackVisualiserView
        ), "Widget inside dock_widget is not an StackVisualiserView!"

        dock_widget.setFloating(floating)

        return dock_widget

    def remove_stack(self, obj):
        getLogger(__name__).debug("Removing stack with uuid %s", obj.uuid)
        self.presenter.remove_stack(obj.uuid)

    def algorithm_accepted(self, stack_uuid, algorithm_dialog):
        """
        We forward the data onwards to the presenter and then the model, so
        that we can have a passive view.

        :param stack_uuid: The unique ID of the stack

        :param algorithm_dialog: The algorithm dialog object
        """
        self.presenter.apply_to_data(stack_uuid, algorithm_dialog)

    def closeEvent(self, event):
        """
        Close all matplotlib PyPlot windows when exiting.

        :param event: Unused
        """
        getLogger(__name__).debug("Closing all PyPlot windows")
        matplotlib.pyplot.close("all")
