from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtCore

from isis_imaging.core.algorithms import gui_compile_ui
from isis_imaging.gui.main_window.load_dialog import MWLoadDialog
from isis_imaging.gui.main_window.mw_presenter import \
    Notification as PresNotification
from isis_imaging.gui.main_window.mw_presenter import MainWindowPresenter
from isis_imaging.gui.main_window.save_dialog import MWSaveDialog
from isis_imaging.gui.stack_visualiser.sv_view import StackVisualiserView


class MainWindowView(Qt.QMainWindow):
    def __init__(self, config):
        super(MainWindowView, self).__init__()
        gui_compile_ui.execute('gui/ui/main_window.ui', self)

        # connection of file menu TODO move to func
        self.setup_shortcuts()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("ISIS Imaging")

        # filter and algorithm communications will be funneled through this
        self.presenter = MainWindowPresenter(self, config)

    def setup_shortcuts(self):
        self.actionLoad.setShortcut('F1')
        self.actionLoad.triggered.connect(self.show_load_dialogue)

        self.actionSave.setShortcut('Ctrl+S')
        self.actionSave.triggered.connect(self.show_save_dialogue)

        self.actionExit.setShortcut('Ctrl+Q')
        self.actionExit.triggered.connect(Qt.qApp.quit)

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

    def stack_names(self):
        # unpacks the tuple and only gives the correctly sorted human readable names
        return zip(*self.presenter.stack_list())[1]

    def stack_list(self):
        return self.presenter.stack_list()

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
        print("Removing stack with uuid", obj.uuid)
        self.presenter.remove_stack(obj.uuid)

    def algorithm_accepted(self, stack_uuid, func):
        self.presenter.do_badly(stack_uuid, func)
