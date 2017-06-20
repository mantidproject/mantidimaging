from __future__ import absolute_import, division, print_function

import os
import uuid

from enum import IntEnum

from isis_imaging.core.io import loader, saver
from gui.main_window.mw_model import ImgpyMainWindowModel


class Notification(IntEnum):
    MEDIAN_FILTER_CLICKED = 1
    LOAD = 2
    SAVE = 3


class ImgpyMainWindowPresenter(object):
    def __init__(self, view, config):
        super(ImgpyMainWindowPresenter, self).__init__()
        self.view = view
        self.config = config
        self.model = ImgpyMainWindowModel()
        # Move to model? It'll get sufficiently complicated I think
        self.active_stacks = {}

    def notify(self, signal):
        # do some magical error message reusal
        # try:
        # except any error:
        # show error message from the CORE, no errors will be written here!
        try:

            if signal == Notification.MEDIAN_FILTER_CLICKED:
                self.update_view_value()
            elif signal == Notification.LOAD:
                self.load_stack()
            elif signal == Notification.SAVE:
                self.save()

        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        print("Magic to be done here")

    def stack_list(self):
        stacks = []
        for stack_uuid, val in self.active_stacks.iteritems():
            # append the UUID and user friendly name
            user_friendly_name = val[0]
            stacks.append((stack_uuid, user_friendly_name))

        # sort by user friendly name
        return sorted(stacks, key=lambda x: x[1])

    def remove_stack(self, uuid):
        # need to call active_stack.destroy()?
        del self.active_stacks[uuid]

    def load_stack(self):
        sample_path = self.view.load_dialogue.sample_path()
        flat_path = self.view.load_dialogue.flat_path()
        dark_path = self.view.load_dialogue.dark_path()
        image_format = self.view.load_dialogue.image_format
        parallel_load = self.view.load_dialogue.parallel_load()
        indices = self.view.load_dialogue.indices()

        if not sample_path:
            return

        stack = loader.load(
            sample_path,
            None,
            None,
            image_format,
            parallel_load=parallel_load,
            indices=indices)

        title = os.path.basename(sample_path)
        dock_widget = self.view.create_stack_window(stack, title=title)

        # append this onto the widget, otherwise it will be a pain to retrieve the information
        # from inside the stack visualiser class
        stackvis = dock_widget.widget()

        # add information to qdockwidget or the stack window?
        # currently added to the qdockwidget
        stackvis.sample_path = sample_path
        stackvis.flat_path = flat_path
        stackvis.dark_path = dark_path
        stackvis.image_format = image_format
        stackvis.parallel_load = parallel_load
        stackvis.uuid = uuid.uuid1()

        self.active_stacks[stackvis.uuid] = (title, dock_widget)
        print("Active stacks", self.active_stacks)

    def save(self, indices=None):
        s_uuid = self.view.save_dialogue.selected_stack
        output_dir = self.view.save_dialogue.save_path()
        image_format = self.view.save_dialogue.image_format()
        overwrite = self.view.save_dialogue.overwrite()
        swap_axes = self.view.save_dialogue.swap_axes()

        # rarely do you see code as ugly as this
        self.active_stacks[s_uuid][1].widget().apply_to_data(
            saver.save,
            output_dir=output_dir,
            swap_axes=swap_axes,
            overwrite_all=overwrite,
            img_format=image_format,
            indices=indices)

    def do_badly(self, stack_uuid, func):
        self.active_stacks[stack_uuid][1].widget().apply_to_data(func)
