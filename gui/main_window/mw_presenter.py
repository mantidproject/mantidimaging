from __future__ import (absolute_import, division, print_function)
from enum import IntEnum


class Notification(IntEnum):
    MEDIAN_FILTER_CLICKED = 1


class ImgpyMainWindowPresenter(object):
    def __init__(self, view, config):
        super(ImgpyMainWindowPresenter, self).__init__()
        self.view = view
        self.config = config
        from gui.mw.mw_model import ImgpyMainWindowModel
        self.model = ImgpyMainWindowModel()

    def notify(self, signal):
        if signal == Notification.MEDIAN_FILTER_CLICKED:
            self.update_view_value()

    def update_view_value(self):
        self.view.set_value(5)
