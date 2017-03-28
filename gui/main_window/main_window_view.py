from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QMainWindow


class ImgpyMainWindowView(QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        uic.loadUi('./gui/ui/main_window.ui', self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        from gui.main_window.main_window_presenter import ImgpyMainWindowPresenter
        self.presenter = ImgpyMainWindowPresenter(self, config)

        # load some sample data, currently provided from the GUI
        from core.imgdata import loader
        stack = loader.load_data(config)[0]

        from gui.stack_visualiser.stack_visualiser_view import ImgpyStackVisualiserView
        self.stackvis = ImgpyStackVisualiserView(self, stack)
        self.stackvis.setVisible(True)
