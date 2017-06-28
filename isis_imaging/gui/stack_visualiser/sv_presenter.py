from __future__ import absolute_import, division, print_function

from PyQt5.Qt import QWidget

from isis_imaging.gui.stack_visualiser.sv_model import ImgpyStackVisualiserModel


class StackViewerPresenter(QWidget):
    def __init__(self, view, data, axis):
        super(StackViewerPresenter, self).__init__()
        self.view = view
        self.data = data
        self.axis = axis

        self.model = ImgpyStackVisualiserModel()

    def delete_data(self):
        del self.data

    def get_image(self, index, axis=None):
        if axis is None:
            # if not provided use the class one
            axis = self.axis

        if axis == 0:
            return self.data[index, :, :]
        elif axis == 1:
            return self.data[:, index, :]

        elif axis == 2:
            return self.data[:, :, index]

    def create_histogram(self, image):
        # update the histogram
        # hist_to_be, bin_edges = np.histogram(im)

        self.hist_axis.cla()
        self.hist_axis.hist(image.flatten(), bins=256)

    def apply_to_data(self, func, *args, **kwargs):

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
        self.view.update_current_image()
