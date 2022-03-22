# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import namedtuple
from logging import getLogger
from typing import Optional

import numpy as np
from PyQt5.QtCore import QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QResizeEvent
from pyqtgraph import ColorMap, GraphicsLayoutWidget, ImageItem, LegendItem, PlotItem, InfiniteLine
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout

from mantidimaging.core.utility.histogram import set_histogram_log_scale
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

LOG = getLogger(__name__)

histogram_axes_labels = {'left': 'Count', 'bottom': 'Gray value'}
before_pen = (200, 0, 0)
after_pen = (0, 200, 0)
diff_pen = (0, 0, 200)

OVERLAY_THRESHOLD = 1e-3
OVERLAY_COLOUR_DIFFERENCE = [0, 255, 0, 255]

Coord = namedtuple('Coord', ['row', 'col'])
histogram_coords = Coord(4, 0)
label_coords = Coord(3, 1)


def _data_valid_for_histogram(data):
    return data is not None and any(d is not None for d in data)


class ZSlider(PlotItem):
    z_line: InfiniteLine
    valueChanged = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedHeight(40)
        self.hideAxis("left")
        self.setXRange(0, 1)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()

        self.z_line = InfiniteLine(0, movable=True)
        self.z_line.setPen((255, 255, 0, 200))
        self.addItem(self.z_line)

        self.z_line.sigPositionChanged.connect(self.value_changed)

    def set_range(self, min, max):
        self.z_line.setValue(min)
        self.setXRange(min, max)
        self.z_line.setBounds([min, max])

    def value_changed(self):
        self.valueChanged.emit(int(self.z_line.value()))


