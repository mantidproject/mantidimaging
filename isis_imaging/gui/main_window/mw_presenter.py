from __future__ import absolute_import, division, print_function

from enum import IntEnum

from gui.main_window.mw_model import ImgpyMainWindowModel


class Notification(IntEnum):
    MEDIAN_FILTER_CLICKED = 1


class ImgpyMainWindowPresenter(object):
    def __init__(self, view, config):
        super(ImgpyMainWindowPresenter, self).__init__()
        self.view = view
        self.config = config
        self.model = ImgpyMainWindowModel()

    def notify(self, signal):
        # do some magical error message reusal
        # try:
        # except any error:
        # show error message from the CORE, no errors will be written here!

        if signal == Notification.MEDIAN_FILTER_CLICKED:
            self.update_view_value()

    def update_view_value(self):
        self.view.set_value(5)
