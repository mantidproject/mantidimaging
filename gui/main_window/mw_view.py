from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QMainWindow
from gui.mw.mw_presenter import ImgpyMainWindowPresenter
from gui.stack_visualiser.stack_visualiser_view import ImgpyStackVisualiserView


class ImgpyMainWindowView(QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        uic.loadUi('./gui/ui/mw.ui', self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        self.presenter = ImgpyMainWindowPresenter(self, config)

        # load some sample data, currently provided from the GUI
        from core.imgdata import loader
        stack = loader.load_data(config)[0]

        self.stackvis = ImgpyStackVisualiserView(self, stack)
        self.stackvis.setVisible(True)

    def median_filter_clicked(self):
        self.presenter.notify(
            ImgpyMainWindowPresenter.Notification.MEDIAN_FILTER_CLICKED)
