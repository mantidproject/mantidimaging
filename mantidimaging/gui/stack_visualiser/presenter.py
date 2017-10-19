from __future__ import absolute_import, division, print_function

import os

import numpy as np

from logging import getLogger
from enum import IntEnum

from .available_parameters import (Parameters, PARAMETERS_ERROR_MESSAGE)


class Notification(IntEnum):
    RENAME_WINDOW = 0
    HISTOGRAM = 1
    NEW_WINDOW_HISTOGRAM = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4
    CLEAR_ROI = 5
    STACK_MODE = 6
    SUM_MODE = 7


class ImageMode(IntEnum):
    STACK = 0
    SUM = 1


class StackVisualiserPresenter(object):
    def __init__(self, view, images, data_traversal_axis):
        super(StackVisualiserPresenter, self).__init__()
        self.view = view
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
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        self.view.show_error_dialog(error)

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
                return self.images.get_sample()[index, :, :]
            elif self.axis == 1:
                return self.images.get_sample()[:, index, :]
            elif self.axis == 2:
                return self.images.get_sample()[:, :, index]

        elif self.mode == ImageMode.SUM:
            return self.summed_image

        raise ValueError('Unknown image mode')

    def get_image_fullpath(self, index):
        filenames = self.images.get_filenames()
        return filenames[index] if filenames is not None else ""

    def get_image_filename(self, index):
        filenames = self.images.get_filenames()
        return os.path.basename(filenames[index] if filenames is not None else "")

    def get_image_count_on_axis(self, axis=None):
        """
        Returns the number of images on a given axis.
        :param axis: Axis on which to count images (defaults to data traversal axis)
        """
        if axis is None:
            axis = self.axis
        return self.images.get_sample().shape[self.axis]

    def get_image_pixel_range(self):
        """
        Gets the range of pixel intensities across all images.

        :return: Tuple of (min, max) pixel intensities
        """
        return (self.images.get_sample().min(), self.images.get_sample().max())

    def do_scroll_stack(self, offset):
        """
        Scrolls through the stack by a given number of images.
        :param offset: Number of images to scroll through stack
        """
        if self.mode == ImageMode.STACK:
            idx = self.view.current_index() + offset
            self.view.set_index(idx)

    def handle_algorithm_dialog_request(self, parameter):
        # Developer note: Parameters need to be checked for both here and in algorithm_dialog.py
        if parameter == Parameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError(PARAMETERS_ERROR_MESSAGE.format(parameter))

    def apply_to_data(self, algorithm_dialog):
        log = getLogger(__name__)

        # This will call the custom_execute function in the filter's _gui declaration, and read off the values from the
        # parameter fields that have been shown to the user
        algorithm_dialog.prepare_execute()

        parameter_name = algorithm_dialog.requested_parameter_name
        parameter_value = self.handle_algorithm_dialog_request(parameter_name) if parameter_name else ()
        getLogger(__name__).info("Received parameter value {}".format(parameter_value))
        if not isinstance(parameter_value, tuple):
            parameter_value = (parameter_value,)

        do_before = self.getattr_and_clear(algorithm_dialog, "do_before")
        do_after = self.getattr_and_clear(algorithm_dialog, "do_after")

        # save the result from the do_before operation, else just an empty tuple
        res_before = do_before(self.images.get_sample()) if do_before else ()

        # enforce that even single arguments are tuples, multiple returned arguments should be tuples by default
        if not isinstance(res_before, tuple):
            res_before = (res_before,)

        ret_val = algorithm_dialog.execute(self.images.get_sample(), *parameter_value)

        # Handle the return value from the algorithm dialog
        if isinstance(ret_val, tuple):
            # Tuples are assumed to be three elements containing sample, flat
            # and dark images
            self.images.sample, self.images.flat, self.images.dark = ret_val
        elif isinstance(ret_val, np.ndarray):
            # Single Numpy arrays are assumed to be just the sample image
            self.images.sample = ret_val
        else:
            log.debug('Unknown execute return value: {}'.format(type(ret_val)))

        # execute the do_after function by passing the results from the do_before
        if do_after:
            do_after(self.images.get_sample(), *res_before)

        self.view.show_current_image()

    def getattr_and_clear(self, algorithm_dialog, attribute):
        attr = getattr(algorithm_dialog, attribute, None)
        if attr:
            setattr(algorithm_dialog, attribute, None)
        return attr
