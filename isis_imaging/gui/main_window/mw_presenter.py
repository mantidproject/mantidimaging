from __future__ import absolute_import, division, print_function

import os

from enum import IntEnum

from core.imgdata import loader
from gui.main_window.mw_model import ImgpyMainWindowModel


class Notification(IntEnum):
    MEDIAN_FILTER_CLICKED = 1
    LOAD_STACK = 2


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

        try:  # this is very very bad, it completely fucks the stacks trace!
            if signal == Notification.MEDIAN_FILTER_CLICKED:
                self.update_view_value()
            elif signal == Notification.LOAD_STACK:
                self.load_stack()
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def load_stack(self):
        # then presenter will load it and set it in the model
        sample_path = self.view.load_dialogue.sample_path()
        # save to model for future runs? or keep getting the value from the dialogue? less places to update
        flat_path = self.view.load_dialogue.flat_path()
        dark_path = self.view.load_dialogue.dark_path()
        img_format = self.view.load_dialogue.img_extension
        parallel_load = self.view.load_dialogue.parallel_load()
        print("Img format", img_format)

        if not sample_path:
            return

        # dirname removes the file name from the path
        stack = loader.load(
            sample_path,
            flat_path,
            dark_path,
            img_format,
            parallel_load=parallel_load)

        self.view.add_stack_dock(stack, title=os.path.basename(sample_path))

    def show_error(self, error):
        print("Magic to be done here")
