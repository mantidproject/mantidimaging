# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import namedtuple
from logging import getLogger
from typing import Optional

import numpy as np
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QGuiApplication, QResizeEvent
from pyqtgraph import ColorMap, GraphicsLayoutWidget, ImageItem, LegendItem, PlotItem, ViewBox
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint

LOG = getLogger(__name__)

histogram_axes_labels = {'left': 'Count', 'bottom': 'Gray value'}
before_pen = (200, 0, 0)
after_pen = (0, 200, 0)
diff_pen = (0, 0, 200)

Coord = namedtuple('Coord', ['row', 'col'])
histogram_coords = {"before": Coord(4, 0), "after": Coord(4, 1), "combined": Coord(4, 0)}

label_coords = {"before": Coord(3, 0), "after": Coord(3, 1), "combined": Coord(3, 1)}


def _data_valid_for_histogram(data):
    return data is not None and any(d is not None for d in data)


class FilterPreviews(GraphicsLayoutWidget):
    image_before: ImageItem
    image_after: ImageItem
    image_diff: ImageItem
    histogram_before: Optional[PlotItem]
    histogram_after: Optional[PlotItem]
    histogram: Optional[PlotItem]

    def __init__(self, parent=None, **kwargs):
        super(FilterPreviews, self).__init__(parent, **kwargs)

        widget_location = self.mapToGlobal(QPoint(self.width() / 2, 0))
        # allow the widget to take up to 80% of the desktop's height
        if QGuiApplication.screenAt(widget_location) is not None:
            screen_height = QGuiApplication.screenAt(widget_location).availableGeometry().height()
        else:
            screen_height = max(QGuiApplication.primaryScreen().availableGeometry().height(), 600)
            LOG.info("Unable to detect current screen. Setting screen height to %s" % screen_height)
        self.ALLOWED_HEIGHT: QRect = screen_height * 0.8

        self.before_histogram_data = None
        self.after_histogram_data = None
        self.histogram = None
        self.before_histogram = None
        self.after_histogram = None
        self.combined_histograms = True
        self.histogram_legend_visible = True

        self.addLabel("Image before")
        self.addLabel("Image after")
        self.addLabel("Image difference")
        self.nextRow()

        self.image_before, self.image_before_vb, self.image_before_hist = self.image_in_vb(name="before")
        self.image_after, self.image_after_vb, self.image_after_hist = self.image_in_vb(name="after")
        self.image_difference, self.image_difference_vb, self.image_difference_hist = self.image_in_vb(
            name="difference")

        self.image_after_overlay = ImageItem()
        self.image_after_overlay.setZValue(10)
        self.image_after_vb.addItem(self.image_after_overlay)

        # Ensure images resize equally
        self.image_layout: GraphicsLayout = self.addLayout(colspan=6)
        self.image_layout.addItem(self.image_before_vb, 0, 0)
        self.image_layout.addItem(self.image_before_hist, 0, 1)
        self.image_layout.addItem(self.image_after_vb, 0, 2)
        self.image_layout.addItem(self.image_after_hist, 0, 3)
        self.image_layout.addItem(self.image_difference_vb, 0, 4)
        self.image_layout.addItem(self.image_difference_hist, 0, 5)
        self.nextRow()

        before_details = self.addLabel("")
        after_details = self.addLabel("")
        difference_details = self.addLabel("")

        self.display_formatted_detail = {
            self.image_before: lambda val: before_details.setText(f"Before: {val:.6f}"),
            self.image_after: lambda val: after_details.setText(f"After: {val:.6f}"),
            self.image_difference: lambda val: difference_details.setText(f"Difference: {val:.6f}"),
        }

        for img in self.image_before, self.image_after, self.image_difference:
            img.hoverEvent = lambda ev: self.mouse_over(ev)

        self.init_histogram()

        # Work around for https://github.com/mantidproject/mantidimaging/issues/565
        for scene in [
                self.image_before.scene(),
                self.image_before_hist.scene(),
                self.image_after.scene(),
                self.image_after_hist.scene(),
                self.image_difference.scene(),
                self.image_difference_hist.scene(),
        ]:
            scene.contextMenu = [item for item in scene.contextMenu if "export" not in item.text().lower()]

    def resizeEvent(self, ev: QResizeEvent):
        if ev is not None and isinstance(self.histogram, PlotItem):
            size = ev.size()
            self.histogram.setFixedHeight(min(size.height() * 0.7, self.ALLOWED_HEIGHT) * 0.25)
        super().resizeEvent(ev)

    def image_in_vb(self, name=None):
        im = ImageItem()
        vb = ViewBox(invertY=True, lockAspect=True, name=name)
        vb.addItem(im)
        hist = HistogramLUTItem(im)
        return im, vb, hist

    def clear_items(self):
        self.image_before.clear()
        self.image_after.clear()
        self.image_difference.clear()
        self.image_after_overlay.clear()

    def init_histogram(self):
        self.histogram = self.addPlot(row=histogram_coords["combined"].row,
                                      col=histogram_coords["combined"].col,
                                      labels=histogram_axes_labels,
                                      lockAspect=True,
                                      colspan=3)
        self.addLabel("Pixel values", row=label_coords["combined"].row, col=label_coords["combined"].col)

        self.legend = self.histogram.addLegend()

    def update_histogram_data(self):
        # Plot any histogram that has data, and add a legend if both exist
        before_data = self.image_before.getHistogram()
        after_data = self.image_after.getHistogram()
        if _data_valid_for_histogram(before_data):
            if self.combined_histograms:
                before_plot = self.histogram.plot(*before_data, pen=before_pen, clear=True)
                self.legend.addItem(before_plot, "Before")
            else:
                self.before_histogram.plot(*before_data, pen=before_pen, clear=True)
        if _data_valid_for_histogram(after_data):
            if self.combined_histograms:
                after_plot = self.histogram.plot(*after_data, pen=after_pen)
                self.legend.addItem(after_plot, "After")
            else:
                self.after_histogram.plot(*after_data, pen=after_pen, clear=True)

    def init_separate_histograms(self):
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
        if _data_valid_for_histogram(self.before_histogram_data):
            self.before_histogram.plot(*self.before_histogram_data, pen=before_pen)
        if _data_valid_for_histogram(self.after_histogram_data):
            self.after_histogram.plot(*self.after_histogram_data, pen=after_pen)

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
        for view1, view2 in [[self.image_before_vb, self.image_after_vb],
                             [self.image_after_vb, self.image_difference_vb],
                             [self.image_after_hist.vb, self.image_before_hist.vb]]:
            view1.linkView(ViewBox.XAxis, view2)
            view1.linkView(ViewBox.YAxis, view2)

    def unlink_all_views(self):
        for view in self.image_before_vb, self.image_after_vb, self.image_after_hist.vb:
            view.linkView(ViewBox.XAxis, None)
            view.linkView(ViewBox.YAxis, None)

    def add_difference_overlay(self, diff):
        diff = -diff
        diff[diff > 0.0] = 1.0
        pos = np.array([0, 1])
        color = np.array([[0, 0, 0, 0], [255, 0, 0, 255]], dtype=np.ubyte)
        map = ColorMap(pos, color)
        self.image_after_overlay.setOpacity(1)
        self.image_after_overlay.setImage(diff)
        lut = map.getLookupTable(0, 1, 2)
        self.image_after_overlay.setLookupTable(lut)

    def hide_difference_overlay(self):
        self.image_after_overlay.setOpacity(0)

    def auto_range(self):
        # This will cause the previews to all show by just causing autorange on self.image_before_vb
        self.image_before_vb.autoRange()
