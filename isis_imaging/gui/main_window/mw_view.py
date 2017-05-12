from __future__ import absolute_import, division, print_function

import os

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt as Qt_

from core.algorithms import gui_compile_ui
from core.imgdata import loader
from gui.main_window.mw_presenter import ImgpyMainWindowPresenter
from gui.stack_visualiser.sv_view import ImgpyStackVisualiserView
from gui.main_window.load_dialog.load_dialog import MWLoadDialog


class ImgpyMainWindowView(QtGui.QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        gui_compile_ui.execute('gui/ui/main_window.ui', self)

        # connection of file menu TODO move to func
        self.actionLoad.triggered.connect(self.show_load_dialogue)
        self.actionExit.triggered.connect(QtGui.qApp.quit)

        # setting of shortcuts TODO move to func
        self.actionLoad.setShortcut('F2')
        self.actionExit.setShortcut('Ctrl+Q')

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        # filter and algorithm communications will be filtered through this
        self.presenter = ImgpyMainWindowPresenter(self, config)

    def show_load_dialogue(self):
        self.load_dialogue = MWLoadDialog(self)

        # actually show the dialogue
        self.load_dialogue.show()

    def load_stack(self):
        # TODO actually notify presenter that it was loaded
        # then presenter will load it and set it in the model
        load_path = str(self.load_dialogue.load_path())
        if not load_path:
            return

        # dirname removes the file name from the path
        stack = loader.load(os.path.dirname(load_path))
        self.add_stack_dock(stack)

    def add_stack_dock(self,
                       stack,
                       position=Qt_.BottomDockWidgetArea,
                       floating=False):
        self.dock_widget = QtGui.QDockWidget("", self)
        self.addDockWidget(position, self.dock_widget)
        self.stackvis = ImgpyStackVisualiserView(self, stack)
        self.dock_widget.setWidget(self.stackvis)
        self.dock_widget.setFloating(floating)

    def set_value(self, value=5):
        pass

    def median_filter_clicked(self):
        self.presenter.notify(
            ImgpyMainWindowPresenter.Notification.MEDIAN_FILTER_CLICKED)
