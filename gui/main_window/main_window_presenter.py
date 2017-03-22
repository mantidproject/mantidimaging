from __future__ import (absolute_import, division, print_function)
from PyQt4.QtGui import QWidget


class ImgpyMainWindowPresenter(QWidget):
    def __init__(self, view, config):
        super(ImgpyMainWindowPresenter, self).__init__()
        self.view = view
        self.config = config
        from gui.main_window.main_window_model import ImgpyMainWindowModel
        self.model = ImgpyMainWindowModel()
