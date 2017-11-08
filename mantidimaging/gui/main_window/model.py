from __future__ import (absolute_import, division, print_function)

import os
import uuid

from logging import getLogger

from mantidimaging.core.io import loader, saver


class MainWindowModel(object):
    def __init__(self, config):
        super(MainWindowModel, self).__init__()
        self.config = config

        self.active_stacks = {}

    def do_load_stack(self, sample_path, image_format, parallel_load, indices,
                      progress):
        images = loader.load(
            sample_path,
            None,
            None,
            in_format=image_format,
            parallel_load=parallel_load,
            indices=indices,
            progress=progress)

        return images

    def do_saving(self, stack_uuid, output_dir, name_prefix, image_format,
                  overwrite, swap_axes, indices, progress):
        svp = self.get_stack_visualiser(stack_uuid).presenter
        saver.save(
            data=svp.images.sample,
            output_dir=output_dir,
            name_prefix=name_prefix,
            swap_axes=swap_axes,
            overwrite_all=overwrite,
            out_format=image_format,
            indices=indices,
            progress=progress)

        return True

    def create_name(self, filename):
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        current_names = self.stack_names()
        num = 1
        while name in current_names:
            num += 1
            name = filename + '_{}'.format(num)

        return name

    def stack_list(self):
        stacks = []
        for stack_uuid, widget in self.active_stacks.items():
            # ask the widget for its current title
            current_name = widget.windowTitle()
            # append the UUID and user friendly name
            stacks.append((stack_uuid, current_name))

        # sort by user friendly name
        return sorted(stacks, key=lambda x: x[1])

    def stack_names(self):
        # unpacks the tuple and only gives the correctly sorted human readable
        # names
        return list(zip(*self.stack_list()))[1] if self.active_stacks else []

    def add_stack(self, stack_visualiser, dock_widget):
        # generate unique ID for this stack
        stack_visualiser.uuid = uuid.uuid1()
        self.active_stacks[stack_visualiser.uuid] = dock_widget
        getLogger(__name__).debug(
                "Active stacks {}".format(self.active_stacks))

    def get_stack(self, stack_uuid):
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The QDockWidget that contains the Stack Visualiser.
                For direct access to the Stack Visualiser widget use
                get_stack_visualiser
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
        del self.active_stacks[stack_uuid]
