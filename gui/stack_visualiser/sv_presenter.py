from __future__ import (absolute_import, division, print_function)
from PyQt4.QtGui import QWidget


class ImgpyStackViewerPresenter(QWidget):
    def __init__(self, view, data, axis):
        super(ImgpyStackViewerPresenter, self).__init__()
        self.view = view
        self.data = data
        self.axis = axis

        from gui.stack_visualiser.stack_visualiser_model import ImgpyStackVisualiserModel
        self.model = ImgpyStackVisualiserModel()

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
