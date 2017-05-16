from __future__ import absolute_import, division, print_function

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt as Qt_

from core.algorithms import gui_compile_ui
from gui.main_window.mw_presenter import ImgpyMainWindowPresenter
from gui.main_window.mw_presenter import Notification as PresNotification
from gui.stack_visualiser.sv_view import ImgpyStackVisualiserView
from gui.main_window.load_dialog.load_dialog import MWLoadDialog
from gui.main_window.save_dialog.save_dialog import MWSaveDialog


class ImgpyMainWindowView(QtGui.QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        gui_compile_ui.execute('gui/ui/main_window.ui', self)

        # connection of file menu TODO move to func
        self.actionLoad.setShortcut('F2')
        self.actionLoad.triggered.connect(self.show_load_dialogue)

        self.actionSave.setShortcut('Ctrl+S')
        self.actionSave.triggered.connect(self.show_save_dialogue)
        # setting of shortcuts TODO move to func
        self.actionExit.triggered.connect(QtGui.qApp.quit)
        self.actionExit.setShortcut('Ctrl+Q')

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        # filter and algorithm communications will be funneled through this
        self.presenter = ImgpyMainWindowPresenter(self, config)

    def show_load_dialogue(self):
        self.load_dialogue = MWLoadDialog(self)
        self.load_dialogue.show()

    def execute_save(self):
        self.presenter.notify(PresNotification.SAVE)

    def execute_load(self):
        self.presenter.notify(PresNotification.LOAD)

    def show_save_dialogue(self):
        self.save_dialogue = MWSaveDialog(self, self.presenter.stack_list())
        self.save_dialogue.show()

    def create_stack_window(self,
                            stack,
                            title,
                            position=Qt_.BottomDockWidgetArea,
                            floating=False):
        dock_widget = QtGui.QDockWidget(title, self)

        self.addDockWidget(position, dock_widget)

        # we can get the stack visualiser widget with dock_widget.widget
        dock_widget.setWidget(
            ImgpyStackVisualiserView(self, dock_widget, stack))

        # proof of concept above
        assert isinstance(
            dock_widget.widget(), ImgpyStackVisualiserView
        ), "Widget inside dock_widget is not an ImgpyStackVisualiserView!"

        dock_widget.setFloating(floating)

        return dock_widget

    def remove_stack(self, obj):
        print("Removing stack with uuid", obj.uuid)
        self.presenter.remove_stack(obj.uuid)
        obj.deleteLater()
