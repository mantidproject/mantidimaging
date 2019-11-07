from typing import Tuple, Optional

from numpy import ndarray
from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotItem

histogram_axes_labels = {'left': 'Frequency', 'bottom': 'Value'}


class FilterPreviews(GraphicsLayoutWidget):
    image_before: ImageItem
    image_after: ImageItem
    image_diff: ImageItem
    histogram_before: Optional[PlotItem]
    histogram_after: Optional[PlotItem]
    histogram: Optional[PlotItem]

    def __init__(self, parent=None, **kwargs):
        super(FilterPreviews, self).__init__(parent, **kwargs)
        self.before_histogram_data = None
        self.after_histogram_data = None
        self.combined_histograms = True
        self.histogram = None
        self.before_histogram = None
        self.after_histogram = None

        self.addLabel("Image before")
        self.nextRow()

        self.image_before, self.image_before_vb = self.add_image_in_vb()

        self.nextRow()
        self.addLabel("Image after")
        self.nextRow()

        self.image_after, self.image_after_bv = self.add_image_in_vb()

        self.nextRow()
        self.addLabel("Image difference")
        self.nextRow()

        self.image_difference, self.image_difference_vb = self.add_image_in_vb()

    def add_image_in_vb(self):
        im = ImageItem()
        vb = self.addViewBox(invertY=True, lockAspect=True)
        vb.addItem(im)
        return im, vb

    def clear_items(self):
        self.image_before.setImage()
        self.image_after.setImage()
        self.image_difference.setImage()
        self.delete_histograms()

    # There seems to be a bug with pyqtgraph.PlotDataItem.setData not forcing a redraw.
    # We work around this by redrawing everything completely every time, which is unreasonably fast anyway.
    def redraw_histograms(self):
        self.delete_histograms()
        self.delete_histogram_labels()

        if self.combined_histograms:
            self.draw_combined_histogram()
        else:
            self.draw_separate_histograms()

    def delete_histograms(self):
        histogram_coords = [(1, 1), (3, 1)]
        histograms = (self.getItem(*coord) for coord in histogram_coords)
        for histogram in filter(lambda h: h is not None, histograms):
            self.removeItem(histogram)
        self.histogram = None
        self.before_histogram = None
        self.after_histogram = None

    def delete_histogram_labels(self):
        label_coords = [(0, 1), (2, 1)]
        labels = (self.getItem(*coord) for coord in label_coords)
        for label in filter(lambda h: h is not None, labels):
            self.removeItem(label)

    def draw_combined_histogram(self):
        self.histogram = self.addPlot(row=1, col=1, labels=histogram_axes_labels, lockAspect=True)
        self.addLabel("Pixel values", row=0, col=1)

        # Plot any histogram that has data, and add a legend if both exist
        if self.before_histogram_data is not None:
            before_plot = self.histogram.plot(*self.before_histogram_data, pen=(0, 0, 200))
            if self.after_histogram_data is not None:
                after_plot = self.histogram.plot(*self.after_histogram_data, pen=(0, 200, 0))
                legend = self.histogram.addLegend()
                legend.addItem(before_plot, "Before")
                legend.addItem(after_plot, "After")
        elif self.after_histogram_data is not None:
            self.histogram.plot(*self.after_histogram_data, pen=(0, 200, 0))

    def draw_separate_histograms(self):
        self.before_histogram = self.addPlot(row=1, col=1, labels=histogram_axes_labels, lockAspect=True)
        self.after_histogram = self.addPlot(row=3, col=1, labels=histogram_axes_labels, lockAspect=True)
        self.addLabel("Pixel values before", row=0, col=1)
        self.addLabel("Pixel values after", row=2, col=1)
        if self.before_histogram_data is not None:
            self.before_histogram.plot(*self.before_histogram_data, pen=(0, 0, 200))

        if self.after_histogram_data is not None:
            self.after_histogram.plot(*self.after_histogram_data, pen=(0, 200, 0))

    def set_before_histogram(self, data: Tuple[ndarray]):
        self.before_histogram_data = data
        self.redraw_histograms()

    def set_after_histogram(self, data: Tuple[ndarray]):
        self.after_histogram_data = data
        self.redraw_histograms()
