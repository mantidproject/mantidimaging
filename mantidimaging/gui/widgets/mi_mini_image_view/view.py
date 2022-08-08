# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from itertools import chain, tee
from typing import List, TYPE_CHECKING, Optional, Union
from weakref import WeakSet

from pyqtgraph import ImageItem, ViewBox
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.gui.utility.qt_helpers import BlockQtSignals
from mantidimaging.gui.widgets.auto_colour_menu.auto_color_menu import AutoColorMenu
from mantidimaging.gui.widgets.bad_data_overlay.bad_data_overlay import BadDataOverlay

if TYPE_CHECKING:
    import numpy as np
    from PyQt5.QtWidgets import QWidget

graveyard = []


# https://docs.python.org/3/library/itertools.html?highlight=itertools#itertools.pairwise
# COMPAT python < 3.10
def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class MIMiniImageView(GraphicsLayout, BadDataOverlay, AutoColorMenu):
    def __init__(self, name: str = "MIMiniImageView", parent: 'Optional[QWidget]' = None, recon_mode: bool = False):
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

        self.add_auto_color_menu_action(parent, recon_mode=recon_mode, set_enabled=False)

    @property
    def histogram(self) -> HistogramLUTItem:
        return self.hist

    @property
    def histogram_region(self):
        return self.hist.region.getRegion()

    @histogram_region.setter
    def histogram_region(self, new_region: tuple[Union[int, list[int]], Union[int, list[int]]]):
        self.hist.region.setRegion(new_region)

    @property
    def image_data(self) -> 'np.ndarray':
        return self.im.image

    @property
    def other_histograms(self) -> List[HistogramLUTItem]:
        return [axis.hist for axis in self.axis_siblings]

    @property
    def image_item(self) -> ImageItem:
        return self.im

    @property
    def viewbox(self) -> ViewBox:
        return self.vb

    def clear(self):
        self.im.clear()
        self.set_auto_color_enabled(False)
        self.clear_overlays()
        self.details.setText("")

    def setImage(self, *args, **kwargs):
        self.im.setImage(*args, **kwargs)
        self.check_for_bad_data()
        self.set_auto_color_enabled(self.im.image is not None)

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

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())

        self.show_details(pos)
        for img_view in self.axis_siblings:
            img_view.show_details(pos)

    def show_details(self, pos):
        image = self.im.image
        if image is not None and pos.y < image.shape[0] and pos.x < image.shape[1]:
            pixel_value = image[pos.y, pos.x]
            value_string = ("%.6f" % pixel_value)[:8]
            self.details.setText(f"x={pos.x}, y={pos.y}, value={value_string}")

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