class FilterPreviews(GraphicsLayoutWidget):
    histogram: Optional[PlotItem]
    z_slider: ZSlider

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        widget_location = self.mapToGlobal(QPoint(self.width() // 2, 0))
        # allow the widget to take up to 80% of the desktop's height
        if QGuiApplication.screenAt(widget_location) is not None:
            screen_height = QGuiApplication.screenAt(widget_location).availableGeometry().height()
        else:
            screen_height = max(QGuiApplication.primaryScreen().availableGeometry().height(), 600)
            LOG.info("Unable to detect current screen. Setting screen height to %s" % screen_height)
        self.ALLOWED_HEIGHT: QRect = screen_height * 0.8

        self.histogram = None

        self.addLabel("Image before")
        self.addLabel("Image after")
        self.addLabel("Image difference")
        self.nextRow()

        self.imageview_before = MIMiniImageView(name="before", parent=self)
        self.imageview_after = MIMiniImageView(name="after", parent=self)
        self.imageview_difference = MIMiniImageView(name="difference", parent=self)
        self.all_imageviews = [self.imageview_before, self.imageview_after, self.imageview_difference]
        MIMiniImageView.set_siblings(self.all_imageviews, axis=True)
        MIMiniImageView.set_siblings([self.imageview_before, self.imageview_after], hist=True)

        self.image_diff_overlay = ImageItem()
        self.image_diff_overlay.setZValue(10)
        self.imageview_after.viewbox.addItem(self.image_diff_overlay)

        # Ensure images resize equally
        self.image_layout: GraphicsLayout = self.addLayout(colspan=3)

        self.image_layout.addItem(self.imageview_before)
        self.image_layout.addItem(self.imageview_after)
        self.image_layout.addItem(self.imageview_difference)
        self.nextRow()

        self.z_slider = ZSlider()
        self.addItem(self.z_slider, colspan=3)

        self.init_histogram()

        # Work around for https://github.com/mantidproject/mantidimaging/issues/565
        self.scene().contextMenu = [item for item in self.scene().contextMenu if "export" not in item.text().lower()]

        self.imageview_before.link_sibling_axis()

        self.imageview_before.enable_nan_check()
        self.imageview_after.enable_nan_check()

    def resizeEvent(self, ev: QResizeEvent):
        if ev is not None and isinstance(self.histogram, PlotItem):
            size = ev.size()
            self.histogram.setFixedHeight(min(size.height() * 0.7, self.ALLOWED_HEIGHT) * 0.25)
        super().resizeEvent(ev)

    def clear_items(self, clear_before: bool = True):
        if clear_before:
            self.imageview_before.clear()
        self.imageview_after.clear()
        self.imageview_difference.clear()
        self.image_diff_overlay.clear()

    def init_histogram(self):
        self.histogram = self.addPlot(row=histogram_coords.row,
                                      col=histogram_coords.col,
                                      labels=histogram_axes_labels,
                                      lockAspect=True,
                                      colspan=3)
        self.addLabel("Pixel values", row=label_coords.row, col=label_coords.col)

        self.legend = self.histogram.addLegend()
        self.legend.setOffset((0, 1))

    def update_histogram_data(self):
        # Plot any histogram that has data, and add a legend if both exist
        before_data = self.imageview_before.image_item.getHistogram()
        after_data = self.imageview_after.image_item.getHistogram()
        if _data_valid_for_histogram(before_data):
            before_plot = self.histogram.plot(*before_data, pen=before_pen, clear=True)
            self.legend.addItem(before_plot, "Before")

        if _data_valid_for_histogram(after_data):
            after_plot = self.histogram.plot(*after_data, pen=after_pen)
            self.legend.addItem(after_plot, "After")

    @property
    def histogram_legend(self) -> Optional[LegendItem]:
        if self.histogram and self.histogram.legend:
            return self.histogram.legend
        return None

    def link_all_views(self):
        self.imageview_before.link_sibling_axis()

    def unlink_all_views(self):
        self.imageview_before.unlink_sibling_axis()

    def add_difference_overlay(self, diff, nan_change):
        diff = np.absolute(diff)
        diff[diff > OVERLAY_THRESHOLD] = 1.0
        diff[nan_change] = 1.0
        pos = np.array([0, 1])
        color = np.array([[0, 0, 0, 0], OVERLAY_COLOUR_DIFFERENCE], dtype=np.ubyte)
        map = ColorMap(pos, color)
        self.image_diff_overlay.setVisible(True)
        self.image_diff_overlay.setImage(diff)
        lut = map.getLookupTable(0, 1, 2)
        self.image_diff_overlay.setLookupTable(lut)

    def add_negative_overlay(self):
        self.imageview_after.enable_nonpositive_check()

    def hide_difference_overlay(self):
        self.image_diff_overlay.setVisible(False)

    def hide_negative_overlay(self):
        self.imageview_after.enable_nonpositive_check(False)

    def auto_range(self):
        # This will cause the previews to all show by just causing autorange on self.imageview_before.viewbox
        self.imageview_before.viewbox.autoRange()

    def record_histogram_regions(self):
        self.before_region = self.imageview_before.histogram.region.getRegion()
        self.diff_region = self.imageview_difference.histogram.region.getRegion()
        self.after_region = self.imageview_after.histogram.region.getRegion()

    def restore_histogram_regions(self):
        self.imageview_before.histogram.region.setRegion(self.before_region)
        self.imageview_difference.histogram.region.setRegion(self.diff_region)
        self.imageview_after.histogram.region.setRegion(self.after_region)

    def link_before_after_histogram_scales(self, create_link: bool):
        """
        Connects or disconnects the scales of the before/after histograms.
        :param create_link: Whether the link should be created or removed.
        """
        if create_link:
            self.imageview_after.link_sibling_histogram()
        else:
            self.imageview_after.unlink_sibling_histogram()

    def set_histogram_log_scale(self):
        """
        Sets the y-values of the before and after histogram plots to a log scale.
        """
        set_histogram_log_scale(self.imageview_before.histogram)
        set_histogram_log_scale(self.imageview_after.histogram)
