from __future__ import (absolute_import, division, print_function)

import os
import uuid

from isis_imaging.core.io import loader, saver


class MainWindowModel(object):
    def __init__(self, view, config):
        super(MainWindowModel, self).__init__()
        self.view = view
        self.config = config

        self.active_stacks = {}

    def do_load_stack(self, image_format, indices, parallel_load, sample_path):
        stack, _, _ = loader.load(
            sample_path,
            None,
            None,
            image_format,
            parallel_load=parallel_load,
            indices=indices)
        title = os.path.basename(sample_path)
        dock_widget = self.view.create_stack_window(stack, title=title)

        stackvis = dock_widget.widget()

        stackvis.uuid = uuid.uuid1()
        self.active_stacks[stackvis.uuid] = dock_widget
        print("Active stacks", self.active_stacks)

    def stack_list(self):
        stacks = []
        for stack_uuid, widget in self.active_stacks.items():
            # ask the widget for its current title
            current_name = widget.windowTitle()
            # append the UUID and user friendly name
            stacks.append((stack_uuid, current_name))

        # sort by user friendly name
        return sorted(stacks, key=lambda x: x[1])

    def get_stack(self, stack_uuid):
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The QDockWidget that contains the Stack Visualiser. For direct access to the
                Stack Visualiser widget use get_stack_visualiser
        """
        return self.active_stacks[stack_uuid]

    def get_stack_visualiser(self, stack_uuid):
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The Stack Visualiser widget that contains the data.
        """
        return self.active_stacks[stack_uuid].widget()

    def do_remove_stack(self, stack_uuid):
        """
        Removes the stack from the active_stacks dictionary.

        :param stack_uuid: The unique ID of the stack that will be removed.
        """
        del self.active_stacks[uuid]

    def do_saving(self, stack_uuid, output_dir, image_format, overwrite, swap_axes, indices):
        self.get_stack_visualiser(stack_uuid).apply_to_data(
            saver.save,
            output_dir=output_dir,
            swap_axes=swap_axes,
            overwrite_all=overwrite,
            img_format=image_format,
            indices=indices)

    def apply_to_data(self, stack_uuid, function):
        self.get_stack_visualiser(stack_uuid).apply_to_data(function)
