from __future__ import absolute_import, division, print_function

import os

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt as Qt_

from core.imgdata import loader
from gui.main_window.mw_presenter import ImgpyMainWindowPresenter
from gui.stack_visualiser.sv_view import ImgpyStackVisualiserView


class ImgpyMainWindowView(QtGui.QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        uic.loadUi('./isis_imaging/gui/ui/main_window.ui', self)

        # easy connection of file menu
        self.actionLoad.triggered.connect(self.show_load_dialogue)
        self.actionExit.triggered.connect(QtGui.qApp.quit)
        # easy setting of shortcuts
        self.actionLoad.setShortcut('F2')
        self.actionExit.setShortcut('Ctrl+Q')

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        # filter and algorithm communications will be filtered through this
        self.presenter = ImgpyMainWindowPresenter(self, config)

    def show_load_dialogue(self):
        self.load_dialogue = uic.loadUi('./isis_imaging/gui/ui/load.ui')

        # open file path dialogue
        self.load_dialogue.sample.clicked.connect(self.select_file)

        # if accepted load the stack
        self.load_dialogue.accepted.connect(self.load_stack)

        # actually show the dialogue
        self.load_dialogue.show()

    def select_file(self):
        # simply open file dialogue
        self.load_dialogue.samplePath.setText(
            QtGui.QFileDialog.getOpenFileName())

    def load_stack(self):
        load_path = str(self.load_dialogue.samplePath.text())
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
