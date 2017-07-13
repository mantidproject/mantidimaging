from __future__ import absolute_import, division, print_function

from enum import Enum

from .mw_model import MainWindowModel


class Notification(Enum):
    LOAD = 1
    SAVE = 2


class MainWindowPresenter(object):
    def __init__(self, view, config):
        super(MainWindowPresenter, self).__init__()
        self.view = view
        self.model = MainWindowModel(config)

    def notify(self, signal):
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
        selected_file = self.view.load_dialogue.sample_file()
        sample_path = self.view.load_dialogue.sample_path()
        image_format = self.view.load_dialogue.image_format
        parallel_load = self.view.load_dialogue.parallel_load()
        indices = self.view.load_dialogue.indices()

        if not sample_path:
            return

        data = self.model.do_load_stack(sample_path, image_format, parallel_load, indices)

        title = self.model.create_title(selected_file)

        dock_widget = self.view.create_stack_window(data, title=title)

        stack_visualiser = dock_widget.widget()

        self.model.add_stack(stack_visualiser, dock_widget)

    def save(self, indices=None):
        stack_uuid = self.view.save_dialogue.selected_stack
        output_dir = self.view.save_dialogue.save_path()
        name_prefix = self.view.save_dialogue.name_prefix()
        image_format = self.view.save_dialogue.image_format()
        overwrite = self.view.save_dialogue.overwrite()
        swap_axes = self.view.save_dialogue.swap_axes()

        self.model.do_saving(stack_uuid, output_dir, name_prefix,
                             image_format, overwrite, swap_axes, indices)

    def apply_to_data(self, stack_uuid, func):
        self.model.apply_to_data(stack_uuid, func)

    def stack_names(self):
        return self.model.stack_names()

    def stack_list(self):
        return self.model.stack_list()
