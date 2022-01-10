# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from itertools import chain, tee
from typing import List, Tuple
from weakref import WeakSet

from pyqtgraph import ImageItem, ViewBox
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.gui.utility.qt_helpers import BlockQtSignals
from mantidimaging.gui.widgets.bad_data_overlay.bad_data_overlay import BadDataOverlay

graveyard = []


# https://docs.python.org/3/library/itertools.html?highlight=itertools#itertools.pairwise
# COMPAT python < 3.10
def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class MIMiniImageView(GraphicsLayout, BadDataOverlay):
    def __init__(self, name: str = "MIMiniImageView"):
        super().__init__()

        self.name = name.title()
        self.im = ImageItem()
        self.vb = ViewBox(invertY=True, lockAspect=True, name=name)
        self.vb.addItem(self.im)
        self.hist = HistogramLUTItem(self.im)
        graveyard.append(self.vb)

        # Sub-layout prevents resizing issues when details text changes
        image_layout = self.addLayout(colspan=2)
        image_layout.addItem(self.vb)
        image_layout.addItem(self.hist)
        self.hist.setFixedWidth(100)  # HistogramLUTItem used pixel sizes

        self.nextRow()
        self.details = self.addLabel("", colspan=2)
        self.im.hoverEvent = lambda ev: self.mouse_over(ev)

        self.axis_siblings: "WeakSet[MIMiniImageView]" = WeakSet()
        self.histogram_siblings: "WeakSet[MIMiniImageView]" = WeakSet()

    @property
    def image_item(self) -> ImageItem:
        return self.im

    @property
    def viewbox(self) -> ViewBox:
        return self.vb

    def clear(self):
        self.im.clear()

    def setImage(self, *args, **kwargs):
        self.im.setImage(*args, **kwargs)
        self.check_for_bad_data()

    @staticmethod
    def set_siblings(sibling_views: List["MIMiniImageView"], axis=False, hist=False):
        for view1 in sibling_views:
            for view2 in sibling_views:
                if view2 is not view1:
                    if axis:
                        view1.add_axis_sibling(view2)
                    if hist:
                        view1.add_hist_sibling(view2)

    def add_axis_sibling(self, sibling: "MIMiniImageView"):
        self.axis_siblings.add(sibling)

    def add_hist_sibling(self, sibling: "MIMiniImageView"):
        self.histogram_siblings.add(sibling)

    def get_parts(self) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        return self.im, self.vb, self.hist

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())

        self.show_value(pos)
        for img_view in self.axis_siblings:
            img_view.show_value(pos)

    def show_value(self, pos):
        image = self.im.image
        if image is not None and pos.y < image.shape[0] and pos.x < image.shape[1]:
            pixel_value = image[pos.y, pos.x]
            value_string = ("%.6f" % pixel_value)[:8]
            self.details.setText(f"{self.name}: {value_string}")

    def link_sibling_axis(self):
        # Linking multiple viewboxes with locked aspect ratios causes
        # odd resizing behaviour. Use workaround from
        # https://github.com/pyqtgraph/pyqtgraph/issues/1348
        self.vb.setAspectLocked(True)
        for view1, view2 in pairwise(chain([self], self.axis_siblings)):
            view2.vb.linkView(ViewBox.XAxis, view1.vb)
            view2.vb.linkView(ViewBox.YAxis, view1.vb)
            view2.vb.setAspectLocked(False)

    def unlink_sibling_axis(self):
        for img_view in chain([self], self.axis_siblings):
            img_view.vb.linkView(ViewBox.XAxis, None)
            img_view.vb.linkView(ViewBox.YAxis, None)
            img_view.vb.setAspectLocked(True)

    def link_sibling_histogram(self):
        for view1, view2 in pairwise(chain([self], self.histogram_siblings)):
            view1.hist.vb.linkView(ViewBox.YAxis, view2.hist.vb)
        for img_view in chain([self], self.histogram_siblings):
            img_view.hist.sigLevelChangeFinished.connect(img_view.update_sibling_histograms)

    def unlink_sibling_histogram(self):
        for img_view in chain([self], self.histogram_siblings):
            img_view.hist.vb.linkView(ViewBox.YAxis, None)
            try:
                img_view.hist.sigLevelChangeFinished.disconnect()
            except TypeError:
                # This is expected if there are slots currently connected
                pass

    def update_sibling_histograms(self):
        hist_range = self.hist.getLevels()
        for img_view in self.histogram_siblings:
            with BlockQtSignals(img_view.hist):
                img_view.hist.setLevels(*hist_range)
