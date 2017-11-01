from __future__ import absolute_import, division, print_function

from enum import Enum
from logging import getLogger

import numpy as np

from mantidimaging.core.io.loader import Images
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.histogram import (
        generate_histogram_from_image)

from .misc import get_auto_params_from_stack
from .model import FiltersWindowModel


class Notification(Enum):
    UPDATE_STACK_LIST = 1
    REGISTER_ACTIVE_FILTER = 2
    APPLY_FILTER = 3
    UPDATE_PREVIEWS = 4


class FiltersWindowPresenter(object):
    def __init__(self, view, main_window):
        super(FiltersWindowPresenter, self).__init__()

        self.view = view
        self.model = FiltersWindowModel(main_window)

        self.main_window = main_window

        # Refresh the stack list in the algorithm dialog whenever the active
        # stacks change
        self.main_window.active_stacks_changed.connect(
                lambda: self.notify(Notification.UPDATE_STACK_LIST))

    def notify(self, signal):
        try:
            if signal == Notification.UPDATE_STACK_LIST:
                self.do_update_stack_list()
            elif signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def show_error(self, error):
        self.view.show_error_dialog(error)

    def set_stack_index(self, stack_idx):
        """
        Sets the currently selected stack index.
        """
        self.model.stack_idx = stack_idx

    def do_update_stack_list(self):
        """
        Refreshes the stack list and UUID cache.

        Must be called at least once before the UI is shown.
        """
        # Clear the previous entries from the drop down menu
        self.view.stackSelector.clear()

        # Get all the new stacks
        stack_list = self.main_window.stack_list()
        if stack_list:
            self.model.stack_uuids, user_friendly_names = zip(*stack_list)
            self.view.stackSelector.addItems(user_friendly_names)

    def do_register_active_filter(self):
        filter_idx = self.view.filterSelector.currentIndex()

        # Get registration function for new filter
        register_func = \
            self.model.filter_registration_func(filter_idx)

        # Register new filter (adding it's property widgets to the properties
        # layout)
        self.model.setup_filter(
                register_func(self.view.filterPropertiesLayout))

    def do_apply_filter(self):
        self.model.do_apply_filter()

    def do_update_previews(self):
        log = getLogger(__name__)

        progress = Progress.ensure_instance()
        progress.task_name = 'Filter preview'
        progress.add_estimated_steps(9)

        with progress:
            progress.update(msg='Getting stack')
            stack = self.model.get_stack()
            if stack is None:
                return

            # Update image before
            self._update_preview_image(stack.get_image(0),
                                       self.view.preview_image_before,
                                       self.view.preview_histogram_before,
                                       progress)

            # Generate sub-stack and run filter
            progress.update(msg='Running preview filter')
            exec_kwargs = get_auto_params_from_stack(
                    stack, self.model.auto_props)

            filtered_image_data = None
            try:
                sub_images = Images(np.asarray([stack.get_image(0)]))
                self.model.apply_filter(sub_images, exec_kwargs)
                filtered_image_data = sub_images.get_sample()[0]
            except Exception:
                log.exception("Error applying filter for preview")

            # Update image after
            if filtered_image_data is not None:
                self._update_preview_image(filtered_image_data,
                                           self.view.preview_image_after,
                                           self.view.preview_histogram_after,
                                           progress)

            # Redraw
            progress.update(msg='Redraw canvas')
            self.view.canvas.draw()

    def _update_preview_image(self, image_data, image, histogram, progress):
        # Generate histogram data
        progress.update(msg='Generating histogram')
        center, hist, _ = generate_histogram_from_image(image_data)

        # Update image
        progress.update(msg='Updating image')
        # TODO: ideally this should update the data without replotting but a
        # valid image must exist to start with (which may not always happen)
        # and this only works as long as the extents do not change.
        image.cla()
        image.imshow(image_data, cmap=self.view.cmap)

        # Update histogram
        progress.update(msg='Updating histogram')
        histogram.lines[0].set_data(center, hist)
        histogram.relim()
        histogram.autoscale()
