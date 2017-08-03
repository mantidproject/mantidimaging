from __future__ import absolute_import, division, print_function

import os

from enum import IntEnum

from isis_imaging.gui.algorithm_dialog import AlgorithmDialog
from isis_imaging.gui.stack_visualiser.sv_available_parameters import Parameters


class Notification(IntEnum):
    RENAME_WINDOW = 0
    HISTOGRAM = 1
    NEW_WINDOW_HISTOGRAM = 2


class StackVisualiserPresenter(object):
    def __init__(self, view, images, data_traversal_axis):
        super(StackVisualiserPresenter, self).__init__()
        self.view = view
        self.images = images
        self.axis = data_traversal_axis

    def notify(self, signal):
        try:
            if signal == Notification.RENAME_WINDOW:
                self.do_rename_view()
            elif signal == Notification.HISTOGRAM:
                self.do_histogram()
            elif signal == Notification.NEW_WINDOW_HISTOGRAM:
                self.do_new_window_histogram()
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        print("Magic to be done here")

    def do_rename_view(self):
        self.view.update_title_event()

    def do_histogram(self):
        """
        Executed when the shortcut is pressed by the user.
        For the current shortcut please check setup_shortcuts in sv_view.
        """
        self.view.show_histogram_of_current_image(new_window=False)

    def do_new_window_histogram(self):
        """
        Executed when the shortcut is pressed by the user.
        For the current shortcut please check setup_shortcuts in sv_view.
        """
        self.view.show_histogram_of_current_image(new_window=True)

    def delete_data(self):
        del self.images

    def get_image(self, index):
        if self.axis == 0:
            return self.images.get_sample()[index, :, :]
        elif self.axis == 1:
            return self.images.get_sample()[:, index, :]
        elif self.axis == 2:
            return self.images.get_sample()[:, :, index]

    def get_image_fullpath(self, index):
        filenames = self.images.get_filenames()
        return filenames[index] if filenames is not None else ""

    def get_image_filename(self, index):
        filenames = self.images.get_filenames()
        return os.path.basename(filenames[index] if filenames is not None else "")

    def handle_algorithm_dialog_request(self, parameter):
        if parameter == Parameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError(
                "Invalid parameter name has been requested from the Stack Visualiser, parameter: {0}".format(parameter))

    def apply_to_data(self, algorithm_dialog, *args, **kwargs):
        # We can't do this in Python 2.7 because we crash due to a circular reference
        # It should work when executed with Python 3.5
        assert isinstance(algorithm_dialog, AlgorithmDialog), "The object is not of the expected type."

        parameter_name = getattr(algorithm_dialog, "requested_parameter_name", None)

        parameter_value = self.handle_algorithm_dialog_request(parameter_name) if parameter_name else ()

        do_before = self.getattr_and_clear(algorithm_dialog, "do_before")
        do_after = self.getattr_and_clear(algorithm_dialog, "do_after")

        # save the result from the do_before operation, else just an empty tuple
        res_before = do_before(self.images.get_sample()) if do_before else ()

        # enforce that even single arguments are tuples, multiple returned arguments should be tuples by default
        if not isinstance(res_before, tuple):
            res_before = (res_before,)

        all_args = parameter_value + args
        algorithm_dialog.execute(self.images.get_sample(), *all_args, **kwargs)

        if do_after:
            do_after(self.images.get_sample(), *res_before)

        self.view.show_current_image()

    def getattr_and_clear(self, algorithm_dialog, attribute):
        attr = getattr(algorithm_dialog, attribute, None)
        if attr:
            setattr(algorithm_dialog, attribute, None)
        return attr
