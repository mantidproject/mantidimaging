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

        # filter and algorithm communications will be funneled through this
        self.presenter = ImgpyMainWindowPresenter(self, config)

    def show_load_dialogue(self):
        self.load_dialogue = MWLoadDialog(self)

        # actually show the dialogue
        self.load_dialogue.show()

    def executeLoadStack(self):
        # TODO THIS DOES TOO MUCH, VIEW IS NOT SUPPOSED TO

        # then presenter will load it and set it in the model
        sample_path = str(self.load_dialogue.sample_path())
        if not sample_path:
            return

        # dirname removes the file name from the path
        stack = loader.load(os.path.dirname(sample_path))
        self.add_stack_dock(stack)
        self.presenter.notify(
            ImgpyMainWindowPresenter.Notification.STACK_LOADED)

    def add_stack_dock(self,
                       stack,
                       title,
                       position=Qt_.BottomDockWidgetArea,
                       floating=False):
        self.dock_widget = QtGui.QDockWidget(title, self)
        self.addDockWidget(position, self.dock_widget)
        self.stackvis = ImgpyStackVisualiserView(self, stack)
        self.dock_widget.setWidget(self.stackvis)
        self.dock_widget.setFloating(floating)

    def median_filter_clicked(self):
        self.presenter.notify(
            ImgpyMainWindowPresenter.Notification.MEDIAN_FILTER_CLICKED)
