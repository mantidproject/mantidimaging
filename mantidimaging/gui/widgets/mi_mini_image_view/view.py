# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Tuple
from weakref import WeakSet

from pyqtgraph import ImageItem, ViewBox
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint

graveyard = []


class MIMiniImageView(GraphicsLayout):
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

        self.nextRow()
        self.details = self.addLabel("", colspan=2)
        self.im.hoverEvent = lambda ev: self.mouse_over(ev)

        self.siblings: "WeakSet[MIMiniImageView]" = WeakSet()

    def clear(self):
        self.im.clear()

    @staticmethod
    def set_siblings(sibling_views: List["MIMiniImageView"]):
        for view1 in sibling_views:
            for view2 in sibling_views:
                if view2 is not view1:
                    view1.add_sibling(view2)

    def add_sibling(self, sibling: "MIMiniImageView"):
        self.siblings.add(sibling)

    def get_parts(self) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        return self.im, self.vb, self.hist

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())

        self.show_value(pos)
        for img_view in self.siblings:
            img_view.show_value(pos)

    def show_value(self, pos):
        image = self.im.image
        if image is not None and pos.y < image.shape[0] and pos.x < image.shape[1]:
            pixel_value = image[pos.y, pos.x]
            self.details.setText(f"{self.name}: {pixel_value:.6f}")
