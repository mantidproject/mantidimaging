from __future__ import absolute_import, division, print_function

from PyQt4 import QtCore, uic
from PyQt4.QtGui import QMainWindow

from gui.main_window.mw_presenter import ImgpyMainWindowPresenter
from gui.stack_visualiser.sv_view import ImgpyStackVisualiserView


class ImgpyMainWindowView(QMainWindow):
    def __init__(self, config):
        super(ImgpyMainWindowView, self).__init__()
        uic.loadUi('./isis_imaging/gui/ui/main_window.ui', self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")

        self.presenter = ImgpyMainWindowPresenter(self, config)

        # load some sample data, currently provided from the GUI
        from core.imgdata import loader
        stack = loader.load_data(config)

        self.stackvis = ImgpyStackVisualiserView(self, stack)
        self.stackvis.setVisible(True)

    def set_value(self, value=5):
        pass

    def median_filter_clicked(self):
        self.presenter.notify(
            ImgpyMainWindowPresenter.Notification.MEDIAN_FILTER_CLICKED)
