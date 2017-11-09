from __future__ import absolute_import, division, print_function

import os

import numpy as np

from enum import IntEnum
from logging import getLogger

from mantidimaging.gui.mvp_base import BasePresenter


class Notification(IntEnum):
    RENAME_WINDOW = 0
    HISTOGRAM = 1
    NEW_WINDOW_HISTOGRAM = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4
    CLEAR_ROI = 5
    STACK_MODE = 6
    SUM_MODE = 7
    REFRESH_IMAGE = 8


class Parameters(IntEnum):
    ROI = 0


class ImageMode(IntEnum):
    STACK = 0
    SUM = 1


class StackVisualiserPresenter(BasePresenter):

    def __init__(self, view, images, data_traversal_axis):
        super(StackVisualiserPresenter, self).__init__(view)
        self.images = images
        self.axis = data_traversal_axis
        self.mode = ImageMode.STACK
        self.summed_image = None

    def notify(self, signal):
        try:
            if signal == Notification.RENAME_WINDOW:
                self.do_rename_view()
            elif signal == Notification.HISTOGRAM:
                self.do_histogram()
            elif signal == Notification.NEW_WINDOW_HISTOGRAM:
                self.do_new_window_histogram()
            elif signal == Notification.SCROLL_UP:
                self.do_scroll_stack(1)
            elif signal == Notification.SCROLL_DOWN:
                self.do_scroll_stack(-1)
            elif signal == Notification.CLEAR_ROI:
                self.do_clear_roi()
            elif signal == Notification.STACK_MODE:
                self.image_mode = ImageMode.STACK
            elif signal == Notification.SUM_MODE:
                self.image_mode = ImageMode.SUM
            elif signal == Notification.REFRESH_IMAGE:
                self.view.show_current_image()
        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def do_rename_view(self):
        self.view.update_title_event()

    def do_histogram(self):
        """
        Executed when the shortcut is pressed by the user.
        For the current shortcut please check setup_shortcuts in view.
        """
        self.view.show_histogram_of_current_image(new_window=False)

    def do_new_window_histogram(self):
        """
        Executed when the shortcut is pressed by the user.
        For the current shortcut please check setup_shortcuts in view.
        """
        self.view.show_histogram_of_current_image(new_window=True)

    def do_clear_roi(self):
        """
        Clears the active ROI selection.
        """
        self.view.current_roi = None

    def delete_data(self):
        del self.images

    @property
    def image_mode(self):
        return self.mode

    @image_mode.setter
    def image_mode(self, mode):
        """
        Sets the mode used to display images.

        STACK mode allows scrolling through the stack of individual images.

        SUM mode summes the entire stack into a single image, divided by the
        number of images in the stack.
        """
        self.mode = mode

        # Create the summed image lazily
        if mode == ImageMode.SUM and self.summed_image is None:
            self.summed_image = np.divide(
                    np.sum(self.images.sample, axis=self.axis),
                    self.images.sample.shape[0])

        # Update image view
        self.view.show_current_image()

        # Disable slider in sum mode
        self.view.slider.set_active(mode == ImageMode.STACK)

    def get_image(self, index):
        if self.mode == ImageMode.STACK:
            if self.axis == 0:
                return self.images.sample[index, :, :]
            elif self.axis == 1:
                return self.images.sample[:, index, :]
            elif self.axis == 2:
                return self.images.sample[:, :, index]

        elif self.mode == ImageMode.SUM:
            return self.summed_image

        raise ValueError('Unknown image mode')

    def get_image_fullpath(self, index):
        filenames = self.images.filenames
        return filenames[index] if filenames is not None else ""

    def get_image_filename(self, index):
        filenames = self.images.filenames
        return os.path.basename(
                filenames[index] if filenames is not None else "")

    def get_image_count_on_axis(self, axis=None):
        """
        Returns the number of images on a given axis.
        :param axis: Axis on which to count images (defaults to data traversal
                     axis)
        """
        if axis is None:
            axis = self.axis
        return self.images.sample.shape[self.axis]

    def get_image_pixel_range(self):
        """
        Gets the range of pixel intensities across all images.

        :return: Tuple of (min, max) pixel intensities
        """
        return (self.images.sample.min(), self.images.sample.max())

    def do_scroll_stack(self, offset):
        """
        Scrolls through the stack by a given number of images.
        :param offset: Number of images to scroll through stack
        """
        if self.mode == ImageMode.STACK:
            idx = self.view.current_index() + offset
            self.view.set_index(idx)

    def get_parameter_value(self, parameter):
        """
        Gets a parameter from the stack visualiser for use elsewhere (e.g.
        filters).
        """
        if parameter == Parameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError(
                    "Invalid parameter name has been requested from the Stack "
                    "Visualiser, parameter: {0}".format(parameter))

    def getattr_and_clear(self, algorithm_dialog, attribute):
        attr = getattr(algorithm_dialog, attribute, None)
        if attr:
            setattr(algorithm_dialog, attribute, None)
        return attr
