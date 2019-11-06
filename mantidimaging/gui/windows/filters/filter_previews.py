from typing import Tuple

from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotItem
from numpy import ndarray

histogram_axes_labels = {'left': 'Frequency', 'bottom': 'Value'}


class FilterPreviews(GraphicsLayoutWidget):
    image_before: ImageItem
    image_after: ImageItem
    histogram_before: PlotItem
    histogram_after: PlotItem

    def __init__(self, parent=None, **kwargs):
        super(FilterPreviews, self).__init__(parent, **kwargs)
        self.before_histogram_data = None
        self.after_histogram_data = None

        self.addLabel("Image before:")
        self.addLabel("Pixel values before:")
        self.nextRow()

        self.image_before = ImageItem()
        self.image_before_vb = self.addViewBox(invertY=True)
        self.image_before_vb.addItem(self.image_before)
        self.histogram = self.addPlot(labels=histogram_axes_labels)

        self.nextRow()
        self.addLabel("Image after:")
        self.nextRow()

        self.image_after = ImageItem()
        self.image_after_vb = self.addViewBox(invertY=True)
        self.image_after_vb.addItem(self.image_after)

    def clear_items(self):
        self.image_before.setImage()
        self.image_after.setImage()
        self.histogram.clear()

    # There seems to be a bug with pyqtgraph.PlotDataItem.setData not redrawing.
    # This works around it by redrawing both plots completely, which is fast enough to be ok.
    def redraw_histograms(self):
        self.histogram.clear()
        if self.before_histogram_data is not None:
            self.histogram.plot(*self.before_histogram_data, pen=(0, 0, 200))

        if self.after_histogram_data is not None:
            self.histogram.plot(*self.after_histogram_data, pen=(0, 200, 0))

    def set_before_histogram(self, data: Tuple[ndarray]):
        self.before_histogram_data = data
        self.redraw_histograms()

    def set_after_histogram(self, data: Tuple[ndarray]):
        self.after_histogram_data = data
        self.redraw_histograms()
