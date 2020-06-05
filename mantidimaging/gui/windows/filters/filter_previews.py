from collections import namedtuple
from typing import Tuple, Optional

from PyQt5.QtWidgets import QGraphicsLinearLayout
from numpy import ndarray
from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotItem, LegendItem, ViewBox

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint

histogram_axes_labels = {'left': 'Frequency', 'bottom': 'Value'}
before_pen = (0, 0, 200)
after_pen = (0, 200, 0)

Coord = namedtuple('Coord', ['row', 'col'])
histogram_coords = {"before": Coord(4, 0), "after": Coord(4, 1), "combined": Coord(4, 0)}

label_coords = {"before": Coord(3, 0), "after": Coord(3, 1), "combined": Coord(3, 1)}


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
        self.histogram = None
        self.before_histogram = None
        self.after_histogram = None

        self.combined_histograms = True
        self.histogram_legend_visible = False

        self.addLabel("Image before")
        self.addLabel("Image after")
        self.addLabel("Image difference")
        self.nextRow()

        self.image_before, self.image_before_vb = self.image_in_vb(name="before")
        self.image_after, self.image_after_vb = self.image_in_vb(name="after")
        self.image_difference, self.image_difference_vb = self.image_in_vb(name="difference")

        # Ensure images resize equally
        image_layout = QGraphicsLinearLayout()
        image_layout.addItem(self.image_before_vb)
        image_layout.addItem(self.image_after_vb)
        image_layout.addItem(self.image_difference_vb)
        self.addItem(image_layout, colspan=3)
        self.nextRow()

        before_details = self.addLabel("")
        after_details = self.addLabel("")
        difference_details = self.addLabel("")

        self.display_formatted_detail = {
            self.image_before: lambda val: before_details.setText(f"Before: {val:.2f}"),
            self.image_after: lambda val: after_details.setText(f"After: {val:.2f}"),
            self.image_difference: lambda val: difference_details.setText(f"Difference: {val:.2f}"),
        }

        for img in self.image_before, self.image_after, self.image_difference:
            img.hoverEvent = lambda ev: self.mouse_over(ev)

        self.img_hover_text = {
            self.image_before: "Before: {}",
            self.image_after: "After: {}",
            self.image_difference: "Difference: {}",
        }

    def image_in_vb(self, name=None):
        im = ImageItem()
        vb = ViewBox(invertY=True, lockAspect=True, name=name)
        vb.addItem(im)
        return im, vb

    def clear_items(self):
        self.image_before.clear()
        self.image_after.clear()
        self.image_difference.clear()
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
        coords = set(c for c in histogram_coords.values())
        histograms = (self.getItem(*coord) for coord in coords)
        for histogram in filter(lambda h: h is not None, histograms):
            self.removeItem(histogram)
        self.histogram = None
        self.before_histogram = None
        self.after_histogram = None

    def delete_histogram_labels(self):
        coords = set(c for c in label_coords.values())
        labels = (self.getItem(*coord) for coord in coords)
        for label in filter(lambda h: h is not None, labels):
            self.removeItem(label)

    def draw_combined_histogram(self):
        self.histogram = self.addPlot(row=histogram_coords["combined"].row,
                                      col=histogram_coords["combined"].col,
                                      labels=histogram_axes_labels,
                                      lockAspect=True,
                                      colspan=3)
        self.addLabel("Pixel values", row=label_coords["combined"].row, col=label_coords["combined"].col)

        # Plot any histogram that has data, and add a legend if both exist
        if self.before_histogram_data is not None:
            before_plot = self.histogram.plot(*self.before_histogram_data, pen=before_pen)
            if self.after_histogram_data is not None:
                after_plot = self.histogram.plot(*self.after_histogram_data, pen=after_pen)
                self.create_histogram_legend(before_plot, after_plot)
                if not self.histogram_legend_visible:
                    self.histogram.legend.hide()
        elif self.after_histogram_data is not None:
            self.histogram.plot(*self.after_histogram_data, pen=after_pen)

    def draw_separate_histograms(self):
        hc = histogram_coords
        self.before_histogram = self.addPlot(row=hc["before"].row,
                                             col=hc["before"].col,
                                             labels=histogram_axes_labels,
                                             lockAspect=True)
        self.after_histogram = self.addPlot(row=hc["after"].row,
                                            col=hc["after"].col,
                                            labels=histogram_axes_labels,
                                            lockAspect=True)
        lc = label_coords
        self.addLabel("Pixel values before", row=lc["before"].row, col=lc["before"].col)
        self.addLabel("Pixel values after", row=lc["after"].row, col=lc["after"].col)
        if self.before_histogram_data is not None:
            self.before_histogram.plot(*self.before_histogram_data, pen=before_pen)

        if self.after_histogram_data is not None:
            self.after_histogram.plot(*self.after_histogram_data, pen=after_pen)

    def create_histogram_legend(self, before_plot, after_plot):
        legend = self.histogram.addLegend()
        legend.addItem(before_plot, "Before")
        legend.addItem(after_plot, "After")

    def set_before_histogram(self, data: Tuple[ndarray]):
        self.before_histogram_data = data
        self.redraw_histograms()

    def set_after_histogram(self, data: Tuple[ndarray]):
        self.after_histogram_data = data
        self.redraw_histograms()

    @property
    def histogram_legend(self) -> Optional[LegendItem]:
        if self.histogram and self.histogram.legend:
            return self.histogram.legend
        return None

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())
        for img in self.image_before, self.image_after, self.image_difference:
            if img.image is not None and pos.x < img.image.shape[0] and pos.y < img.image.shape[1]:
                pixel_value = img.image[pos.y, pos.x]
                self.display_formatted_detail[img](pixel_value)

    def link_all_views(self):
        for view1, view2 in zip([self.image_before_vb, self.image_after_vb],
                                [self.image_after_vb, self.image_difference_vb]):
            view1.linkView(ViewBox.XAxis, view2)
            view1.linkView(ViewBox.YAxis, view2)

    def unlink_all_views(self):
        for view in self.image_before_vb, self.image_after_vb, self.image_difference_vb:
            view.linkView(ViewBox.XAxis, None)
            view.linkView(ViewBox.YAxis, None)
