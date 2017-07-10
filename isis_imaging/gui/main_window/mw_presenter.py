from __future__ import absolute_import, division, print_function


from enum import Enum

from . import mw_model


class Notification(Enum):
    LOAD = 1
    SAVE = 2


class MainWindowPresenter(object):
    def __init__(self, view, config):
        super(MainWindowPresenter, self).__init__()
        self.view = view
        self.model = mw_model.MainWindowModel(config)

    def notify(self, signal):
        # do some magical error message reusage
        # try:
        # except any error:
        # show error message from the CORE, no errors will be written here!
        try:
            if signal == Notification.LOAD:
                self.load_stack()
            elif signal == Notification.SAVE:
                self.save()

        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        print("TODO Error window should be shown here to the user with the following error:", error)

    def remove_stack(self, uuid):
        self.model.do_remove_stack(uuid)

    def load_stack(self):
        sample_path = self.view.load_dialogue.sample_path()
        image_format = self.view.load_dialogue.image_format
        parallel_load = self.view.load_dialogue.parallel_load()
        indices = self.view.load_dialogue.indices()

        if not sample_path:
            return

        self.model.do_load_stack(
            image_format, indices, parallel_load, sample_path)

    def save(self, indices=None):
        stack_uuid = self.view.save_dialogue.selected_stack
        output_dir = self.view.save_dialogue.save_path()
        image_format = self.view.save_dialogue.image_format()
        overwrite = self.view.save_dialogue.overwrite()
        swap_axes = self.view.save_dialogue.swap_axes()

        self.model.do_saving(stack_uuid, output_dir,
                             image_format, overwrite, swap_axes, indices)

    def apply_to_data(self, stack_uuid, func):
        self.model.apply_to_data(stack_uuid, func)
