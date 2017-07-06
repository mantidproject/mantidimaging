from __future__ import absolute_import, division, print_function

from enum import IntEnum

from isis_imaging.gui.stack_visualiser.sv_model import \
    ImgpyStackVisualiserModel


class Notification(IntEnum):
    RENAME_WINDOW = 0
    HISTOGRAM = 1


class StackViewerPresenter(object):
    def __init__(self, view, data, axis):
        super(StackViewerPresenter, self).__init__()
        self.view = view
        self.data = data
        self.axis = axis

        self.model = ImgpyStackVisualiserModel()

    def notify(self, signal):
        try:
            if signal == Notification.RENAME_WINDOW:
                self.do_rename_view()
            elif signal == Notification.HISTOGRAM:
                self.do_histogram()
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        print("Magic to be done here")

    def do_rename_view(self):
        self.view.update_title_event()

    def do_histogram(self):
        self.view.show_histogram_of_current_image()

    def delete_data(self):
        del self.data

    def get_image(self, index):
        if self.axis == 0:
            return self.data[index, :, :]
        elif self.axis == 1:
            return self.data[:, index, :]
        elif self.axis == 2:
            return self.data[:, :, index]

    def apply_to_data(self, func, *args, **kwargs):
        # TODO refactor
        do_before = getattr(func, "do_before", None)
        if hasattr(func, "do_before"):
            delattr(func, "do_before")
        do_after = getattr(func, "do_after", None)
        if hasattr(func, "do_after"):
            delattr(func, "do_after")

        if do_before:
            res_before = do_before(self.data)
        func(self.data, *args, **kwargs)
        if do_after:
            do_after(self.data, res_before)
        self.view.show_current_image()
